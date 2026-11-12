# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Reviewed loss carryforward form facts feeding the existing native row410."""
from datetime import date
from decimal import Decimal, InvalidOperation

from dateutil.relativedelta import relativedelta
from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.addons.l10n_cssk_core.tools import statutory_round


class DppoTableD(models.Model):
    _inherit = "cssk.income.tax.return"

    l10n_sk_table_d_ids = fields.One2many(
        "l10n.sk.dppo.table.d.line", "return_id", copy=True, string="Table D prior tax losses")
    l10n_sk_form_notes = fields.Text(string="Official form special records")

    def write(self, values):
        if {"l10n_sk_table_d_ids", "l10n_sk_form_notes"} & values.keys():
            self._l10n_sk_form_inputs_editable()
        return super().write(values)

    def _l10n_sk_dppo_table_d_payload(self, *, compare_row=True):
        self.ensure_one()
        self.check_access("read")
        rows = {line.code: line.value for line in self.line_ids}
        base = max(0, rows.get("r400", 0))
        micro = self.l10n_sk_form_micro_taxpayer
        if micro and (self.l10n_sk_form_controlled_transactions or rows.get("r560", 0) > 60000
                or self.date_to < self.date_from + relativedelta(months=12, days=-1)):
            raise UserError(_("Review micro-taxpayer status: controlled transactions, income above EUR 60,000 or a shorter tax period exclude it."))
        items = [item._form_payload() for item in self.l10n_sk_table_d_ids.sorted("column")]
        if len({item["column"] for item in items}) != len(items):
            raise UserError(_("Use each official Table D column only once."))
        regular = [item for item in items if item["column"] >= 4]
        if any(first["date_to"] >= second["date_from"] for first, second in zip(regular, regular[1:])):
            raise UserError(_("Enter prior Table D periods from oldest to newest without overlap."))
        normal = sum(item["deducted"] for item in regular
                     if not micro or item["date_from"] < "2021-01-01")
        if self.currency_id.compare_amounts(normal, statutory_round(base * .5, 2)) > 0:
            raise UserError(_("The ordinary Table D loss deduction cannot exceed 50 percent of row 400."))
        total = statutory_round(sum(item["deducted"] for item in items), 2)
        if self.currency_id.compare_amounts(total, base) > 0:
            raise UserError(_("The total Table D deduction cannot exceed the positive row 400 base."))
        if compare_row and self.currency_id.compare_amounts(total, rows.get("r410", 0)):
            raise UserError(_("Apply the reviewed Table D deduction to native row 410 and recompute the return."))
        if any(item["column"] == 1 and item["deducted"] for item in items) and not (self.l10n_sk_form_notes or "").strip():
            raise UserError(_("Explain the special Table D column 1 deduction in the official special records."))
        return {"items": items, "total": total}

    def action_apply_table_d_deduction(self):
        self.ensure_one()
        with self.env.cr.savepoint():
            self._l10n_sk_form_inputs_editable()
            if self.version_id.l10n_sk_dppo_layout != "2026" or not self.line_ids:
                raise UserError(_("Compute the published paper-form return before applying Table D."))
            data = self._l10n_sk_dppo_table_d_payload(compare_row=False)
            line = self.line_ids.filtered(lambda row: row.code == "r410")
            line.write({"is_overridden": True, "manual_value": data["total"]})
            result = self.action_compute_lines()
            # The native recomputation can refresh a changed GL/manual base.
            # Recheck against that result before the savepoint may commit.
            self._l10n_sk_dppo_table_d_payload()
            return result

    def action_post_provision(self):
        self.ensure_one()
        if self.version_id.l10n_sk_dppo_layout == "2026" and (
                self.l10n_sk_table_d_ids or self.line_ids.filtered(lambda row: row.code == "r410" and row.value)):
            self._l10n_sk_dppo_table_d_payload()
        return super().action_post_provision()

    def _l10n_sk_dppo_pdf_annex_payload(self):
        result = super()._l10n_sk_dppo_pdf_annex_payload()
        result["table_d"] = self._l10n_sk_dppo_table_d_payload()
        result["notes"] = self.l10n_sk_form_notes or ""
        return result


class DppoTableDLine(models.Model):
    _name = "l10n.sk.dppo.table.d.line"
    _description = "DPPO Table D prior tax loss"
    _inherit = "l10n.sk.dppo.form.input.mixin"
    _check_company_auto = True
    _order = "column, id"

    column = fields.Selection([(str(number), "D %s" % number) for number in range(1, 9)],
                              default="4", required=True, string="Official Table D column")
    date_from = fields.Date(string="Loss period from")
    date_to = fields.Date(string="Loss period to")
    source_return_id = fields.Many2one("cssk.income.tax.return", string="Native original loss return",
                                      check_company=True, domain="[('company_id', '=', company_id)]")
    loss_amount = fields.Monetary(string="Originally declared tax loss", required=True)
    prior_deducted = fields.Monetary(string="Deducted in prior tax periods")
    deducted = fields.Monetary(string="Deducted in this tax period")
    subsequent_period_number = fields.Integer(string="Following tax-period number", default=1,
        help="Reviewed ordinal from 1 to 5 for ordinary section 30 losses. Count tax periods, including short periods, not elapsed calendar years.")
    remaining = fields.Monetary(string="Remaining for future tax periods", compute="_compute_balance")
    expired = fields.Monetary(string="Unused balance expiring after this period", compute="_compute_balance")
    evidence = fields.Text(string="Loss eligibility evidence")

    @api.depends("loss_amount", "prior_deducted", "deducted", "column", "subsequent_period_number")
    def _compute_balance(self):
        for item in self:
            balance = statutory_round(item.loss_amount - item.prior_deducted - item.deducted, 2)
            last = int(item.column or "4") >= 4 and item.subsequent_period_number == 5
            item.remaining = 0 if last else balance
            item.expired = balance if last else 0

    def _form_payload(self):
        self.ensure_one()
        self.check_access("read")
        for value in (self.loss_amount, self.prior_deducted, self.deducted):
            try:
                number = Decimal(str(value))
                if not number.is_finite() or number < 0 or number != number.quantize(Decimal(".01")):
                    raise ValueError()
            except (InvalidOperation, TypeError, ValueError) as error:
                raise UserError(_("Use finite nonnegative Table D amounts in whole eurocents.")) from error
        if not self.loss_amount or self.currency_id.compare_amounts(self.prior_deducted + self.deducted, self.loss_amount) > 0:
            raise UserError(_("Table D deductions cannot exceed the positive originally declared loss."))
        column = int(self.column)
        if column != 1 and (not self.date_from or not self.date_to
                or self.date_from > self.date_to or self.date_to >= self.return_id.date_from):
            raise UserError(_("Table D must describe an earlier loss period; the current-period loss stays in row 400."))
        if column >= 4 and (self.date_from < date(2020, 1, 1)
                or not 1 <= self.subsequent_period_number <= 5):
            raise UserError(_("Review the ordinary loss period and its following-tax-period number from 1 to 5."))
        if (column >= 4 and self.date_to + relativedelta(days=1) == self.return_id.date_from
                and self.subsequent_period_number != 1):
            raise UserError(_("An immediately following loss-deduction period must have ordinal 1."))
        source = self.source_return_id
        if source:
            loss = source.line_ids.filtered(lambda row: row.code == "r400")
            if (source.company_id != self.company_id or source == self.return_id
                    or source.date_from != self.date_from or source.date_to != self.date_to
                    or source.state not in ("preview", "exported", "submitted", "legacy")
                    or len(loss) != 1 or loss.value >= 0
                    or self.currency_id.compare_amounts(self.loss_amount, -loss.value)):
                raise UserError(_("The linked native loss return must match the company, loss period and declared loss amount."))
        return {"column": column, "date_from": str(self.date_from) if self.date_from else None,
                "date_to": str(self.date_to) if self.date_to else None,
                "loss": self.loss_amount, "prior": self.prior_deducted,
                "deducted": self.deducted, "remaining": self.remaining,
                "expired": self.expired}
