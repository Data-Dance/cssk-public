# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import ValidationError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPayOnPost(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.cash = cls.company_data["default_journal_cash"]
        cls.mode = cls.env["account.payment.mode"].create({
            "name": "Hotovost",
            "payment_method_id": cls.env.ref(
                "account.account_payment_method_manual_in").id,
            "bank_account_link": "fixed",
            "fixed_journal_id": cls.cash.id,
            "pay_on_post": True,
        })

    def _invoice(self, mode):
        return self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner_a.id,
            "invoice_date": "2026-09-01", "payment_mode_id": mode.id,
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": 100.0,
                "tax_ids": [Command.clear()]})],
        })

    def test_the_invoice_is_paid_when_posted(self):
        invoice = self._invoice(self.mode)
        invoice.action_post()
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))
        payment = invoice.matched_payment_ids
        self.assertEqual(payment.journal_id, self.cash)
        self.assertEqual(str(payment.date), "2026-09-01")

    def test_a_mode_without_the_flag_leaves_it_open(self):
        self.mode.pay_on_post = False
        invoice = self._invoice(self.mode)
        invoice.action_post()
        self.assertEqual(invoice.payment_state, "not_paid")

    def test_the_flag_needs_a_fixed_journal(self):
        with self.assertRaises(ValidationError):
            self.env["account.payment.mode"].create({
                "name": "Karta",
                "payment_method_id": self.env.ref(
                    "account.account_payment_method_manual_in").id,
                "bank_account_link": "variable",
                "pay_on_post": True,
            })
