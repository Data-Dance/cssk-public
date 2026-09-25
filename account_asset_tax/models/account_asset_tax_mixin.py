from odoo import _, api, fields, models
from odoo.exceptions import UserError, ValidationError

from ..engine import depreciation as eng


class AccountAssetTaxMixin(models.AbstractModel):
    """Tax-depreciation behaviour mixed into ``account.asset`` by the bridges.

    A bridge module declares::

        class AccountAsset(models.Model):
            _name = "account.asset"
            _inherit = ["account.asset", "account.asset.tax.mixin"]

    and implements the two abstract readers below so the mixin can stay ignorant
    of whether it runs on the Enterprise (``account_asset``) or OCA
    (``account_asset_management``) asset model.
    """

    _name = "account.asset.tax.mixin"
    _description = "Tax Depreciation Mixin"

    tax_depreciation_enabled = fields.Boolean(
        string="Track Tax Depreciation",
        help="Maintain a separate, non-posted tax-depreciation schedule for this "
        "asset (daňové odpisy). The accounting depreciation board is unaffected.",
    )
    tax_class_id = fields.Many2one(
        "account.asset.tax.class",
        string="Tax Depreciation Group",
        help="Statutory depreciation group (odpisová skupina).",
    )
    tax_method = fields.Selection(
        [
            ("linear", "Straight-line (rovnoměrné / rovnomerné)"),
            ("accelerated", "Accelerated (zrychlené / zrýchlené)"),
            ("extraordinary", "Extraordinary (CZ §30a)"),
        ],
        string="Tax Method",
        default="linear",
    )
    tax_increased_first_year = fields.Selection(
        [("0", "None"), ("10", "+10 %"), ("15", "+15 %"), ("20", "+20 %")],
        string="Increased First-Year Rate",
        default="0",
        help="CZ §31(1)(b)/(c)/(d): a first depreciator of a group 1–3 asset may "
        "elect a higher first-year straight-line rate (+10/15/20 %). CZ + "
        "straight-line + groups 1–3 only.",
    )
    tax_method_locked = fields.Boolean(
        string="Tax Method Locked",
        help="Set once the first tax depreciation is filed. The statutory method "
        "may not change for the asset's whole life (CZ §30(2) / SK §26(3)).",
    )
    # This abstract mixin is set up standalone by the ORM, so its own Monetary
    # fields need a currency field that exists *on the mixin* — it cannot borrow
    # ``company_id.currency_id`` (company_id is only on the concrete asset). The
    # bridge's ``tax_value_*`` Monetary fields reuse this same currency field.
    tax_currency_id = fields.Many2one(
        "res.currency", compute="_compute_tax_currency_id",
        help="Company currency, for the tax-depreciation monetary fields.",
    )
    tax_entry_value = fields.Monetary(
        string="Tax Entry Value", currency_field="tax_currency_id",
        help="Depreciable base for tax purposes (vstupní / vstupná cena). Defaults "
        "to the accounting acquisition value but can differ (e.g. capped M1 vehicle, "
        "non-deductible components).",
    )
    tax_vehicle_capped = fields.Boolean(
        string="Apply Vehicle Depreciation Cap",
        help="Passenger vehicle subject to the statutory depreciation cap "
        "(CZ §30e 2M CZK / SK §17(34) 48k EUR). The tax board is then computed on "
        "the company's capped base instead of the full entry value.",
    )
    tax_in_service_date_override = fields.Date(
        string="Tax In-Service Date",
        help="Date the asset entered use for tax purposes (zaradenie do "
        "užívania). Defaults to the accounting depreciation start; override it "
        "when migrating an asset whose tax depreciation started on another date.",
    )
    # NOTE: the ``tax_line_ids`` One2many — and the ``tax_value_residual`` /
    # ``tax_value_depreciated`` computes that depend on it — are declared by the
    # bridge module (which also adds the ``asset_id`` inverse on
    # ``account.asset.tax.line``), so this core mixin never references the asset
    # model relationally and stays valid when set up on its own.
    # convenience for the form: which methods the chosen group permits
    tax_allowed_methods = fields.Char(compute="_compute_tax_allowed_methods")
    # used to scope the tax-group selection on the form to the company country
    tax_country_code = fields.Char(compute="_compute_tax_country_code")

    # ------------------------------------------------------------------
    # Bridge contract — overridden in account_asset_tax_ee / _cssk_oca
    # ------------------------------------------------------------------
    def _tax_get_entry_value(self):
        """Return the gross accounting acquisition value of the asset."""
        raise NotImplementedError

    def _tax_get_in_service_date(self):
        """Return the date the asset was put into use (date)."""
        raise NotImplementedError

    def _tax_get_country_code(self):
        """Return 'CZ' / 'SK' from the company, falling back to the tax class."""
        self.ensure_one()
        country = self.company_id.account_fiscal_country_id or self.company_id.country_id
        code = (country.code or "").upper()
        if code in ("CZ", "SK"):
            return code
        return self.tax_class_id.country_code or False

    def _cssk_book_depreciation_by_year(self):
        """Bridge contract: the ACCOUNTING (book) depreciation of this asset,
        aggregated per fiscal year::

            {year: {"amount": <book depreciation>, "residual": <book net value>}}

        Overridden per edition (EE = ``depreciation_move_ids``, OCA =
        ``depreciation_line_ids``); returns ``{}`` when the asset has no
        accounting depreciation yet. Tax depreciation is always annual, so this
        lets us line the two streams up by year even when book depreciation is
        posted monthly.
        """
        self.ensure_one()
        return {}

    def _cssk_book_tax_by_year(self):
        """Merge accounting vs tax depreciation by fiscal year for this asset.

        Returns an ordered list of dicts — ``year, book, tax, difference``
        (book − tax), ``book_residual, tax_residual, cumulative_difference``
        (Σbook − Σtax up to and including the year). The per-year ``difference``
        is the DPPO add-back/deduction (SK pripočítateľná/odpočítateľná položka,
        CZ § 23/3 ř. 50/150); ``cumulative_difference`` (book ZC − tax ZC) is the
        temporary difference feeding deferred tax (odložená daň).
        """
        self.ensure_one()
        book = self._cssk_book_depreciation_by_year()
        tax_lines = {line.fiscal_year: line for line in self.tax_line_ids}
        rows = []
        cumulative = 0.0
        for year in sorted(set(book) | set(tax_lines)):
            b = book.get(year) or {}
            tl = tax_lines.get(year)
            book_amt = b.get("amount", 0.0)
            tax_amt = tl.amount if tl else 0.0
            cumulative += book_amt - tax_amt
            rows.append({
                "year": year,
                "book": book_amt,
                "tax": tax_amt,
                "difference": book_amt - tax_amt,
                "book_residual": b.get("residual", 0.0),
                "tax_residual": tl.residual if tl else 0.0,
                "cumulative_difference": cumulative,
            })
        return rows

    # ------------------------------------------------------------------
    # Computes
    # ------------------------------------------------------------------
    # No @api.depends: ``company_id`` lives on the concrete asset, not on this
    # abstract mixin, so a dependency path would fail at standalone setup. The
    # company currency is effectively constant per asset, so lazy compute is fine.
    def _compute_tax_currency_id(self):
        for asset in self:
            asset.tax_currency_id = asset.company_id.currency_id

    @api.depends("tax_class_id")
    def _compute_tax_allowed_methods(self):
        for asset in self:
            asset.tax_allowed_methods = ",".join(asset.tax_class_id.allowed_methods()) if asset.tax_class_id else ""

    def _compute_tax_country_code(self):
        for asset in self:
            asset.tax_country_code = asset._tax_get_country_code() or ""

    # ------------------------------------------------------------------
    # Onchange helpers
    # ------------------------------------------------------------------
    @api.onchange("tax_class_id")
    def _onchange_tax_class_id(self):
        for asset in self:
            allowed = asset.tax_class_id.allowed_methods() if asset.tax_class_id else []
            if allowed and asset.tax_method not in allowed:
                asset.tax_method = allowed[0]

    @api.onchange("tax_depreciation_enabled")
    def _onchange_tax_enabled(self):
        for asset in self:
            if asset.tax_depreciation_enabled and not asset.tax_entry_value:
                try:
                    asset.tax_entry_value = asset._tax_get_entry_value()
                except NotImplementedError:
                    pass

    # ------------------------------------------------------------------
    # Statutory immutability of the chosen method/group (CZ §30(2) / SK §26(3))
    # ------------------------------------------------------------------
    # Inputs that fully determine the engine schedule: once a year is filed
    # (posted board lines exist), silently changing any of them would invalidate
    # the frozen history. The backfill wizard (which mass-unfreezes first, under
    # the ``cssk_unfreeze`` context flag) is the sanctioned correction path.
    _TAX_FROZEN_INPUT_FIELDS = (
        "tax_entry_value",
        "tax_in_service_date_override",
        "tax_increased_first_year",
        "tax_vehicle_capped",
    )

    def write(self, vals):
        if "tax_method" in vals or "tax_class_id" in vals:
            for asset in self:
                if not asset.tax_method_locked:
                    continue
                if (vals.get("tax_method") and vals["tax_method"] != asset.tax_method):
                    raise UserError(_(
                        "The tax depreciation method of %s is locked and may not "
                        "change for the asset's whole depreciation life "
                        "(CZ §30(2) / SK §26(3)). Untick “Tax Method Locked” only "
                        "to correct a data-entry error.", asset.display_name))
                if (vals.get("tax_class_id")
                        and vals["tax_class_id"] != asset.tax_class_id.id):
                    raise UserError(_(
                        "The tax depreciation group of %s is locked because filed "
                        "years exist; it may not change.", asset.display_name))
        touched = [f for f in self._TAX_FROZEN_INPUT_FIELDS if f in vals]
        if touched and not self.env.context.get("cssk_unfreeze") \
                and "tax_line_ids" in self._fields:
            for asset in self:
                if not asset.tax_line_ids.filtered("posted"):
                    continue
                for fname in touched:
                    field = asset._fields[fname]
                    if (field.convert_to_cache(vals[fname], asset)
                            != field.convert_to_cache(asset[fname], asset)):
                        raise UserError(_(
                            "Cannot change %(field)s on %(asset)s: filed "
                            "(frozen) tax-depreciation years exist and the "
                            "change would silently contradict them. Use the "
                            "Backfill (migration) wizard to correct the tax "
                            "parameters — it unfreezes and rebuilds the "
                            "history explicitly.",
                            field=self._fields[fname].string or fname,
                            asset=asset.display_name))
        return super().write(vals)

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------
    @api.constrains("tax_increased_first_year", "tax_method", "tax_class_id")
    def _check_increased_first_year(self):
        for asset in self:
            if not asset.tax_depreciation_enabled or asset.tax_increased_first_year in (False, "0"):
                continue
            ok = (asset._tax_get_country_code() == eng.CZ
                  and asset.tax_method == eng.METHOD_LINEAR
                  and asset.tax_class_id.group_number in (1, 2, 3))
            if not ok:
                raise ValidationError(_(
                    "The increased first-year rate (§31) applies only to Czech "
                    "straight-line depreciation of groups 1–3."))

    @api.constrains("tax_method", "tax_class_id")
    def _check_tax_method_allowed(self):
        for asset in self:
            if not asset.tax_depreciation_enabled or not asset.tax_class_id:
                continue
            allowed = asset.tax_class_id.allowed_methods()
            if asset.tax_method not in allowed:
                raise ValidationError(_(
                    "Group %(group)s does not allow the %(method)s method. "
                    "Allowed: %(allowed)s.",
                    group=asset.tax_class_id.code,
                    method=asset.tax_method,
                    allowed=", ".join(allowed) or "—",
                ))

    # ------------------------------------------------------------------
    # Engine orchestration
    # ------------------------------------------------------------------
    def _tax_engine_spec(self):
        """Build the :class:`engine.depreciation.TaxAssetSpec` for this asset."""
        self.ensure_one()
        country = self._tax_get_country_code()
        if not country:
            raise UserError(_("Cannot determine the tax country for asset %s.", self.display_name))
        if not self.tax_class_id:
            raise UserError(_("Set a tax depreciation group on asset %s first.", self.display_name))
        return eng.TaxAssetSpec(
            country=country,
            method=self.tax_method,
            entry_value=self.tax_entry_value or self._tax_get_entry_value(),
            in_service_date=self.tax_in_service_date_override or self._tax_get_in_service_date(),
            tax_class=self.tax_class_id.to_engine(),
            monthly=(self.tax_method == eng.METHOD_EXTRAORDINARY),
            increased_first_year=int(self.tax_increased_first_year or "0"),
            entry_cap=(self.company_id.tax_vehicle_cap_amount or 0.0) if self.tax_vehicle_capped else 0.0,
        )

    def _tax_year_index_for_date(self, schedule, dt):
        """Return the schedule year_index whose fiscal year contains ``dt``."""
        for line in schedule:
            if line.fiscal_year == dt.year:
                return line.year_index
        if not schedule:
            return 1
        # date before the schedule: clamp to the FIRST year (clamping early
        # dates to the last index made a pre-in-service event hit the final
        # schedule year instead of the earliest one)
        if dt.year < schedule[0].fiscal_year:
            return schedule[0].year_index
        # date beyond the schedule: clamp to the last year
        return schedule[-1].year_index

    def _tax_fold_events(self, schedule):
        """Replay the persisted lifecycle events onto a clean ``schedule``.

        Returns ``(schedule, tax_residual_on_disposal_or_None)``.
        """
        self.ensure_one()
        spec = self._tax_engine_spec()
        disposal_residual = None
        for event in self.tax_event_ids.sorted(lambda e: (e.date, e.id)):
            if not schedule:
                break
            if event.event_type == "improvement":
                yi = self._tax_year_index_for_date(schedule, event.date)
                schedule = eng.apply_technical_improvement(schedule, spec, yi, event.amount)
            elif event.event_type == "suspension":
                yi = self._tax_year_index_for_date(schedule, event.date)
                years = [yi + n for n in range(max(event.duration_years, 1))]
                schedule = eng.apply_suspension(schedule, years)
            elif event.event_type == "disposal":
                schedule, disposal_residual = eng.apply_disposal(schedule, spec, event.date)
        return schedule, disposal_residual

    def compute_tax_depreciation_board(self):
        """(Re)build the tax-depreciation board, preserving filed lines.

        The clean statutory schedule is laid out first, then every persisted
        lifecycle event is folded in (in date order), so the result is fully
        reproducible from the asset parameters + its events.
        """
        TaxLine = self.env["account.asset.tax.line"]
        for asset in self:
            if not asset.tax_depreciation_enabled:
                asset.tax_line_ids.unlink()
                continue
            # Keep filed lines untouched; only redo the open tail.
            filed = asset.tax_line_ids.filtered("posted")
            schedule = eng.compute_schedule(asset._tax_engine_spec())
            schedule, _residual = asset._tax_fold_events(schedule)
            ccy = asset.company_id.currency_id
            # Freeze integrity: the engine must still reproduce every FILED
            # year. A divergence means an asset parameter or event contradicts
            # a filed figure — refuse (before touching any line) instead of
            # leaving a frozen line the engine disagrees with. The backfill
            # wizard is the sanctioned unfreeze-and-rebuild path.
            engine_by_index = {l.year_index: l for l in schedule}
            for fl in filed.sorted("year_index"):
                el = engine_by_index.get(fl.year_index)
                if el is None or ccy.compare_amounts(fl.amount, el.amount) != 0:
                    raise UserError(_(
                        "Recomputing the tax board of %(asset)s would change "
                        "the already-filed year %(year)s (filed %(filed)s vs "
                        "recomputed %(computed)s). Filed years are frozen; use "
                        "the Backfill (migration) wizard to unfreeze and "
                        "rebuild the history explicitly.",
                        asset=asset.display_name,
                        year=fl.fiscal_year,
                        filed=fl.amount,
                        computed=ccy.round(el.amount) if el is not None else _("(no line)"),
                    ))
            (asset.tax_line_ids - filed).unlink()
            filed_years = set(filed.mapped("year_index"))
            vals = []
            for line in schedule:
                if line.year_index in filed_years:
                    continue
                vals.append({
                    "asset_id": asset.id,
                    "company_id": asset.company_id.id,
                    "year_index": line.year_index,
                    "fiscal_year": line.fiscal_year,
                    "date_from": line.date_from,
                    "date_to": line.date_to,
                    "amount": ccy.round(line.amount),
                    "amount_cumulative": ccy.round(line.cumulative),
                    "residual": ccy.round(line.residual),
                    "note": line.note,
                })
            if vals:
                TaxLine.create(vals)
        return True

    def action_compute_tax_board(self):
        self.compute_tax_depreciation_board()
        return True

    # ------------------------------------------------------------------
    # Lifecycle event helpers (called by the wizards)
    # ------------------------------------------------------------------
    def _add_tax_event(self, event_type, date, amount=0.0, duration_years=1, note=False):
        """Create a lifecycle event and recompute the board."""
        self.ensure_one()
        if event_type == "improvement" and self.tax_method == eng.METHOD_EXTRAORDINARY:
            raise UserError(_(
                "A technical improvement of a §30a (extraordinary) asset is "
                "depreciated as a separate asset under §30a(3), not folded into "
                "this one. Create a new asset for the improvement."))
        if event_type == "suspension" and self.tax_method == eng.METHOD_EXTRAORDINARY:
            raise UserError(_(
                "Extraordinary (§30a) depreciation may not be interrupted — "
                "§30a(4) requires it to run in uninterrupted whole months. A "
                "suspension event cannot be recorded on this asset."))
        # Events dated inside (or before) an already-filed year would rewrite
        # frozen history on replay. The backfill wizard is the sanctioned path
        # for corrections reaching into filed years.
        ev_date = fields.Date.to_date(date)
        filed = self.tax_line_ids.filtered("posted")
        if filed and ev_date and ev_date.year <= max(filed.mapped("fiscal_year")):
            raise UserError(_(
                "The %(type)s event dated %(date)s falls inside or before the "
                "last filed tax year (%(year)s) of %(asset)s. Filed years are "
                "frozen; use the Backfill (migration) wizard to unfreeze and "
                "rebuild the history, then record the event.",
                type=event_type, date=ev_date,
                year=max(filed.mapped("fiscal_year")),
                asset=self.display_name))
        self.env["account.asset.tax.event"].create({
            "asset_id": self.id,
            "company_id": self.company_id.id,
            "event_type": event_type,
            "date": date,
            "amount": amount,
            "duration_years": duration_years,
            "note": note or False,
        })
        # NOTE: do NOT raise ``tax_entry_value`` here. The event is the single
        # source of truth — the board recompute replays it (the engine folds the
        # improvement into the schedule), so adding it to the entry value too
        # would double-count the increase. ``tax_entry_value`` stays the original
        # input price; the increased base is reflected in the board and residual.
        self.compute_tax_depreciation_board()
        return True

    def _tax_register_disposal(self, disposal_date):
        """Auto-create the tax disposal event when the asset is disposed in the
        edition's own flow (EE ``set_to_close`` / OCA removal wizard).

        Idempotent: does nothing if tax tracking is off or a disposal event
        already exists, so it is safe to call from a write hook.
        """
        for asset in self:
            if not asset.tax_depreciation_enabled or not disposal_date:
                continue
            if asset.tax_event_ids.filtered(lambda e: e.event_type == "disposal"):
                continue
            asset._add_tax_event("disposal", disposal_date,
                                 note="auto: asset disposed")

    def tax_residual_on_disposal(self):
        """Tax residual value at disposal (for the gain/loss computation) =
        the residual carried by the last (disposal) board line."""
        self.ensure_one()
        board = self.tax_line_ids.sorted("year_index")
        return board[-1].residual if board else (self.tax_entry_value or 0.0)

    # ------------------------------------------------------------------
    # Backfill / migration helpers
    # ------------------------------------------------------------------
    def _tax_freeze_through(self, fiscal_year):
        """Freeze (mark filed) every board line up to and including ``fiscal_year``."""
        self.ensure_one()
        self.tax_line_ids.filtered(
            lambda l: l.fiscal_year <= fiscal_year).write({"posted": True})

    def tax_residual_at_year_end(self, fiscal_year):
        """Tax residual value at the end of ``fiscal_year`` from the board."""
        self.ensure_one()
        past = self.tax_line_ids.filtered(
            lambda l: l.fiscal_year <= fiscal_year).sorted("year_index")
        return past[-1].residual if past else (self.tax_entry_value or 0.0)

    # ------------------------------------------------------------------
    # Accounting-vs-tax reconciliation (DPPO)
    # ------------------------------------------------------------------
    def _tax_accounting_depreciation_for_period(self, date_from, date_to):
        """Posted *accounting* depreciation in the period (bridge-specific).

        Overridden in the EE / OCA bridges; the core default returns 0 so a
        core-only install never crashes.
        """
        return 0.0

    def _tax_accounting_residual(self, on_date):
        """Accounting net book value as of ``on_date`` (bridge-specific).

        Used for the deferred-tax temporary difference. Core default returns 0.
        """
        return 0.0

    def _tax_depreciation_for_period(self, date_from, date_to):
        """Sum of the *tax* board amounts whose line falls inside the period."""
        self.ensure_one()
        total = 0.0
        for line in self.tax_line_ids:
            if line.date_from and date_from <= line.date_from <= date_to:
                total += line.amount
        return total
