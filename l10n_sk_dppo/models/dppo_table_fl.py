# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Ordinary double-entry F/L facts, using the existing ledger and row560."""
import math
import re
from odoo import _, fields, models
from odoo.exceptions import UserError
from odoo.addons.l10n_cssk_core.tools import statutory_round


class DppoTableFL(models.Model):
    _inherit = "cssk.income.tax.return"

    l10n_sk_f_manual = fields.Boolean(string="Use reviewed Table F source figures")
    l10n_sk_f_revenue = fields.Monetary(string="Reviewed Table F revenue")
    l10n_sk_f_cost = fields.Monetary(string="Reviewed Table F costs before income tax")
    l10n_sk_f_evidence = fields.Text(string="Table F source evidence")
    l10n_sk_table_l_ids = fields.One2many("l10n.sk.dppo.table.l.line", "return_id",
        copy=True, string="Table L taxable-revenue adjustments")

    def write(self, values):
        if {"l10n_sk_f_manual", "l10n_sk_f_revenue", "l10n_sk_f_cost",
                "l10n_sk_f_evidence", "l10n_sk_table_l_ids"} & values.keys():
            self._l10n_sk_form_inputs_editable()
        return super().write(values)

    def _l10n_sk_table_fl_payload(self, *, compare_row=True):
        self.ensure_one()
        self.check_access("read")
        if self.l10n_sk_f_manual:
            revenue, cost = self.l10n_sk_f_revenue, self.l10n_sk_f_cost
            if not (self.l10n_sk_f_evidence or "").strip():
                raise UserError(_("Retain the reviewed Table F source evidence."))
        else:
            balances = self._cssk_account_balance_map(self.date_from, self.date_to)
            revenue = self._eval_accounts("6", balances)
            cost = self._eval_accounts("-5,591,592,595,596", balances)
        if any(not math.isfinite(value) for value in (revenue, cost)):
            raise UserError(_("Use finite Table F amounts."))
        profit = statutory_round(revenue - cost, 2)
        rows = {row.code: row.value for row in self.line_ids}
        if self.currency_id.compare_amounts(profit, rows.get("r100", 0)):
            raise UserError(_("Table F revenue less costs must equal row 100; review the ledger or enter reviewed source figures."))
        items = [item._form_payload() for item in self.l10n_sk_table_l_ids.sorted(lambda item: (item.sequence, item.id))]
        if len(items) > 97:
            raise UserError(_("The published Table L has adjustment rows 2 through 98."))
        linked = {}
        for item in items:
            linked[item["row"]] = linked.get(item["row"], 0) + item["amount"]
        if any(self.currency_id.compare_amounts(abs(amount), abs(rows.get("r" + code, 0))) > 0
               for code, amount in linked.items()):
            raise UserError(_("The Table L adjustment linked to a return row cannot exceed that row's amount."))
        taxable = statutory_round(revenue + sum(item["amount"] for item in items), 2)
        if taxable < 0:
            raise UserError(_("Table L taxable revenue cannot be negative."))
        if compare_row and self.currency_id.compare_amounts(taxable, rows.get("r560", 0)):
            raise UserError(_("Apply the reviewed Table L taxable revenue to native row 560 and recompute."))
        return {"revenue": revenue, "cost": cost, "profit": profit,
                "items": items, "taxable": taxable}

    def action_apply_table_l_revenue(self):
        self.ensure_one()
        with self.env.cr.savepoint():
            self._l10n_sk_form_inputs_editable()
            if self.version_id.l10n_sk_dppo_layout != "2026" or not self.line_ids:
                raise UserError(_("Compute the published paper-form return before applying Table L."))
            data = self._l10n_sk_table_fl_payload(compare_row=False)
            self.line_ids.filtered(lambda row: row.code == "r560").write({
                "is_overridden": True, "manual_value": data["taxable"]})
            result = self.action_compute_lines()
            self._l10n_sk_table_fl_payload()
            return result

    def action_post_provision(self):
        self.ensure_one()
        if self.version_id.l10n_sk_dppo_layout == "2026":
            self._l10n_sk_check_advance_relief()
            if self.l10n_sk_table_l_ids or self.l10n_sk_f_manual:
                self._l10n_sk_table_fl_payload()
        return super().action_post_provision()

    def _l10n_sk_dppo_pdf_annex_payload(self):
        result = super()._l10n_sk_dppo_pdf_annex_payload()
        result["table_fl"] = self._l10n_sk_table_fl_payload()
        result["annex_count"] = result.get("annex_count", 5) + max(0, (len(result["table_fl"]["items"]) - 1) // 26)
        return result


class DppoTableLLine(models.Model):
    _name = "l10n.sk.dppo.table.l.line"
    _description = "DPPO Table L taxable-revenue adjustment"
    _inherit = "l10n.sk.dppo.form.input.mixin"
    _order = "sequence, id"
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    description = fields.Char(string="Taxable-revenue adjustment", required=True)
    amount = fields.Monetary(string="Signed taxable-revenue adjustment", required=True)
    return_row = fields.Char(string="Related DPPO row", required=True,
        help="Three-digit row number of the income adjustment in the return.")
    evidence = fields.Text(string="Taxable-revenue classification evidence", required=True)

    def _form_payload(self):
        self.ensure_one()
        self.check_access("read")
        if (not (self.description or "").strip() or not (self.evidence or "").strip()
                or not math.isfinite(self.amount) or not self.amount
                or not re.fullmatch(r"[0-9]{3}", self.return_row or "")
                or "r" + self.return_row not in self.return_id.line_ids.mapped("code")):
            raise UserError(_("Review each Table L description, signed amount, related return row and classification evidence."))
        return {"description": self.description, "amount": self.amount, "row": self.return_row}
