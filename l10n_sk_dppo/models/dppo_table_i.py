# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Entered statutory Table I facts, not postings or a second tax calculation."""
from decimal import Decimal, InvalidOperation
import re

from odoo import _, fields, models
from odoo.exceptions import UserError


class DppoTableI(models.Model):
    _inherit = "cssk.income.tax.return"

    l10n_sk_table_i_ids = fields.One2many(
        "l10n.sk.dppo.table.i.line", "return_id", copy=True, string="Table I transactions")
    l10n_sk_table_i_below_threshold = fields.Boolean(
        string="Other controlled transactions below the statutory threshold",
        help="Only transactions not already included in an aggregated transaction in Table I.")

    def _l10n_sk_form_inputs_editable(self):
        self.check_access("write")
        if not self:
            return
        self.flush_recordset(["state"])
        self.env.cr.execute(
            "SELECT id FROM cssk_income_tax_return WHERE id IN %s ORDER BY id FOR NO KEY UPDATE",
            [tuple(sorted(self.ids))])
        self.invalidate_recordset(["state"])
        if any(ret.state not in ("draft", "preview") for ret in self):
            raise UserError(_("Reset the unfiled return to draft before changing its official annex inputs."))
        # Child-only changes must advance the parent's ordinary audit stamp,
        # forcing a concurrent old REPEATABLE READ export snapshot to retry.
        self.env.cr.execute(
            "UPDATE cssk_income_tax_return SET write_date=clock_timestamp(),write_uid=%s WHERE id IN %s",
            [self.env.uid, tuple(sorted(self.ids))])
        self.invalidate_recordset(["write_date", "write_uid"])

    def write(self, values):
        if {"l10n_sk_table_i_ids", "l10n_sk_table_i_below_threshold"} & values.keys():
            self._l10n_sk_form_inputs_editable()
        return super().write(values)

    def _l10n_sk_dppo_pdf_annex_payload(self):
        self.ensure_one()
        data = super()._l10n_sk_dppo_pdf_annex_payload()
        transactions = self.l10n_sk_table_i_ids.filtered(lambda item: item.section == "transaction")
        loans = self.l10n_sk_table_i_ids - transactions
        entered = bool(transactions or loans or self.l10n_sk_table_i_below_threshold)
        if entered != bool(self.l10n_sk_form_controlled_transactions):
            raise UserError(_("The controlled-transactions declaration must agree with the entered Table I facts."))
        if len(transactions) > 99 or len(loans) > 99:
            raise UserError(_("Table I allows at most 99 transactions and 99 loans; review the statutory reporting priorities."))
        data["table_i"] = {
            "transactions": [item._form_payload() for item in transactions],
            "loans": [item._form_payload() for item in loans],
            "below_threshold": self.l10n_sk_table_i_below_threshold,
        }
        data["annex_count"] = 5 + max(0, (len(transactions) - 1) // 4) + max(0, (len(loans) - 1) // 5)
        return data


class DppoTableILine(models.Model):
    _name = "l10n.sk.dppo.table.i.line"
    _description = "DPPO Table I entered transaction"
    _inherit = "l10n.sk.dppo.form.input.mixin"
    _order = "sequence, id"
    _check_company_auto = True

    sequence = fields.Integer(default=10)
    section = fields.Selection([("transaction", "Transaction"), ("loan", "Loan or credit")],
                               default="transaction", required=True)
    transaction_code = fields.Char(string="Official transaction code", required=True,
        help="Use the two-digit code in the published instructions: 01–37 for transactions, 01–05 for loans.")
    partner_id = fields.Many2one("res.partner", string="Related person", required=True, check_company=True)
    resident_country_code = fields.Char(string="Tax-residence country code", required=True,
        help="Enter the three-digit official country code for the counterparty's tax residence.")
    aggregated = fields.Boolean(string="Aggregated transactions")
    permanent_establishment_link = fields.Boolean(string="Link under section 2(r)")
    tax_effect = fields.Monetary(string="Signed effect on row 400")
    highest_principal = fields.Monetary(string="Highest loan principal during the period")
    closing_principal = fields.Monetary(string="Loan principal at the period end")
    evidence = fields.Text(string="Classification and amount evidence")

    def _form_payload(self):
        self.ensure_one()
        self.check_access("read")
        maximum = 37 if self.section == "transaction" else 5
        if (not re.fullmatch(r"[0-9]{2}", self.transaction_code or "")
                or not 1 <= int(self.transaction_code) <= maximum
                or not re.fullmatch(r"[0-9]{3}", self.resident_country_code or "")
                or self.resident_country_code == "000" or not self.partner_id.name):
            raise UserError(_("Review the Table I transaction code, tax-residence country code and related person's name."))
        if self.partner_id.company_id and self.partner_id.company_id != self.company_id:
            raise UserError(_("The related contact must be shared or belong to the return's company."))
        for value in (self.tax_effect, self.highest_principal, self.closing_principal):
            try:
                number = Decimal(str(value))
                if not number.is_finite() or number != number.quantize(Decimal(".01")):
                    raise ValueError()
            except (InvalidOperation, TypeError, ValueError) as error:
                raise UserError(_("Use finite Table I amounts in whole eurocents.")) from error
        if self.section == "transaction":
            if self.highest_principal or self.closing_principal:
                raise UserError(_("Enter loan principal in the loan section of Table I."))
        elif (self.tax_effect or self.aggregated or self.permanent_establishment_link
              or self.highest_principal < 0 or self.closing_principal < 0
              or self.closing_principal > self.highest_principal):
            raise UserError(_("Review Table I loan amounts: the nonnegative closing principal cannot exceed the highest principal."))
        return {"code": self.transaction_code, "name": self.partner_id.name,
                "country": self.resident_country_code, "aggregated": self.aggregated,
                "permanent_link": self.permanent_establishment_link,
                "effect": self.tax_effect, "highest": self.highest_principal,
                "closing": self.closing_principal}
