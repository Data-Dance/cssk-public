# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import base64
from unittest.mock import patch

from odoo import fields
from odoo.exceptions import AccessError
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from odoo.addons.l10n_cssk_receipt_capture.tests.qr_images import (
    FISCAL_ID, LOYALTY_LINK, receipt_image,
)


@tagged("post_install", "-at_install")
class TestExpenseVisibility(AccountTestInvoicingCommon):
    """What an employee sees after uploading or scanning a receipt."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.cssk_receipt_expense_account_id = cls.company_data[
            "default_account_expense"]
        cls.product = cls.env["product.product"].create({
            "name": "Receipt expense", "can_be_expensed": True, "type": "service",
        })
        cls.company.cssk_receipt_expense_product_id = cls.product
        for rate in (23.0, 19.0, 5.0):
            cls.env["account.tax"].create({
                "name": "DPH %g%% incl (test)" % rate, "amount_type": "percent",
                "amount": rate, "type_tax_use": "purchase",
                "price_include_override": "tax_included",
                "company_id": cls.company.id,
            })
        # The accountant running most of these needs an employee record too.
        cls.env["hr.employee"].sudo().create({
            "name": "Accountant", "user_id": cls.env.user.id,
            "company_id": cls.company.id,
        })
        # An employee with NO accounting rights: the person who actually
        # uploads receipts, and who could not, before.
        cls.employee_user = cls.env["res.users"].create({
            "name": "Plain Employee", "login": "plain.employee@example.com",
            "company_id": cls.company.id, "company_ids": [(6, 0, [cls.company.id])],
            "groups_id": [(6, 0, [cls.env.ref("base.group_user").id])],
        })
        cls.employee = cls.env["hr.employee"].sudo().create({
            "name": "Plain Employee", "user_id": cls.employee_user.id,
            "company_id": cls.company.id,
        })

    def _upload(self, data, user=None):
        Expense = self.env["hr.expense"].with_user(user or self.env.user)
        attachment = self.env["ir.attachment"].with_user(user or self.env.user).create({
            "name": "receipt.jpg", "mimetype": "image/jpeg",
            "datas": base64.b64encode(data), "res_model": "hr.expense", "res_id": 0,
        })
        result = Expense.create_expense_from_attachments(
            attachment_ids=attachment.ids)
        # 18.0 returns the act_window that opens the new expenses; 19.0 returns
        # their ids. The module's own helper reads both, and this exercises it.
        return Expense._cssk_uploaded_expenses(result, attachment.ids)

    def _ekasa_ready(self):
        if "cssk.receipt.provider.sk_ekasa" not in self.env:
            self.skipTest("l10n_sk_ekasa_receipt is not installed")
        from odoo.addons.l10n_sk_ekasa_receipt.tests.common import load_fixture

        self.company.write({"l10n_sk_ekasa_enabled": True,
                            "l10n_sk_ekasa_ip_notified": True})
        payload = load_fixture("receipt_online_fuel.json")

        def _fetch(self_model, company, request):
            return payload, {"outcome": "found", "http_status": 200,
                             "return_value": 0}
        return patch.object(type(self.env["cssk.receipt.provider.sk_ekasa"]),
                            "_fetch", _fetch)

    # ------------------------------------------------------------------
    def test_an_employee_without_accounting_rights_can_upload(self):
        """The upload ran as the employee and cssk.receipt is an accounting
        record: every upload by an ordinary employee raised AccessError."""
        expenses = self._upload(receipt_image([]), user=self.employee_user)
        self.assertEqual(len(expenses), 1)
        expense = expenses.with_user(self.employee_user)
        # The employee reads the outcome through the expense, not the receipt.
        self.assertEqual(expense.cssk_receipt_state, "error")
        self.assertTrue(expense.cssk_receipt_reason)

    def test_the_uploader_is_told_how_it_went(self):
        sent = []
        users_cls = type(self.env["res.users"])

        def _bus_send(self_user, notification_type, message, **kw):
            sent.append((notification_type, message))
        with patch.object(users_cls, "_bus_send", _bus_send):
            self._upload(receipt_image([]))
        self.assertEqual(sent[0][0], "simple_notification")
        self.assertIn("could not be read", sent[0][1]["message"])
        self.assertTrue(sent[0][1]["sticky"])

    def test_a_photographed_receipt_fills_its_expense(self):
        """Photo → QR read off it (under a loyalty link) → eKasa → expense."""
        with self._ekasa_ready():
            expenses = self._upload(receipt_image([LOYALTY_LINK, FISCAL_ID]))
        expense = expenses
        self.assertEqual(expense.cssk_receipt_state, "captured",
                         expense.cssk_receipt_reason)
        self.assertAlmostEqual(expense.total_amount_currency, 57.85, places=2)
        self.assertAlmostEqual(expense.tax_amount_currency, 10.82, places=2)
        self.assertEqual(expense.date, fields.Date.to_date("2026-03-20"))
        self.assertTrue(expense.message_ids.filtered(
            lambda m: "Receipt read" in (m.body or "")))

    def test_scanning_from_the_expenses_app_lands_on_an_expense(self):
        Expense = self.env["hr.expense"].with_user(self.employee_user)
        refusal = Expense.action_capture_from_scan(LOYALTY_LINK)
        self.assertTrue(refusal["retry"])
        with self._ekasa_ready():
            result = Expense.action_capture_from_scan(FISCAL_ID)
        self.assertFalse(result["retry"])
        expense = self.env["hr.expense"].browse(result["action"]["res_id"])
        self.assertEqual(expense.employee_id, self.employee)
        self.assertAlmostEqual(expense.total_amount_currency, 57.85, places=2)

    def test_above_the_limit_it_is_one_expense_with_the_vat_as_cost(self):
        """401.25 EUR: booked in full, nothing deducted, nothing to split."""
        receipt = self.env["cssk.receipt"].create({
            "company_id": self.company.id,
            "currency_id": self.company.currency_id.id,
            "seller_name": "Vzorový obchod", "seller_vat": "SK2099000002",
            "issue_date": "2026-10-02 13:51:40", "amount_total": 401.25,
            "state": "captured",
            "line_ids": [fields.Command.create({
                "name": "Tovar", "quantity": 1, "vat_rate": 23.0,
                "amount_total": 401.25})],
            "tax_summary_ids": [fields.Command.create({
                "vat_rate": 23.0, "amount_untaxed": 326.22, "amount_tax": 75.03})],
        })
        self.assertFalse(receipt.vat_deductible)
        expenses = receipt.with_user(self.env.user).action_create_expenses()
        self.assertEqual(len(expenses), 1)
        self.assertAlmostEqual(expenses.total_amount_currency, 401.25, places=2)
        self.assertAlmostEqual(expenses.tax_amount_currency, 0.0, places=2)
        self.assertFalse(expenses.tax_ids)

    def test_a_receipt_cannot_be_claimed_by_two_employees(self):
        """A colleague's expense is invisible to the employee, so the check that
        it is already claimed must not run with the employee's own rights."""
        with self._ekasa_ready():
            first = self.env["hr.expense"].action_capture_from_scan(FISCAL_ID)
            second = self.env["hr.expense"].with_user(
                self.employee_user).action_capture_from_scan(FISCAL_ID)
        self.assertFalse(first["retry"])
        self.assertTrue(second["retry"])
        self.assertIn("already been claimed", second["message"])
        receipt = self.env["cssk.receipt"].search([("qr_raw", "=", FISCAL_ID)])
        self.assertEqual(
            len(self.env["hr.expense"].search([("cssk_receipt_id", "=", receipt.id)])), 1)

    # ------------------------------------------------------------------
    # the employee sees their own receipts, and only those
    # ------------------------------------------------------------------
    def _other_employee(self):
        user = self.env["res.users"].create({
            "name": "Colleague", "login": "colleague@example.com",
            "company_id": self.company.id, "company_ids": [(6, 0, [self.company.id])],
            "groups_id": [(6, 0, [self.env.ref("base.group_user").id])],
        })
        self.env["hr.employee"].sudo().create({
            "name": "Colleague", "user_id": user.id, "company_id": self.company.id})
        return user

    def test_the_employee_opens_the_receipt_behind_their_expense(self):
        """Uploaded by the employee, read from eKasa: the receipt, its items
        and its VAT recap are theirs to read — the whole form, not just the
        state mirrored onto the expense."""
        with self._ekasa_ready():
            expense = self._upload(receipt_image([FISCAL_ID]), user=self.employee_user)
        receipt = expense.with_user(self.employee_user).cssk_receipt_id
        self.assertTrue(receipt)
        form = receipt.get_views([(False, "form")])["models"]["cssk.receipt"]["fields"]
        values = receipt.read(list(form))[0]
        self.assertAlmostEqual(values["amount_total"], 57.85, places=2)
        self.assertTrue(receipt.line_ids.read(["name", "amount_total"]))
        self.assertTrue(receipt.tax_summary_ids.read(["vat_rate", "amount_tax"]))
        self.assertTrue(receipt.attempt_ids.read(["outcome"]))
        self.assertIn(receipt, self.env["cssk.receipt"].with_user(
            self.employee_user).search([]))

    def test_a_receipt_captured_for_the_employee_is_theirs_too(self):
        """An accountant can capture a receipt and file the expense for an
        employee; the employee did not create it but owns the expense."""
        with self._ekasa_ready():
            expense = self._upload(receipt_image([FISCAL_ID]))
        expense.employee_id = self.employee
        mine = self.env["cssk.receipt"].with_user(self.employee_user).search([])
        self.assertEqual(mine, expense.cssk_receipt_id)

    def test_an_employee_does_not_see_a_colleagues_receipt(self):
        with self._ekasa_ready():
            self._upload(receipt_image([FISCAL_ID]), user=self.employee_user)
        colleague = self._other_employee()
        self.assertFalse(self.env["cssk.receipt"].with_user(colleague).search([]))
        self.assertFalse(self.env["cssk.receipt.line"].with_user(colleague).search([]))

    def test_an_employee_reads_but_does_not_change_a_receipt(self):
        with self._ekasa_ready():
            expense = self._upload(receipt_image([FISCAL_ID]), user=self.employee_user)
        receipt = expense.cssk_receipt_id.with_user(self.employee_user)
        with self.assertRaises(AccessError):
            receipt.write({"seller_name": "Changed"})
