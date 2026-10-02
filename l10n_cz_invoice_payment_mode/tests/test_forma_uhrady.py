# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestFormaUhrady(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.mode = cls.env["account.payment.mode"].create({
            "name": "Převodem",
            "bank_account_link": "variable",
            "payment_method_id": cls.env.ref(
                "account.account_payment_method_manual_in").id,
        })

    def _html(self, mode):
        invoice = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner_a.id,
            "invoice_date": "2026-09-01", "payment_mode_id": mode.id,
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": 100.0})],
        })
        invoice.action_post()
        return self.env["ir.actions.report"]._render_qweb_html(
            "account.account_invoices", invoice.ids)[0].decode()

    def test_the_payment_mode_is_printed_as_forma_uhrady(self):
        html = self._html(self.mode)
        self.assertIn("Forma úhrady", html)
        self.assertIn("Převodem", html)

    def test_nothing_is_printed_without_a_mode(self):
        self.assertNotIn("Forma úhrady", self._html(self.mode.browse()))
