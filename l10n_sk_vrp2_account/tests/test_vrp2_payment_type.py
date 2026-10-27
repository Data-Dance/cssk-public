from contextlib import contextmanager
from unittest.mock import patch

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged

RESPONSE_OK = {
    "receiptNumber": "0001",
    "receiptId": "V-TEST-AAA",
    "id": 111,
    "okp": "aaaaaaaa-bbbbbbbb",
    "dataBase64": "QUJD",
    "createDate": 1750000000000,
}


@tagged("post_install", "-at_install")
class TestVrp2PaymentType(AccountTestInvoicingCommon):
    """The receipt registers how the invoice was paid, and a rounded cash
    payment is booked at the rounded amount."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "vrp2_login": "88812345678900001",
            "vrp2_token": "TOK",
            "vrp2_fiscalize_on_payment": True,
            "vrp2_round_5c": True,
        })
        cls.rounding_profit = cls.company_data["default_account_revenue"].copy(
            {"code": "648900"})
        cls.rounding_loss = cls.company_data["default_account_expense"].copy(
            {"code": "548900"})
        cls.cash_rounding = cls.env["account.cash.rounding"].create({
            "name": "VRP2 0.05",
            "rounding": 0.05,
            "strategy": "add_invoice_line",
            "profit_account_id": cls.rounding_profit.id,
            "loss_account_id": cls.rounding_loss.id,
            "rounding_method": "HALF-UP",
        })
        cls.company.vrp2_cash_rounding_id = cls.cash_rounding

    def _invoice(self, amount=100.03):
        return self.init_invoice(
            "out_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[amount], taxes=self.env["account.tax"], post=True,
        )

    @contextmanager
    def _mock_client(self):
        bodies = []
        Client = type(self.env["vrp2.client"])

        def fake(holder, body):
            bodies.append(body)
            return dict(RESPONSE_OK)

        with patch.object(Client, "_ensure_session", return_value="TOK"), \
                patch.object(Client, "_create_invoice", side_effect=fake):
            yield bodies

    def _register(self, invoices, **vals):
        return (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoices.ids)
            .create(vals)
        )

    # ---- the invoice buttons ask how it was paid -------------------------

    def test_the_button_asks_for_the_form_of_payment(self):
        invoice = self._invoice()
        action = invoice.action_vrp2_fiscalize()
        self.assertEqual(action["res_model"], "vrp2.fiscalize.wizard")
        wizard = self.env["vrp2.fiscalize.wizard"].with_context(
            action["context"]).new({})
        self.assertEqual(wizard.move_ids._origin, invoice)
        self.assertFalse(wizard.payment_type, "no form of payment is assumed")

    def test_a_card_payment_is_registered_as_card_and_not_rounded(self):
        invoice = self._invoice()
        wizard = self.env["vrp2.fiscalize.wizard"].create({
            "move_ids": [(6, 0, invoice.ids)], "payment_type": "CARD",
        })
        with self._mock_client() as bodies, \
                patch.object(type(invoice), "_vrp2_merged_pdf_action",
                             return_value=True):
            wizard.action_fiscalize()
        body = bodies[0]
        self.assertEqual(body["payments"][0]["type"], "CARD")
        self.assertEqual(body["payments"][0]["sum"], 100.03)
        self.assertEqual(body["roundingAmount"], 0.0)
        self.assertEqual(invoice.vrp2_receipt_ids.payment_method, "CARD")

    def test_the_mass_action_asks_too(self):
        invoices = self._invoice() | self._invoice()
        action = invoices.action_vrp2_mass_fiscalize()
        self.assertEqual(action["res_model"], "vrp2.fiscalize.wizard")
        self.assertEqual(action["context"]["default_move_ids"],
                         [(6, 0, invoices.ids)])

    # ---- § 3 ods. 4 zákona č. 18/1996 Z. z. --------------------------------

    def test_one_or_two_cents_round_up_to_five(self):
        round5 = self.env["account.move"]._vrp2_round_5c_amount
        self.assertEqual(round5(0.01), 0.05)
        self.assertEqual(round5(0.02), 0.05)
        self.assertEqual(round5(0.03), 0.05)
        self.assertEqual(round5(1.02), 1.00)
        self.assertEqual(round5(0.0), 0.0)

    # ---- Register Payment books the rounding --------------------------------

    def test_a_rounded_cash_payment_is_booked_at_the_rounded_amount(self):
        invoice = self._invoice(100.03)
        wizard = self._register(invoice, vrp2_payment_type="CASH")
        with self._mock_client() as bodies:
            payment = wizard._create_payments()
        self.assertEqual(payment.amount, 100.05)
        self.assertIn(invoice.payment_state, ("paid", "in_payment"))
        writeoff = payment.move_id.line_ids.filtered(
            lambda l: l.account_id == self.rounding_profit)
        self.assertEqual(writeoff.credit, 0.02)
        body = bodies[0]
        self.assertEqual(body["priceWithVat"], 100.03)
        self.assertEqual(body["payments"][0]["sum"], 100.05)
        self.assertEqual(body["roundingAmount"], 0.02)
        self.assertEqual(invoice.vrp2_receipt_ids.amount, 100.03)

    def test_rounding_down_goes_to_the_loss_account(self):
        invoice = self._invoice(100.02)
        wizard = self._register(invoice, vrp2_payment_type="CASH")
        with self._mock_client() as bodies:
            payment = wizard._create_payments()
        self.assertEqual(payment.amount, 100.00)
        writeoff = payment.move_id.line_ids.filtered(
            lambda l: l.account_id == self.rounding_loss)
        self.assertEqual(writeoff.debit, 0.02)
        self.assertEqual(bodies[0]["roundingAmount"], -0.02)

    def test_a_card_payment_is_not_rounded(self):
        invoice = self._invoice(100.03)
        wizard = self._register(invoice, vrp2_payment_type="CARD")
        with self._mock_client() as bodies:
            payment = wizard._create_payments()
        self.assertEqual(payment.amount, 100.03)
        self.assertEqual(bodies[0]["payments"][0]["type"], "CARD")
        self.assertEqual(bodies[0]["roundingAmount"], 0.0)

    def test_without_a_rounding_account_nothing_is_sent(self):
        self.company.vrp2_cash_rounding_id = False
        invoice = self._invoice(100.03)
        wizard = self._register(invoice, vrp2_payment_type="CASH")
        with self._mock_client() as bodies:
            with self.assertRaisesRegex(UserError, "cash rounding"):
                wizard._create_payments()
        self.assertFalse(bodies)

    def test_a_partial_cash_payment_off_the_grid_is_refused(self):
        invoice = self._invoice(100.03)
        wizard = self._register(invoice, vrp2_payment_type="CASH", amount=50.03)
        with self._mock_client() as bodies:
            with self.assertRaisesRegex(UserError, "0.05"):
                wizard._create_payments()
        self.assertFalse(bodies)

    def test_a_partial_cash_payment_on_the_grid_is_fine(self):
        invoice = self._invoice(100.03)
        wizard = self._register(invoice, vrp2_payment_type="CASH", amount=50.05)
        with self._mock_client() as bodies:
            payment = wizard._create_payments()
        self.assertEqual(payment.amount, 50.05)
        self.assertEqual(bodies[0]["roundingAmount"], 0.0)

    def test_several_invoices_off_the_grid_are_refused(self):
        invoices = self._invoice(100.03) | self._invoice(100.00)
        wizard = self._register(invoices, vrp2_payment_type="CASH",
                                group_payment=False)
        with self._mock_client() as bodies:
            with self.assertRaisesRegex(UserError, "on its own"):
                wizard._create_payments()
        self.assertFalse(bodies)
