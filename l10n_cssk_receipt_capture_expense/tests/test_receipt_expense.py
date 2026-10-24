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
                # Either kind works (special_mode="total_included"); the
                # tax-excluded case has its own test.
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

    def test_three_rates_are_one_expense(self):
        """One receipt, one expense: the rates live in its VAT, not in copies.

        It used to become one expense per rate, because hr.expense applies all
        its taxes to one base. The 0.00 row at 19 % is not a rate at all.
        """
        receipt = self._restaurant_receipt()
        expense = receipt.action_create_expenses()
        self.assertEqual(len(expense), 1)
        self.assertAlmostEqual(expense.total_amount_currency, 181.90, places=2)
        self.assertAlmostEqual(expense.tax_amount_currency, 15.82, places=2)
        self.assertAlmostEqual(expense.untaxed_amount_currency, 166.08, places=2)
        self.assertEqual(expense.tax_ids, self.taxes[5.0] | self.taxes[23.0])
        self.assertEqual(expense.name, "Vzorová reštaurácia, s. r. o.")

    # ------------------------------------------------------------------
    # posting: a base and a VAT line per rate
    # ------------------------------------------------------------------
    def _approved(self, expense, payment_mode):
        self.env.user.group_ids |= self.env.ref(
            "hr_expense.group_hr_expense_manager")
        expense.payment_mode = payment_mode
        expense.action_submit()
        expense.action_approve()
        return expense

    def _vat_by_rate(self, move):
        lines = move.line_ids
        return {
            tax.amount: (
                round(sum(lines.filtered(lambda l: tax in l.tax_ids).mapped("balance")), 2),
                round(sum(lines.filtered(lambda l: l.tax_line_id == tax).mapped("balance")), 2),
            )
            for tax in (self.taxes[5.0], self.taxes[23.0])
        }

    def test_an_employee_paid_expense_posts_each_rate_on_its_own_base(self):
        expense = self._approved(
            self._restaurant_receipt().action_create_expenses(), "own_account")
        action = expense.action_post()
        self.env["hr.expense.post.wizard"].with_context(action["context"]).browse(
            action["res_id"]).action_post_entry()
        move = expense.account_move_id
        self.assertEqual(move.state, "posted")
        self.assertAlmostEqual(move.amount_total, 181.90, places=2)
        self.assertEqual(self._vat_by_rate(move),
                         {5.0: (124.29, 6.21), 23.0: (41.79, 9.61)})

    def test_a_company_paid_expense_posts_each_rate_on_its_own_base(self):
        expense = self._approved(
            self._restaurant_receipt().action_create_expenses(), "company_account")
        expense.action_post()
        move = expense.account_move_id
        self.assertEqual(move.state, "posted")
        self.assertEqual(self._vat_by_rate(move),
                         {5.0: (124.29, 6.21), 23.0: (41.79, 9.61)})
        self.assertAlmostEqual(sum(move.line_ids.mapped("balance")), 0.0, places=2)

    def test_an_expense_edited_away_from_its_receipt_does_not_post(self):
        """Its VAT is posted from the receipt; an edited amount cannot be."""
        expense = self._restaurant_receipt().action_create_expenses()
        expense.total_amount_currency = 150.0
        self._approved(expense, "company_account")
        with self.assertRaisesRegex(UserError, "no longer matches its receipt"):
            expense.action_post()

    def test_a_tax_excluded_tax_splits_the_gross_too(self):
        """hr.expense reads its amount as tax-included whatever the tax says.

        This used to be refused, on the belief that a tax-excluded tax would
        treat the gross as a net. It does not (special_mode="total_included"),
        and the refusal blocked every receipt on a stock chart — whose taxes
        are tax-excluded, as the vendor-bill path requires.
        """
        self.taxes[23.0].price_include_override = "tax_excluded"
        expenses = self._fuel_receipt().action_create_expenses()
        self.assertAlmostEqual(expenses.total_amount_currency, 57.85, places=2)
        self.assertAlmostEqual(expenses.tax_amount_currency, 10.82, places=2)
        self.assertAlmostEqual(expenses.untaxed_amount_currency, 47.03, places=2)

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
        # Nothing here can read these photographs. That used to leave the
        # receipts silently "new" behind an "Untitled Expense, 0.00"; now each
        # is an error carrying the reason, and the reason is on the expense.
        self.assertEqual(
            set(expenses.mapped("cssk_receipt_id.state")), {"error"})
        for expense in expenses:
            self.assertTrue(expense.cssk_receipt_reason)
            self.assertEqual(expense.cssk_receipt_state, "error")
            self.assertTrue(expense.message_ids.filtered(
                lambda m: "could not be read" in (m.body or "")))

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

    def test_multi_rate_capture_fills_the_one_expense(self):
        """Three rates on the receipt, still one expense: the uploaded one.

        This first declined and left the expense at 0.00, then split it into
        one expense per rate.
        """
        self.company.cssk_receipt_capture_on_expense_upload = False
        attachment = self._attachment()
        expense_ids = self.env["hr.expense"].create_expense_from_attachments(
            attachment_ids=attachment.ids)
        expense = self.env["hr.expense"].browse(expense_ids)
        receipt = self._restaurant_receipt()
        expense.cssk_receipt_id = receipt
        self.assertTrue(expense._cssk_apply_captured_receipt(receipt))
        self.assertEqual(
            self.env["hr.expense"].search([("cssk_receipt_id", "=", receipt.id)]),
            expense)
        self.assertAlmostEqual(expense.total_amount_currency, 181.90, places=2)
        self.assertAlmostEqual(expense.tax_amount_currency, 15.82, places=2)


    # -- one purchase, booked once (cssk-public#10) ---------------------
    # A stock chart's purchase taxes are tax-excluded, which both paths take
    # (a vendor receipt refuses the tax-included kind this class sets up).
    def _bookable_fuel_receipt(self):
        self.taxes[23.0].price_include_override = "tax_excluded"
        return self._fuel_receipt()

    def test_a_receipt_claimed_as_an_expense_gets_no_vendor_receipt(self):
        receipt = self._bookable_fuel_receipt()
        receipt.action_create_partner()
        receipt.state = "captured"
        receipt.action_create_expenses()
        self.assertEqual(receipt.state, "captured", "the expense moves on, not the receipt")
        with self.assertRaisesRegex(UserError, "already claimed as 1 expense"):
            receipt.action_create_bill()
        self.assertFalse(receipt.move_id)

    def test_a_receipt_booked_as_a_vendor_receipt_gets_no_expense(self):
        receipt = self._bookable_fuel_receipt()
        receipt.action_create_partner()
        receipt.state = "captured"
        receipt.action_create_bill()
        with self.assertRaisesRegex(UserError, "can become expenses"):
            receipt.action_create_expenses()
        self.assertFalse(receipt.expense_ids)
