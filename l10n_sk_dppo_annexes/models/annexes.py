# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Itemised evidence feeds native Table A return lines; native B is untouched."""

from collections import defaultdict
from decimal import Decimal, InvalidOperation

from odoo import _, api, fields, models
from odoo.exceptions import UserError


class DppoAnnexes(models.Model):
    _inherit = "cssk.income.tax.return"

    l10n_sk_annexes_enabled = fields.Boolean(string="Use itemised Table A workpaper")
    l10n_sk_annexes_reviewed = fields.Boolean(
        string="Table A workpaper reviewed", copy=False
    )
    l10n_sk_annexes_evidence = fields.Text(string="Table A review evidence", copy=False)
    l10n_sk_annex_a_ids = fields.One2many(
        "l10n.sk.dppo.annex.a.line",
        "return_id",
        copy=True,
        string="Table A non-deductible expenses",
    )
    # Ownership of ordinary overrides, NOT an export/ledger proof. Copied with
    # native return lines so amendments and disabling can release them correctly.
    l10n_sk_annex_a_overrides = fields.Json(readonly=True, copy=True)

    def _annex_editable(self):
        self.check_access("write")
        if not self:
            return
        self.flush_recordset(["state"])
        self.env.cr.execute(
            "SELECT id FROM cssk_income_tax_return WHERE id IN %s ORDER BY id FOR NO KEY UPDATE",
            [tuple(sorted(self.ids))],
        )
        self.invalidate_recordset(["state"])
        if any(rec.state not in ("draft", "preview") for rec in self):
            raise UserError(
                _("Reset the unfiled DPPO to draft before changing its workpaper.")
            )
        # A child-only edit must also invalidate a concurrent native filing's
        # REPEATABLE READ snapshot. Updating the parent's ordinary audit stamp
        # needs neither a proof ledger nor a separate financial-source registry.
        self.env.cr.execute(
            "UPDATE cssk_income_tax_return SET write_date=clock_timestamp(),write_uid=%s WHERE id IN %s",
            [self.env.uid, tuple(sorted(self.ids))],
        )
        self.invalidate_recordset(["write_date", "write_uid"])

    def write(self, values):
        if {
            "l10n_sk_annexes_enabled",
            "l10n_sk_annexes_reviewed",
            "l10n_sk_annexes_evidence",
            "l10n_sk_annex_a_ids",
        } & values.keys():
            self._annex_editable()
        return super().write(values)

    def _annex_a_definitions(self):
        self.ensure_one()
        return self.version_id.line_def_ids.filtered(
            lambda row: row.kind == "manual"
            and row.code in {"a%02d" % number for number in range(1, 17)}
        )

    def _annex_a_sums(self):
        self.ensure_one()
        if self.country_id.code != "SK" or not self._annex_a_definitions():
            raise UserError(
                _("This return version has no supported Slovak Table A inputs.")
            )
        if (
            not self.l10n_sk_annexes_reviewed
            or not (self.l10n_sk_annexes_evidence or "").strip()
        ):
            raise UserError(
                _("Review the itemised Table A and retain its review evidence.")
            )
        allowed = set(self._annex_a_definitions().mapped("code"))
        amounts = defaultdict(Decimal)
        for item in self.l10n_sk_annex_a_ids:
            if item.row_code not in allowed:
                raise UserError(_("Choose a Table A input row of this return version."))
            if not (item.evidence or "").strip():
                raise UserError(_("Each Table A expense item needs its evidence."))
            try:
                amount = Decimal(str(item.amount))
                if (
                    not amount.is_finite()
                    or amount < 0
                    or amount != amount.quantize(Decimal(".01"))
                ):
                    raise ValueError()
            except (InvalidOperation, TypeError, ValueError) as error:
                raise UserError(
                    _("Use finite nonnegative expense amounts in whole eurocents.")
                ) from error
            amounts[item.row_code] += amount
        return {code: float(amount) for code, amount in amounts.items()}

    def action_compute_lines(self):
        self.ensure_one()
        with self.env.cr.savepoint():
            self._annex_editable()
            previous = self.l10n_sk_annex_a_overrides or {}
            amounts = self._annex_a_sums() if self.l10n_sk_annexes_enabled else {}
            # Native compute creates rows on a first calculation. It also owns
            # all Table B prefill, aggregates, tax spine and amendment differences.
            if not self.line_ids:
                super().action_compute_lines()
            for row in self.line_ids:
                if row.code in amounts:
                    row.write(
                        {"is_overridden": True, "manual_value": amounts[row.code]}
                    )
                elif (
                    row.code in previous
                    and row.is_overridden
                    and not self.currency_id.compare_amounts(
                        row.manual_value, previous[row.code]
                    )
                ):
                    row.write({"is_overridden": False, "manual_value": 0})
            super(DppoAnnexes, self).write({"l10n_sk_annex_a_overrides": amounts})
            return super().action_compute_lines()

    def _cssk_preflight_export(self):
        result = super()._cssk_preflight_export()
        self._annex_a_check_current()
        return result

    def _annex_a_check_current(self):
        self.ensure_one()
        self.check_access("read")
        previous = self.l10n_sk_annex_a_overrides or {}
        amounts = self._annex_a_sums() if self.l10n_sk_annexes_enabled else {}
        if previous != amounts:
            raise UserError(
                _("Recompute the changed Table A workpaper before output or posting.")
            )
        for code, amount in amounts.items():
            row = self.line_ids.filtered(lambda line: line.code == code)
            if len(row) != 1 or self.currency_id.compare_amounts(row.value, amount):
                raise UserError(
                    _(
                        "Recompute the changed Table A workpaper before output or posting."
                    )
                )

    def _l10n_sk_dppo_pdf_annex_payload(self):
        self._annex_a_check_current()
        return super()._l10n_sk_dppo_pdf_annex_payload()

    def action_post_provision(self):
        self._annex_a_check_current()
        return super().action_post_provision()


class AnnexALine(models.Model):
    _name = "l10n.sk.dppo.annex.a.line"
    _description = "DPPO Table A expense item"
    _check_company_auto = True
    _order = "row_code, id"

    return_id = fields.Many2one(
        "cssk.income.tax.return", required=True, ondelete="cascade"
    )
    company_id = fields.Many2one(related="return_id.company_id", store=True)
    currency_id = fields.Many2one(related="return_id.currency_id")
    row_code = fields.Selection(selection="_selection_row_code", required=True)
    row_caption = fields.Char(
        compute="_compute_row_caption", string="Return row caption"
    )
    amount = fields.Monetary(required=True)
    evidence = fields.Text(required=True)

    @api.model
    def _selection_row_code(self):
        identifier = self.env.context.get("default_return_id")
        parent = (
            self.env["cssk.income.tax.return"].browse(identifier).exists()
            if isinstance(identifier, int)
            else False
        )
        version = (
            parent.version_id
            if parent
            else self.env["cssk.income.tax.version"].search(
                [("country_id.code", "=", "SK")],
                order="valid_from desc,id desc",
                limit=1,
            )
        )
        definitions = version.line_def_ids.filtered(lambda row: row.kind == "manual")
        names = {row.code: row.name for row in definitions}
        return [
            ("a%02d" % number, names.get("a%02d" % number, "A%d" % number))
            for number in range(1, 17)
        ]

    @api.depends("row_code", "return_id.version_id")
    def _compute_row_caption(self):
        for item in self:
            item.row_caption = item.return_id.version_id.line_def_ids.filtered(
                lambda row: row.code == item.row_code
            ).name

    @api.model_create_multi
    def create(self, values_list):
        self.check_access("create")
        with self.env.cr.savepoint():
            normalized = [dict(source) for source in values_list]
            for values in normalized:
                values.setdefault(
                    "return_id", self.env.context.get("default_return_id")
                )
                if type(values["return_id"]) is not int or values["return_id"] <= 0:
                    raise UserError(
                        _("Choose the DPPO return before adding a Table A item.")
                    )
            identifiers = sorted({values["return_id"] for values in normalized})
            parents = self.env["cssk.income.tax.return"].browse(identifiers).exists()
            if len(parents) != len(identifiers):
                raise UserError(
                    _("Choose the DPPO return before adding a Table A item.")
                )
            parents.check_access("write")
            by_id = {parent.id: parent for parent in parents}
            for values in normalized:
                parent = by_id[values["return_id"]]
                supplied = values.pop(
                    "company_id", self.env.context.get("default_company_id")
                )
                currency = values.pop(
                    "currency_id", self.env.context.get("default_currency_id")
                )
                if supplied and supplied != parent.company_id.id:
                    raise UserError(
                        _("The Table A item must belong to its DPPO company.")
                    )
                if currency and currency != parent.currency_id.id:
                    raise UserError(_("The Table A item must use its DPPO currency."))
            parents._annex_editable()
            context = dict(self.env.context)
            context.pop("default_company_id", None)
            context.pop("default_currency_id", None)
            return super(AnnexALine, self.with_context(context)).create(normalized)

    def write(self, values):
        self.check_access("write")
        if {"return_id", "company_id", "currency_id"} & values.keys():
            raise UserError(
                _("Table A items cannot be reassigned to another return or company.")
            )
        with self.env.cr.savepoint():
            self.return_id._annex_editable()
            return super().write(values)

    def unlink(self):
        self.check_access("unlink")
        with self.env.cr.savepoint():
            self.return_id._annex_editable()
            return super().unlink()
