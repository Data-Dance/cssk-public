# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64

from odoo import fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestReceiptExpense(AccountTestInvoicingCommon):
    """The expense sink, on the two real receipts' figures."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.cssk_receipt_expense_account_id = cls.company_data[
            "default_account_expense"]
        cls.env.user.company_ids |= cls.company
        cls.env.user.company_id = cls.company
        # sudo: hr's own create() reads res.partner.employee_ids, which is
        # restricted to HR officers. Whoever captures receipts need not be one —
        # reading their OWN employee record is unrestricted, which is all the
        # module does.
        cls.employee = cls.env["hr.employee"].sudo().create({
            "name": "Receipt Tester",
            "user_id": cls.env.user.id,
            "company_id": cls.company.id,
        })
        cls.product = cls.env["product.product"].create({
            "name": "Receipt expense",
            "default_code": "EXP_GEN_TEST",
            "can_be_expensed": True,
            "type": "service",
        })
        cls.company.cssk_receipt_expense_product_id = cls.product
        cls.taxes = {}
        for rate in (23.0, 19.0, 5.0):
            cls.taxes[rate] = cls.env["account.tax"].create({
                "name": "DPH %g%% incl (test)" % rate,
                "amount_type": "percent",
                "amount": rate,
                "type_tax_use": "purchase",
                # hr.expense derives the net from the total, so only a
                # tax-included tax lands on the receipt's own base.
                "price_include_override": "tax_included",
                "company_id": cls.company.id,
            })

    def _fuel_receipt(self):
        return self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "seller_name": "Vzorová čerpacia stanica, a. s.",
            "seller_vat": "SK7199000006",
            "issue_date": "2026-03-20 09:36:36",
            "amount_total": 57.85,
            "state": "captured",
            "line_ids": [fields.Command.create({
                "name": "Benzín 95", "quantity": 31.17, "uom_label": "l",
                "vat_rate": 23.0, "amount_total": 57.85})],
            "tax_summary_ids": [fields.Command.create({
                "vat_rate": 23.0, "amount_untaxed": 47.03, "amount_tax": 10.82})],
        })

    def _restaurant_receipt(self):
        return self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "seller_name": "Vzorová reštaurácia, s. r. o.",
            "issue_date": "2026-03-14 19:59:02",
            "amount_total": 181.90,
            "state": "captured",
            "tax_summary_ids": [
                fields.Command.create({"vat_rate": 5.0, "amount_untaxed": 124.29,
                                       "amount_tax": 6.21}),
                fields.Command.create({"vat_rate": 23.0, "amount_untaxed": 41.79,
                                       "amount_tax": 9.61}),
                fields.Command.create({"vat_rate": 19.0, "amount_untaxed": 0.0,
                                       "amount_tax": 0.0}),
            ],
        })

    # ------------------------------------------------------------------
    def test_single_rate_receipt_becomes_one_expense(self):
        receipt = self._fuel_receipt()
        expenses = receipt.action_create_expenses()
        self.assertEqual(len(expenses), 1)
        self.assertAlmostEqual(expenses.total_amount_currency, 57.85, places=2)
        self.assertAlmostEqual(expenses.tax_amount_currency, 10.82, places=2)
        self.assertAlmostEqual(expenses.untaxed_amount_currency, 47.03, places=2)
        self.assertEqual(expenses.quantity, 1.0)
        self.assertEqual(expenses.cssk_receipt_id, receipt)
        self.assertEqual(receipt.expense_count, 1)

    def test_three_rates_become_three_expenses(self):
        """One per rate, because hr.expense carries a single tax set."""
        receipt = self._restaurant_receipt()
        expenses = receipt.action_create_expenses()
        self.assertEqual(len(expenses), 3)
        self.assertAlmostEqual(
            sum(expenses.mapped("total_amount_currency")), 181.90, places=2)
        self.assertAlmostEqual(
            sum(expenses.mapped("tax_amount_currency")), 15.82, places=2)
        self.assertEqual(
            sorted(round(e.total_amount_currency, 2) for e in expenses),
            [0.0, 51.40, 130.50])

    def test_refused_when_the_tax_is_not_price_included(self):
        """Otherwise the gross is treated as a net and the expense overstates."""
        self.taxes[23.0].price_include_override = "tax_excluded"
        receipt = self._fuel_receipt()
        with self.assertRaisesRegex(UserError, "not tax-included"):
            receipt.action_create_expenses()
        self.assertFalse(receipt.expense_ids)

    def test_refused_when_a_rate_has_no_tax(self):
        self.taxes[23.0].unlink()
        receipt = self._fuel_receipt()
        with self.assertRaisesRegex(UserError, "No purchase tax is mapped"):
            receipt.action_create_expenses()

    def test_refused_for_an_unreconciled_receipt(self):
        receipt = self._fuel_receipt()
        receipt.state = "review"
        with self.assertRaisesRegex(UserError, "captured, reconciled"):
            receipt.action_create_expenses()

    def test_refused_without_a_vat_recap(self):
        receipt = self._fuel_receipt()
        receipt.tax_summary_ids.unlink()
        with self.assertRaisesRegex(UserError, "no VAT recap"):
            receipt.action_create_expenses()

    def test_not_created_twice(self):
        receipt = self._fuel_receipt()
        receipt.action_create_expenses()
        with self.assertRaisesRegex(UserError, "already has"):
            receipt.action_create_expenses()

    # ------------------------------------------------------------------
    # the Expenses-app upload path
    # ------------------------------------------------------------------
    def _attachment(self, name="receipt.jpg"):
        return self.env["ir.attachment"].create({
            "name": name,
            "datas": base64.b64encode(b"not really a jpeg"),
            "res_model": "hr.expense",
            "res_id": 0,
        })

    def test_upload_creates_a_captured_receipt_per_attachment(self):
        attachments = self._attachment("a.jpg") | self._attachment("b.jpg")
        expense_ids = self.env["hr.expense"].create_expense_from_attachments(
            attachment_ids=attachments.ids)
        expenses = self.env["hr.expense"].browse(expense_ids)
        self.assertEqual(len(expenses), 2)
        self.assertTrue(all(e.cssk_receipt_id for e in expenses))
        self.assertEqual(len(expenses.mapped("cssk_receipt_id")), 2)
        # Nothing could read a photograph here, so they wait rather than lying.
        self.assertEqual(
            set(expenses.mapped("cssk_receipt_id.state")), {"new"})

    def test_upload_capture_can_be_switched_off(self):
        self.company.cssk_receipt_capture_on_expense_upload = False
        attachment = self._attachment()
        expense_ids = self.env["hr.expense"].create_expense_from_attachments(
            attachment_ids=attachment.ids)
        expense = self.env["hr.expense"].browse(expense_ids)
        self.assertFalse(expense.cssk_receipt_id)

    def test_single_rate_capture_fills_the_expense_in_place(self):
        attachment = self._attachment()
        expense_ids = self.env["hr.expense"].create_expense_from_attachments(
            attachment_ids=attachment.ids)
        expense = self.env["hr.expense"].browse(expense_ids)
        receipt = self._fuel_receipt()
        self.assertTrue(expense._cssk_apply_captured_receipt(receipt))
        self.assertAlmostEqual(expense.total_amount_currency, 57.85, places=2)
        self.assertAlmostEqual(expense.tax_amount_currency, 10.82, places=2)

    def test_multi_rate_capture_is_left_to_the_split(self):
        """Three rates cannot be one expense, so the in-place fill declines."""
        attachment = self._attachment()
        expense_ids = self.env["hr.expense"].create_expense_from_attachments(
            attachment_ids=attachment.ids)
        expense = self.env["hr.expense"].browse(expense_ids)
        receipt = self._restaurant_receipt()
        self.assertFalse(expense._cssk_apply_captured_receipt(receipt))
        self.assertAlmostEqual(expense.total_amount_currency, 0.0, places=2)
