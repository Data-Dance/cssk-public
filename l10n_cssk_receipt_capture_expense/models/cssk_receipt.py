# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import _, api, fields, models
from odoo.exceptions import UserError

from odoo.addons.l10n_cssk_receipt_capture.tools.amounts import reconciles


class CSSKReceipt(models.Model):
    _inherit = "cssk.receipt"

    expense_ids = fields.One2many(
        "hr.expense", "cssk_receipt_id", string="Expenses", readonly=True)
    expense_count = fields.Integer(compute="_compute_expense_count")

    @api.depends("expense_ids")
    def _compute_expense_count(self):
        for receipt in self:
            receipt.expense_count = len(receipt.expense_ids)

    # ------------------------------------------------------------------
    def _expense_product(self):
        self.ensure_one()
        product = self.company_id.cssk_receipt_expense_product_id
        if product:
            return product
        Product = self.env["product.product"]
        expensable = Product.search([("can_be_expensed", "=", True)])
        product = expensable.filtered(
            lambda p: p.default_code == "EXP_GEN")[:1] or expensable[:1]
        if not product:
            raise UserError(_(
                "No expense category exists. Create one (a product with "
                "'Can be Expensed' set) or name it in Settings ▸ Accounting ▸ "
                "Fiscal Receipt Capture."))
        return product

    def _expense_employee(self):
        """The employee the expense belongs to.

        The user capturing the receipt, which is who photographed it. An
        accountant capturing somebody else's receipt sets the employee
        afterwards; guessing would be worse than asking.
        """
        self.ensure_one()
        employee = self.env.user.employee_id
        if not employee:
            raise UserError(_(
                "%s has no employee record, so an expense cannot be created "
                "for them. Create the employee, or post the receipt as a "
                "vendor bill instead.", self.env.user.display_name))
        return employee

    def _expense_parts(self):
        """The receipt's VAT split, as the expense posts it: ``[(gross, tax, rate)]``.

        One part per VAT rate when the VAT is deductible — the receipt is still
        ONE expense, and the expense's journal entry carries a base and a VAT
        line per part (see ``hr.expense._cssk_rate_parts``). A single untaxed
        part for the whole gross when it is not deductible: above the
        simplified-invoice limit the VAT is part of the cost. A rate the recap
        lists at 0.00 (tap water at 19 %) is not a part: it would put a second
        tax on the expense and Odoo would stack the two on one base.
        """
        self.ensure_one()
        if not self.vat_deductible:
            return [(self.amount_total, self.env["account.tax"], None)]
        rows = self.tax_summary_ids
        if not rows:
            raise UserError(_(
                "%s has no VAT recap, so there is no way to split it into "
                "expenses. Post it as a vendor bill instead.", self.display_name))
        parts = []
        for row in rows:
            if self.currency_id.is_zero(row.amount_untaxed + row.amount_tax):
                continue
            tax = self._checked_tax_for_rate(row.vat_rate)
            if not tax:
                raise UserError(_(
                    "No purchase tax is mapped for %g%%. Without it the expense "
                    "would carry no VAT and the deduction would be lost.",
                    row.vat_rate))
            parts.append((row.amount_untaxed + row.amount_tax, tax, row.vat_rate))
        return parts

    def _expense_label(self):
        self.ensure_one()
        seller = self.partner_id.name or self.seller_name or self.display_name
        if not self.vat_deductible:
            return _("%s (VAT not deductible)", seller)
        return seller

    def _expense_amount_vals(self):
        """What a receipt sets on its one expense: the total and every rate's tax.

        The expense shows the taxes for what they are; its VAT figure and its
        journal entry come from the receipt's split, never from Odoo applying
        all of them to one base.
        """
        self.ensure_one()
        parts = self._expense_parts()
        taxes = self.env["account.tax"].union(*(tax for _gross, tax, _rate in parts))
        return {
            "name": self._expense_label(),
            "date": self._issue_local_date() or fields.Date.context_today(self),
            "currency_id": self.currency_id.id,
            "quantity": 1.0,
            # The gross is what the receipt states. hr.expense computes its taxes
            # with special_mode="total_included", so the net and the VAT come out
            # of this figure whether or not the tax is price-included — the
            # ordinary tax-excluded taxes a chart ships, and that the vendor-bill
            # path insists on, work here too. _verify_expenses still checks.
            "total_amount_currency": self.amount_total,
            "tax_ids": [fields.Command.set(taxes.ids)],
        }

    def _prepare_expense_vals(self):
        self.ensure_one()
        return {
            **self._expense_amount_vals(),
            "cssk_receipt_id": self.id,
            "company_id": self.company_id.id,
            "employee_id": self._expense_employee().id,
            "product_id": self._expense_product().id,
            "vendor_id": self.partner_id.id or False,
        }

    def action_create_expenses(self):
        """The receipt as ONE expense, whatever its VAT rates."""
        expenses = self.env["hr.expense"]
        for receipt in self:
            if receipt.state != "captured":
                raise UserError(_(
                    "Only a captured, reconciled receipt can become expenses. "
                    "%(name)s is %(state)s.",
                    name=receipt.display_name, state=receipt.state))
            if receipt.expense_ids:
                raise UserError(_(
                    "%(name)s already has %(count)s expense(s).",
                    name=receipt.display_name, count=len(receipt.expense_ids)))
            created = receipt.env["hr.expense"].create(
                receipt._prepare_expense_vals())
            receipt._verify_expenses(created)
            receipt.message_post(body=_("Expense created from this receipt."))
            expenses |= created
        return expenses

    def _verify_expenses(self, expenses):
        """Refuse expenses whose total or VAT does not match the receipt."""
        self.ensure_one()
        # Stored computes on records created a moment ago: read them back from
        # the database rather than trusting the in-memory values.
        expenses.flush_recordset()
        expenses.invalidate_recordset(
            ["total_amount_currency", "tax_amount_currency"])
        total = self._round(sum(expenses.mapped("total_amount_currency")))
        tax = self._round(sum(expenses.mapped("tax_amount_currency")))
        expected_tax = self.amount_tax if self.vat_deductible else 0.0
        if not reconciles(total, self.amount_total, tolerance=0.02):
            raise UserError(_(
                "The expenses total %(got).2f but the receipt totals "
                "%(want).2f. Nothing was kept.",
                got=total, want=self.amount_total))
        if not reconciles(tax, expected_tax, tolerance=0.02):
            raise UserError(_(
                "The expenses carry %(got).2f of VAT but %(want).2f was "
                "expected. Nothing was kept.", got=tax, want=expected_tax))

    def action_open_expenses(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Expenses"),
            "res_model": "hr.expense",
            "view_mode": "list,form",
            "domain": [("cssk_receipt_id", "=", self.id)],
        }
