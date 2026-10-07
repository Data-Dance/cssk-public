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

    def _prepare_expense_vals(self, tax_row, tax):
        self.ensure_one()
        label = _("%(seller)s — items at %(rate)g%% VAT",
                  seller=self.partner_id.name or self.seller_name or "",
                  rate=tax_row.vat_rate)
        return {
            "name": label.strip(" —"),
            "cssk_receipt_id": self.id,
            "company_id": self.company_id.id,
            "employee_id": self._expense_employee().id,
            "product_id": self._expense_product().id,
            "date": self.issue_date and self.issue_date.date(),
            "currency_id": self.currency_id.id,
            "quantity": 1.0,
            # The gross is what the receipt states; hr.expense derives the unit
            # price and the tax from it, which is only correct for a
            # price-included tax — checked after creation.
            "total_amount_currency": tax_row.amount_total,
            "tax_ids": [fields.Command.set(tax.ids)],
            "vendor_id": self.partner_id.id or False,
        }

    def action_create_expenses(self):
        """One expense per VAT rate, because hr.expense carries one tax set."""
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
                    name=receipt.display_name,
                    count=len(receipt.expense_ids)))
            rows = receipt.tax_summary_ids
            if not rows:
                raise UserError(_(
                    "%s has no VAT recap, so there is no way to split it into "
                    "expenses. Post it as a vendor bill instead.",
                    receipt.display_name))
            created = receipt.env["hr.expense"]
            for row in rows:
                tax = receipt._checked_tax_for_rate(row.vat_rate)
                if not tax:
                    raise UserError(_(
                        "No purchase tax is mapped for %g%%. Without it the "
                        "expense would carry no VAT and the deduction would be "
                        "lost.", row.vat_rate))
                if not tax.price_include:
                    raise UserError(_(
                        "The purchase tax %(tax)s is not tax-included. An "
                        "expense derives its net amount from the total, so a "
                        "receipt's gross can only be split correctly by a "
                        "tax-included tax — otherwise %(gross).2f would be "
                        "treated as a net amount and the expense would total "
                        "more than the receipt. Set the tax's 'Included in "
                        "Price', or the company's price-include default.",
                        tax=tax.display_name, gross=row.amount_total))
                created |= receipt.env["hr.expense"].create(
                    receipt._prepare_expense_vals(row, tax))
            receipt._verify_expenses(created)
            receipt.message_post(body=_(
                "%s expense(s) created from this receipt.", len(created)))
            expenses |= created
        return expenses

    def _verify_expenses(self, expenses):
        """Refuse expenses whose total or VAT does not match the receipt."""
        self.ensure_one()
        # These are stored computes on records created a moment ago; read them
        # back from the database rather than trusting the in-memory values.
        expenses.flush_recordset()
        expenses.invalidate_recordset(
            ["total_amount_currency", "tax_amount_currency"])
        total = self._round(sum(expenses.mapped("total_amount_currency")))
        tax = self._round(sum(expenses.mapped("tax_amount_currency")))
        if not reconciles(total, self.amount_total, tolerance=0.02):
            raise UserError(_(
                "The expenses total %(got).2f but the receipt totals "
                "%(want).2f. Nothing was kept.",
                got=total, want=self.amount_total))
        if not reconciles(tax, self.amount_tax, tolerance=0.02):
            raise UserError(_(
                "The expenses carry %(got).2f of VAT but the receipt reports "
                "%(want).2f. Nothing was kept.",
                got=tax, want=self.amount_tax))

    def action_open_expenses(self):
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": self.env._("Expenses"),
            "res_model": "hr.expense",
            "view_mode": "list,form",
            "domain": [("cssk_receipt_id", "=", self.id)],
        }
