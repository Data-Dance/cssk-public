from odoo import _, api, fields, models
from odoo.exceptions import UserError

from ..engine import depreciation as eng


class AccountAssetTaxBackfill(models.TransientModel):
    """Set up tax depreciation on an asset that is already part-way through its
    life (migration of an existing fleet).

    Tax depreciation is statutory, so the historical years are exactly what the
    engine computes — the wizard lays out the full board, **freezes** every year
    up to the last filed fiscal year, and leaves the open tail to be claimed
    going forward. An optional *expected residual* is checked up-front against
    the computed residual so that any discrepancy (a past suspension or technical
    improvement not yet modelled, or a wrong in-service date) is caught before
    anything is written.
    """

    _name = "account.asset.tax.backfill"
    _description = "Backfill Tax Depreciation"

    asset_display = fields.Char(string="Asset", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)
    tax_class_id = fields.Many2one("account.asset.tax.class", string="Tax Group", required=True)
    tax_method = fields.Selection(
        [
            ("linear", "Straight-line"),
            ("accelerated", "Accelerated"),
            ("extraordinary", "Extraordinary (CZ §30a)"),
        ],
        required=True, default="linear",
    )
    tax_entry_value = fields.Monetary(required=True)
    tax_in_service_date = fields.Date(string="Tax In-Service Date", required=True)
    filed_through_year = fields.Integer(
        string="Filed Through Fiscal Year", required=True,
        help="Last fiscal year whose tax depreciation has already been filed. "
        "Every board year up to and including it is frozen.",
    )
    expected_residual = fields.Monetary(
        string="Expected Tax Residual",
        help="Optional cross-check: the tax residual value at the end of the "
        "filed period per your prior records. The wizard refuses to backfill if "
        "it disagrees with the statutory computation.",
    )

    # ------------------------------------------------------------------
    def _asset(self):
        if self.env.context.get("active_model") != "account.asset":
            raise UserError(_("Open this from an asset."))
        active_id = self.env.context.get("active_id")
        if not active_id:
            raise UserError(_("No asset in context."))
        return self.env["account.asset"].browse(active_id)

    @api.model
    def default_get(self, fields_list):
        res = super().default_get(fields_list)
        asset = self._asset()
        res["asset_display"] = asset.display_name
        res["currency_id"] = asset.company_id.currency_id.id
        res["tax_class_id"] = asset.tax_class_id.id or False
        if asset.tax_method:
            res["tax_method"] = asset.tax_method
        try:
            res["tax_entry_value"] = asset.tax_entry_value or asset._tax_get_entry_value()
        except NotImplementedError:
            res["tax_entry_value"] = asset.tax_entry_value or 0.0
        in_service = asset.tax_in_service_date_override
        if not in_service:
            try:
                in_service = asset._tax_get_in_service_date()
            except NotImplementedError:
                in_service = False
        res["tax_in_service_date"] = in_service
        today = fields.Date.context_today(self)
        res.setdefault("filed_through_year", today.year - 1)
        return res

    def _dry_run_residual(self, asset):
        """Compute the statutory residual at the end of ``filed_through_year``
        from the wizard parameters, without persisting anything.

        The spec is built by the asset's own ``_tax_engine_spec()`` (on an
        in-memory copy carrying the wizard's overrides), so parameters the
        wizard does not override — the §31 increased first-year election, the
        vehicle base cap — feed the dry run exactly as they will feed the final
        board. Hand-rolling the spec here silently dropped them, making the
        residual cross-check disagree with the board it was validating.
        """
        virtual = asset.new(origin=asset)
        virtual.update({
            "tax_class_id": self.tax_class_id,
            "tax_method": self.tax_method,
            "tax_entry_value": self.tax_entry_value,
            "tax_in_service_date_override": self.tax_in_service_date,
        })
        schedule = eng.compute_schedule(virtual._tax_engine_spec())
        past = [l for l in schedule if l.fiscal_year <= self.filed_through_year]
        return past[-1].residual if past else self.tax_entry_value

    def action_backfill(self):
        self.ensure_one()
        asset = self._asset()
        ccy = asset.company_id.currency_id

        # Validate before writing: the computed residual must match the records.
        if self.expected_residual:
            computed = self._dry_run_residual(asset)
            if ccy.compare_amounts(computed, self.expected_residual) != 0:
                raise UserError(_(
                    "The statutory tax residual at the end of %(year)s is "
                    "%(computed)s, but you entered %(expected)s.\n\n"
                    "Tax depreciation is statutory, so a mismatch usually means a "
                    "past technical improvement or suspension is not yet recorded, "
                    "or the tax in-service date is wrong. Fix those first (add the "
                    "events, correct the date), then backfill.",
                    year=self.filed_through_year,
                    computed=ccy.round(computed),
                    expected=ccy.round(self.expected_residual),
                ))

        # Mass unfreeze FIRST (the wizard is the sanctioned unfreeze path — the
        # ``cssk_unfreeze`` flag bypasses the posted-line write guard), so the
        # parameter write below happens with no filed lines left to contradict.
        asset.tax_line_ids.with_context(cssk_unfreeze=True).write({"posted": False})
        asset.write({
            "tax_depreciation_enabled": True,
            "tax_class_id": self.tax_class_id.id,
            "tax_method": self.tax_method,
            "tax_entry_value": self.tax_entry_value,
            "tax_in_service_date_override": self.tax_in_service_date,
        })
        # full clean rebuild, then freeze the historical years
        asset.compute_tax_depreciation_board()
        asset._tax_freeze_through(self.filed_through_year)
        if asset.tax_line_ids.filtered("posted"):
            asset.tax_method_locked = True

        return {
            "type": "ir.actions.act_window",
            "res_model": "account.asset",
            "res_id": asset.id,
            "view_mode": "form",
        }
