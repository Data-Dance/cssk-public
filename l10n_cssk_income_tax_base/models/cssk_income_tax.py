# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, _, api, fields, models
from odoo.tools.translate import LazyTranslate
from odoo.exceptions import UserError
from odoo.tools.safe_eval import safe_eval

_lt = LazyTranslate(__name__)


class CSSKIncomeTaxReturn(models.Model):
    """Corporate income-tax return (DPPO).

    Starts from the accounting result (an ``account`` line over the P&L),
    applies the tax adjustments (``manual`` lines entered by the accountant),
    and computes the tax spine (``aggregate`` lines). CE-clean: the accounting
    result is summed from ``account.move.line`` directly.
    """

    _name = "cssk.income.tax.return"
    _description = "Income Tax Return"
    # Two mixins, two concerns, both wanted: the statutory one retains the
    # filed copy, the submittable one tracks whether it arrived and holds what
    # came back. Neither substitutes for the other — a daňová kontrola asks for
    # the doručenka, which only the second can produce.
    _inherit = ["mail.thread", "mail.activity.mixin",
                "cssk.statutory.submission.mixin",
                "cssk.submittable.mixin"]
    _order = "date_from desc, id desc"

    name = fields.Char(compute="_compute_name")
    company_id = fields.Many2one(
        "res.company", required=True, default=lambda s: s.env.company
    )
    currency_id = fields.Many2one(related="company_id.currency_id")
    country_id = fields.Many2one(
        related="company_id.account_fiscal_country_id", store=True
    )

    version_id = fields.Many2one(
        "cssk.income.tax.version",
        required=True,
        domain="[('country_id', '=', country_id),"
        " ('valid_from', '<=', date_to),"
        " '|', ('valid_to', '=', False), ('valid_to', '>=', date_from)]",
        # The dropdown must offer an ARCHIVED vintage too. The domain
        # above already scopes by period, so a 2026 filing never sees
        # the 2014 vzor anyway — archiving is a way of tidying the
        # configuration list, and it must not quietly make an old
        # period unenterable or a historical filing un-repointable.
        context={'active_test': False},
    )
    date_from = fields.Date(required=True)
    date_to = fields.Date(required=True)
    statement_type_id = fields.Many2one(
        "cssk.income.tax.type",
        domain="[('version_id', '=', version_id)]",
        required=True,
    )

    line_ids = fields.One2many(
        "cssk.income.tax.return.line", "return_id",
        copy=True)  # carry the manual tax spine onto a dodatočné amendment

    # Health roll-up: drillable leaves that don't tie to their journal items.
    unreconciled_count = fields.Integer(compute="_compute_unreconciled_count")

    @api.depends("line_ids.has_source", "line_ids.source_reconciles")
    def _compute_unreconciled_count(self):
        for ret in self:
            ret.unreconciled_count = len(ret.line_ids.filtered(
                lambda ln: ln.has_source and not ln.source_reconciles))

    def action_view_unreconciled(self):
        self.ensure_one()
        bad = self.line_ids.filtered(
            lambda ln: ln.has_source and not ln.source_reconciles)
        return {
            "type": "ir.actions.act_window",
            "name": _("Unreconciled rows"),
            "res_model": "cssk.income.tax.return.line",
            "view_mode": "list",
            "domain": [("id", "in", bad.ids)],
            "context": {"create": False, "delete": False},
        }

    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("preview", "Preview"),
            ("exported", "Exported"),
            ("submitted", "Submitted"),
            ("cancelled", "Cancelled"),
            # Terminal, and off the workflow rather than at the end of it. A
            # historical filing was completed and submitted years ago by
            # whoever ran the previous system; it is a RECORD of a filing, not
            # a filing in progress, so no transition leads into or out of it.
            # Set automatically whenever ``legacy`` is set — see
            # ``cssk.statutory.submission.mixin``, which owns that rule so the
            # importer cannot set one without the other.
            ("legacy", "Historical filing"),
        ],
        default="draft",
        tracking=True,
    )
    xml_attachment_id = fields.Many2one("ir.attachment", readonly=True)
    original_return_id = fields.Many2one(
        "cssk.income.tax.return", string="Amends", copy=False, readonly=True,
        index=True,
        help="The originally-filed return this amended / corrective return amends.")
    amendment_ids = fields.One2many(
        "cssk.income.tax.return", "original_return_id", string="Amendments")

    # Year-end income-tax provision (MD 591 / D 341)
    provision_journal_id = fields.Many2one(
        "account.journal", copy=False,
        domain="[('company_id', '=', company_id), ('type', '=', 'general')]",
        help="Journal for the year-end income-tax provision entry. Defaults to "
             "the company's first general journal.")
    provision_expense_account_id = fields.Many2one(
        "account.account", string="Tax expense account", copy=False,
        domain="[('company_ids', 'in', company_id)]",
        help="Override; defaults to the version's 591 code prefix.")
    provision_payable_account_id = fields.Many2one(
        "account.account", string="Tax payable account", copy=False,
        domain="[('company_ids', 'in', company_id)]",
        help="Override; defaults to the version's 341 code prefix.")
    provision_move_id = fields.Many2one(
        "account.move", string="Provision entry", readonly=True, copy=False)
    provision_amount = fields.Monetary(
        compute="_compute_provision", currency_field="currency_id",
        help="Current income tax to provision = value of the version's "
             "provision_line_code (e.g. r1050 / r340).")
    provision_posted = fields.Boolean(
        compute="_compute_provision", string="Provision posted")

    @api.depends("line_ids.value", "version_id.provision_line_code",
                 "provision_move_id.state")
    def _compute_provision(self):
        for ret in self:
            code = ret.version_id.provision_line_code
            line = ret.line_ids.filtered(lambda l: l.code == code)[:1]
            ret.provision_amount = line.value if (code and line) else 0.0
            ret.provision_posted = ret.provision_move_id.state == "posted"

    @api.depends("date_from", "date_to")
    def _compute_name(self):
        for ret in self:
            ret.name = "DPPO %s — %s" % (
                ret.date_from or "",
                ret.date_to or "",
            )

    # ------------------------------------------------------------------
    # Compute (the evaluator)
    # ------------------------------------------------------------------
    def action_compute_lines(self):
        self._cssk_check_not_legacy(_("recomputed"))
        self.ensure_one()
        if self.state not in ("draft", "preview"):
            raise UserError(_("Only draft returns can be recomputed."))
        overrides = {
            line.code: line.manual_value
            for line in self.line_ids
            if line.is_overridden
        }
        self.line_ids.unlink()
        # ONE grouped query serves every 'account' line of this compute pass
        # (the prefix matching happens in Python in _eval_accounts).
        balances = self._cssk_account_balance_map(self.date_from, self.date_to)
        computed = {}
        vals = []
        for ldef in self.version_id.line_def_ids.sorted("sequence"):
            overridden = ldef.code in overrides
            src_domain = []
            if overridden:
                value = overrides[ldef.code]
            elif ldef.kind == "account":
                value = self._eval_accounts(ldef.account_formula, balances)
                src_domain = self._account_source_domain(ldef.account_formula)
            elif ldef.kind == "aggregate":
                value = self._eval_aggregate(ldef.aggregate_formula, computed)
            elif ldef.kind == "asset_diff":
                value = self._eval_asset_diff(ldef.account_formula)
            else:  # manual without an override
                value = 0.0
            computed[ldef.code] = value
            vals.append(
                {
                    "return_id": self.id,
                    "code": ldef.code,
                    "name": ldef.name,
                    "sequence": ldef.sequence,
                    "value": value,
                    "kind": ldef.kind,
                    "in_xml": ldef.in_xml,
                    "manual_value": value if overridden else 0.0,
                    "is_overridden": overridden,
                    "source_domain": repr(src_domain),
                    "formula_note": (
                        ldef.aggregate_formula if ldef.kind == "aggregate"
                        else (_("manual input") if ldef.kind == "manual" else "")),
                }
            )
        self.env["cssk.income.tax.return.line"].create(vals)
        self.state = "preview"

    def _eval_asset_diff(self, which):
        """Book−tax depreciation difference for the period, from
        ``account_asset_tax`` if installed (soft dependency). ``which`` (the line
        def's ``account_formula``) selects ``addback`` (book>tax → increases the
        base), ``deduction`` (tax>book → lowers it) or ``difference`` (signed).
        Returns 0.0 when the tax-asset module is not installed.
        """
        company = self.company_id
        if not hasattr(company, "_cssk_asset_book_tax_difference"):
            return 0.0
        data = company._cssk_asset_book_tax_difference(self.date_from, self.date_to)
        return data.get((which or "difference").strip(), 0.0)

    def _eval_accounts(self, formula, balances=None):
        """Period balance of the comma-separated P&L code prefixes.

        A leading '-' on a prefix negates its contribution. Returns the net
        as a positive profit (revenues − expenses) given the prefix signs in
        the formula.

        ``balances`` is the pre-fetched ``{account_code: balance}`` map of
        the period (``_cssk_account_balance_map`` — ONE grouped query per
        compute pass instead of one search per prefix per line). The token
        semantics are IDENTICAL to the historical per-prefix search: default
        sign −1, a leading '-' flips to +1, and an account matched by two
        tokens contributes once PER TOKEN with each token's sign.
        """
        formula = (formula or "").strip()
        if not formula:
            return 0.0
        if balances is None:
            balances = self._cssk_account_balance_map(
                self.date_from, self.date_to)
        # Shared matcher in l10n_cssk_core, with THIS statement's inverted sign
        # convention preserved: a bare prefix counts −1 and a leading '-' flips
        # it to +1, so the net reads as a positive profit. Do not "normalise"
        # that to the FS convention — every row definition here depends on it.
        return self._cssk_eval_formula(formula, balances, default_sign=-1.0)

    def _account_source_domain(self, formula):
        """A small, serialisable domain for the P&L move lines a ``kind=account``
        line aggregates — re-queried on drill-down (the result line spans every
        P&L line of the year), not stored as ids."""
        codes = sorted({t.strip().lstrip("-")
                        for t in (formula or "").split(",") if t.strip()})
        codes = [c for c in codes if c]
        if not codes:
            return []
        acc_dom = ["|"] * (len(codes) - 1) + [
            ("account_id.code", "=like", c + "%") for c in codes]
        return [("parent_state", "=", "posted"),
                ("company_id", "=", self.company_id.id),
                ("date", ">=", str(self.date_from)),
                ("date", "<=", str(self.date_to))] + acc_dom

    def _eval_aggregate(self, formula, computed):
        if not formula:
            return 0.0
        return float(safe_eval(formula, dict(computed)) or 0.0)

    # ------------------------------------------------------------------
    # Export — the pipeline lives in cssk.statutory.submission.mixin;
    # only the form-specific hooks are parameterized here. The income-tax
    # return thereby also gains the ``_cssk_check_kontroly`` stage (a no-op
    # until a country module supplies DPPO kontrolné pravidlá).
    # ------------------------------------------------------------------
        #: LAZY, not a plain string. This names the form in error messages and
    #: on the comparison screen, and as a bare literal it was in no .pot at
    #: all — untranslatable in every language, not merely untranslated.
    #: ``_lt`` defers the lookup to render time, which is what lets a
    #: module-level constant be translated at all; render it with
    #: ``self.env._(...)`` so it picks up the READER's language.
    _cssk_form_label = _lt("income-tax return")
    _cssk_xml_name_fallback = "income_tax_return"

    def _cssk_export_draft_error(self):
        return _("Compute the return before exporting.")

    def _cssk_preflight_export(self):
        """DPPO identification: the SK template emits the DIČ
        (``l10n_sk_dic``, falling back to the VAT number), the CZ one the
        DIČ derived from the VAT number — either identifier satisfies the
        form, so accept whichever is set (unlike the VAT-only base check).

        The DIČ field is read by feature detection: it lives in
        ``l10n_sk_base``, and this module is the shared CZ/SK base, which a
        Czech-only deployment installs without any Slovak module. In Czech
        usage the DIČ *is* the VAT number, so ``vat`` alone is the right
        answer there.
        """
        for rec in self:
            if not (getattr(rec.company_id, "l10n_sk_dic", False) or rec.company_id.vat):
                raise UserError(_(
                    "Company '%(company)s' has neither a Tax ID (DIČ) nor a "
                    "VAT number set, but the income-tax return XML must carry "
                    "the filer's tax identification. Set 'Tax ID (DIČ)' or "
                    "'Tax ID' (VAT) on the company (Settings → Users & "
                    "Companies → Companies → %(company)s) and export again.",
                    company=rec.company_id.display_name))
        return True

    def _cssk_render_context(self):
        ctx = super()._cssk_render_context()
        ctx.update({
            "lines": self.line_ids,
            "values": {line.code: line.value for line in self.line_ids},
            "values_fmt": {
                line.code: "%.2f" % line.value for line in self.line_ids
            },
            # Not every row on a DPPO is money. The older vzory carry counts
            # and years typed as an INTEGER union, and "0.00" is not a valid
            # value of one — the export is refused, which is the right answer
            # and a confusing one to arrive at from a form full of amounts.
            "values_int": {
                line.code: "%d" % round(line.value) for line in self.line_ids
            },
        })
        return ctx

    # ------------------------------------------------------------------
    # Year-end income-tax provision (MD splatná daň 591 / D daňový záväzok 341)
    # ------------------------------------------------------------------
    # Completes the DPPO loop: the return computes the tax, this books it as the
    # závierka provision so the VZS after-tax result and the Súvaha tax payable
    # close. Posts the FULL computed tax (provision_line_code). For a dodatočné
    # amendment, post the *difference* manually — re-posting would double-book.
    def _resolve_provision_account(self, override, prefix, label):
        if override:
            return override
        acc = self.env["account.account"].search(
            [("company_ids", "in", self.company_id.id),
             ("code", "=like", (prefix or "") + "%")], order="code", limit=1)
        if not acc:
            raise UserError(_(
                "No %(label)s account (code prefix %(p)s) found for %(co)s — "
                "set it explicitly on the return.",
                label=label, p=prefix or "?", co=self.company_id.display_name))
        return acc

    def action_post_provision(self):
        self.ensure_one()
        if self.provision_move_id:
            raise UserError(_(
                "A provision entry already exists (%s). Reverse it first.",
                self.provision_move_id.name))
        if self.state == "draft":
            raise UserError(_("Compute the return before posting the provision."))
        code = self.version_id.provision_line_code
        if not code:
            raise UserError(_(
                "Set 'provision_line_code' on the version (e.g. r1050 / r340) "
                "to post the income-tax provision."))
        amount = self.currency_id.round(self.provision_amount)
        if amount <= 0:
            raise UserError(_(
                "Computed income tax (line %(c)s) is %(a)s — nothing to "
                "provision.", c=code, a=amount))
        exp = self._resolve_provision_account(
            self.provision_expense_account_id,
            self.version_id.provision_expense_code or "591",
            _("income-tax expense"))
        pay = self._resolve_provision_account(
            self.provision_payable_account_id,
            self.version_id.provision_payable_code or "341",
            _("income-tax payable"))
        journal = self.provision_journal_id or self.env["account.journal"].search(
            [("company_id", "=", self.company_id.id), ("type", "=", "general")],
            limit=1)
        if not journal:
            raise UserError(_("No general journal found for the provision entry."))
        move = self.env["account.move"].create({
            "move_type": "entry", "journal_id": journal.id, "date": self.date_to,
            "ref": _("%s — splatná daň z príjmov", self.name),
            "company_id": self.company_id.id,
            "line_ids": [
                Command.create({
                    "account_id": exp.id, "name": _("Splatná daň z príjmov"),
                    "debit": amount, "credit": 0.0}),
                Command.create({
                    "account_id": pay.id, "name": _("Daň z príjmov — záväzok"),
                    "debit": 0.0, "credit": amount}),
            ]})
        move.action_post()
        self.provision_move_id = move.id
        self.message_post(body=_(
            "Posted income-tax provision %(amt)s: %(exp)s / %(pay)s (%(mv)s).",
            amt=amount, exp=exp.code, pay=pay.code, mv=move.name))
        return True

    def action_reverse_provision(self):
        self.ensure_one()
        move = self.provision_move_id
        if not move:
            raise UserError(_("No provision entry to reverse."))
        if move.state == "posted":
            move._reverse_moves(
                [{"date": move.date, "ref": _("Reversal of %s", move.name)}],
                cancel=True)
        else:
            move.unlink()
        self.provision_move_id = False
        return True

    def action_view_provision(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window", "res_model": "account.move",
            "res_id": self.provision_move_id.id, "view_mode": "form",
            "target": "current",
        }


class CSSKIncomeTaxReturnLine(models.Model):
    _name = "cssk.income.tax.return.line"
    _description = "Income Tax Return Line"
    _order = "return_id, sequence, code"

    return_id = fields.Many2one(
        "cssk.income.tax.return", required=True, ondelete="cascade", index=True
    )
    company_currency_id = fields.Many2one(related="return_id.currency_id")
    code = fields.Char(required=True)
    name = fields.Char()
    sequence = fields.Integer(default=10)
    kind = fields.Selection(
        [
            ("account", "Accounting result (P&L)"),
            ("aggregate", "Aggregate"),
            ("asset_diff", "Asset book-vs-tax depreciation difference"),
            ("manual", "Manual"),
        ],
    )
    in_xml = fields.Boolean()
    value = fields.Monetary(
        currency_field="company_currency_id",
        help="Effective value: the computed result, or the manual override.",
    )
    is_overridden = fields.Boolean(
        string="Override",
        help="Tick to enter a manual value — used for the tax-adjustment lines "
        "and to correct a computed line. Preserved and fed into dependent "
        "aggregate lines on recompute.",
    )
    manual_value = fields.Monetary(currency_field="company_currency_id")

    # --- drill-down: the P&L journal items behind an account-based (leaf) line ---
    is_leaf = fields.Boolean(compute="_compute_is_leaf", store=True)
    # Tier-3 transparency: how a derived row's value was obtained.
    formula_note = fields.Char(string="Derivation")
    # Drill-down: stored as a small serialised domain, re-queried on click.
    source_domain = fields.Char()
    has_source = fields.Boolean(compute="_compute_has_source")
    source_reconciles = fields.Boolean(compute="_compute_source_reconciles")

    @api.depends("kind")
    def _compute_is_leaf(self):
        for line in self:
            line.is_leaf = line.kind in ("account", "asset_diff")

    @api.depends("source_domain")
    def _compute_has_source(self):
        for line in self:
            line.has_source = bool(line.source_domain
                                   and line.source_domain not in ("[]", "False"))

    @api.depends("source_domain", "value")
    def _compute_source_reconciles(self):
        # Batched: ONE grouped query per return (per distinct period window)
        # instead of one _read_group per line on every form load. All leaf
        # domains share the period/company base and differ only in their
        # account-code prefixes, so the prefix matching happens in Python on
        # a {account_code: balance} map.
        for ret, lines in self.grouped("return_id").items():
            maps = {}
            for line in lines:
                if not line.has_source:
                    line.source_reconciles = False
                    continue
                domain = safe_eval(line.source_domain)
                prefixes = [
                    term[2][:-1] for term in domain
                    if isinstance(term, (list, tuple))
                    and term[0] == "account_id.code" and term[1] == "=like"]
                base = [
                    list(term) for term in domain
                    if isinstance(term, (list, tuple))
                    and term[0] != "account_id.code"]
                key = repr(base)
                if key not in maps:
                    maps[key] = ret._cssk_balances_by_account_code(
                        base, company=ret.company_id)
                s = sum(
                    balance for code, balance in maps[key].items()
                    if any(code.startswith(p) for p in prefixes))
                line.source_reconciles = abs(abs(s) - abs(line.value)) < 0.5

    def action_view_source_lines(self):
        self.ensure_one()
        view = self.env.ref(
            "l10n_cssk_income_tax_base.view_move_line_dppo_audit",
            raise_if_not_found=False)
        return {
            "type": "ir.actions.act_window",
            "name": _("Source documents — %s %s") % (
                self.code or "", self.name or ""),
            "res_model": "account.move.line",
            "view_mode": "list,form",
            "views": [(view.id if view else False, "list"), (False, "form")],
            "domain": safe_eval(self.source_domain or "[]"),
            "context": {"create": False, "delete": False,
                        "group_by": ["account_id"]},
        }

    @api.onchange("is_overridden", "manual_value")
    def _onchange_override(self):
        for line in self:
            if line.is_overridden:
                line.value = line.manual_value
