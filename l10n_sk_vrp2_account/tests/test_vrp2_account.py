import json
from contextlib import contextmanager
from unittest.mock import patch

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged

# A real "Úhrada faktúry" style VRP2 response (trimmed).
RESPONSE_OK = {
    "receiptNumber": "0001",
    "receiptId": "V-TEST-AAA",
    "id": 111,
    "okp": "aaaaaaaa-bbbbbbbb",
    "dataBase64": "QUJD",
    "createDate": 1750000000000,
}


@tagged("post_install", "-at_install")
class TestVrp2Account(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vrp2_login = "88812345678900001"
        cls.company.vrp2_token = "TOK"
        cls.company.vrp2_fiscalize_on_payment = True

    def _invoice(self, partner, move_type="out_invoice"):
        return self.init_invoice(
            move_type, partner=partner, invoice_date="2026-06-10",
            amounts=[100.0], taxes=self.env["account.tax"], post=True,
        )

    def _wizard(self, invoices, **vals):
        return (
            self.env["account.payment.register"]
            .with_context(active_model="account.move", active_ids=invoices.ids)
            .create(vals)
        )

    @contextmanager
    def _mock_client(self, create_invoice):
        Client = type(self.env["vrp2.client"])
        with patch.object(Client, "_ensure_session", return_value="TOK"), \
             patch.object(Client, "_create_invoice",
                          side_effect=create_invoice) as mock_ci:
            yield mock_ci

    # ---- pure helper -----------------------------------------------------

    def test_round_5c_amount(self):
        round5 = self.env["account.move"]._vrp2_round_5c_amount
        self.assertEqual(round5(1.11), 1.10)
        self.assertEqual(round5(1.13), 1.15)
        self.assertEqual(round5(1.125), 1.15)  # half up, no float drift
        self.assertEqual(round5(10.00), 10.00)

    # ---- refunds must not be fiscalized as positive receipts --------------

    def test_refund_fiscalization_blocked(self):
        refund = self._invoice(self.partner_a, move_type="out_refund")
        with patch.object(
            type(self.env["vrp2.client"]), "_request_raw",
            side_effect=AssertionError("refund must be blocked pre-network"),
        ):
            with self.assertRaisesRegex(UserError, "[Ss]torno"):
                refund._vrp2_fiscalize()
        self.assertFalse(refund.vrp2_receipt_ids)

    def test_mass_fiscalize_refuses_refund_only_selection(self):
        refund = self._invoice(self.partner_a, move_type="out_refund")
        with self.assertRaisesRegex(UserError, "storno"):
            refund.action_vrp2_mass_fiscalize()

    def test_mass_fiscalize_keeps_earlier_receipt_on_failure(self):
        """A mid-batch VRP2 failure keeps the receipts already issued and
        records the failed one instead of rolling the whole batch back."""
        inv1 = self._invoice(self.partner_a)
        inv2 = self._invoice(self.partner_b)
        Client = type(self.env["vrp2.client"])

        calls = []

        def fake_ci(holder, body):
            calls.append(body["invoiceNumber"])
            if len(calls) == 1:
                return dict(RESPONSE_OK)
            raise UserError("VRP2 error: boom (Kód chyby: 42)")

        with patch.object(Client, "_ensure_session", return_value="TOK"), \
             patch.object(Client, "_create_invoice", side_effect=fake_ci):
            receipts = (inv1 | inv2)._vrp2_fiscalize("CASH")

        # No exception escaped; exactly the first invoice was fiscalized.
        self.assertEqual(len(receipts), 1)
        self.assertEqual(receipts.state, "confirmed")
        self.assertEqual(len(calls), 2)
        first = (inv1 | inv2).filtered(lambda m: m.name == calls[0])
        second = (inv1 | inv2) - first

        ok_receipt = first.vrp2_receipt_ids
        self.assertEqual(len(ok_receipt), 1)
        self.assertEqual(ok_receipt.state, "confirmed")

        # The failed invoice left an error-state audit record + chatter note,
        # and its rolled-back draft receipt did not survive the savepoint.
        err_receipt = second.vrp2_receipt_ids
        self.assertEqual(len(err_receipt), 1)
        self.assertEqual(err_receipt.state, "error")
        self.assertIn("boom", err_receipt.error_message)
        self.assertTrue(
            any("VRP2" in (msg.body or "") for msg in second.message_ids)
        )

    def test_mass_fiscalize_first_failure_still_raises(self):
        """With nothing issued yet, the batch fails fast and rolls back."""
        inv1 = self._invoice(self.partner_a)
        Client = type(self.env["vrp2.client"])
        with patch.object(Client, "_ensure_session", return_value="TOK"), \
             patch.object(Client, "_create_invoice",
                          side_effect=UserError("VRP2 error: rejected")):
            with self.assertRaisesRegex(UserError, "rejected"):
                inv1._vrp2_fiscalize("CASH")
        self.assertFalse(inv1.vrp2_receipt_ids)

    # ---- payment register: validate ALL before ANY network call -----------

    def test_register_validates_before_any_network_call(self):
        inv1 = self._invoice(self.partner_a)
        inv2 = self._invoice(self.partner_b)
        inv3 = self._invoice(self.partner_b)
        wizard = self._wizard(inv1 | inv2 | inv3, group_payment=True)
        self.assertTrue(wizard.vrp2_fiscalize)
        with self._mock_client(
            AssertionError("network fired before validation finished")
        ) as mock_ci:
            with self.assertRaisesRegex(UserError, "one invoice per payment"):
                wizard._create_payments()
        mock_ci.assert_not_called()

    # ---- payment register: an FS-issued receipt survives later failures ---

    def test_later_failure_keeps_earlier_receipt(self):
        inv1 = self._invoice(self.partner_a)
        inv2 = self._invoice(self.partner_b)
        wizard = self._wizard(inv1 | inv2, group_payment=False)
        self.assertTrue(wizard.vrp2_fiscalize)

        calls = []

        def fake_create_invoice(holder, body):
            calls.append(body["invoiceNumber"])
            if len(calls) == 1:
                return dict(RESPONSE_OK)
            raise UserError("VRP2 error: boom (Kód chyby: 42)")

        with self._mock_client(fake_create_invoice):
            payments = wizard._create_payments()

        # Both payments exist, no exception escaped the wizard.
        self.assertEqual(len(payments), 2)
        self.assertEqual(len(calls), 2)
        first = (inv1 | inv2).filtered(lambda m: m.name == calls[0])
        second = (inv1 | inv2) - first

        # The receipt fiscalized at the FS kept its local record.
        ok_receipt = first.vrp2_receipt_ids
        self.assertEqual(len(ok_receipt), 1)
        self.assertEqual(ok_receipt.state, "confirmed")
        self.assertEqual(ok_receipt.name, "0001")
        self.assertEqual(ok_receipt.vrp2_receipt_uuid, "V-TEST-AAA")

        # The failed one left an error-state audit record + chatter note.
        err_receipt = second.vrp2_receipt_ids
        self.assertEqual(len(err_receipt), 1)
        self.assertEqual(err_receipt.state, "error")
        self.assertIn("boom", err_receipt.error_message)
        self.assertTrue(
            any(
                "VRP2" in (msg.body or "") and "boom" in (msg.body or "")
                for msg in second.message_ids
            )
        )

    def test_first_failure_still_fails_fast(self):
        """With nothing fiscalized yet there is nothing to protect: the
        wizard fails fast and everything rolls back together."""
        inv1 = self._invoice(self.partner_a)
        wizard = self._wizard(inv1, group_payment=False)
        with self._mock_client(UserError("VRP2 error: rejected")):
            with self.assertRaisesRegex(UserError, "rejected"):
                wizard._create_payments()

    # ---- storno: a valid receipt with a CORRECTION line -------------------

    def test_storno_dto_and_flow(self):
        """Storno posts a /create/valid body with one negative CORRECTION line
        referencing the original receiptId (shape from the 2026-07-15 capture).
        """
        self.company.vat = "SK2020000000"
        move = self._invoice(self.partner_a)
        Client = type(self.env["vrp2.client"])

        # Fiscalize the invoice first so there is a confirmed receipt to storno.
        with patch.object(Client, "_ensure_session", return_value="TOK"), \
             patch.object(Client, "_create_invoice", return_value=dict(RESPONSE_OK)):
            receipt = move._vrp2_fiscalize("CASH")
        self.assertEqual(receipt.state, "confirmed")
        self.assertEqual(receipt.vrp2_receipt_uuid, "V-TEST-AAA")
        invoice_number = json.loads(receipt.request_json)["invoiceNumber"]

        storno_resp = {
            "receiptNumber": "0002", "receiptId": "V-TEST-STORNO", "id": 222,
            "okp": "cccccccc-dddddddd", "createDate": 1750000001000,
        }
        captured = {}

        def fake_valid(holder, body):
            captured["body"] = body
            return dict(storno_resp)

        # vatPayer/version come from the register's dashboard, not from the
        # company's VAT number or the clock (2026-10-06 capture).
        dashboard = {"cashRegister": {
            "dkp": "99920201234560002", "version": 1662177617338,
            "organization": {"name": "X", "vatPayer": True},
        }}
        with patch.object(Client, "_ensure_session", return_value="TOK"), \
             patch.object(Client, "_get_dashboard", return_value=dashboard), \
             patch.object(Client, "_create_receipt_valid", side_effect=fake_valid):
            storno = receipt._create_storno()

        body = captured["body"]
        self.assertIs(body["vatPayer"], True)
        self.assertEqual(body["version"], 1662177617338)
        self.assertEqual(body["priceWithVat"], -100.0)
        self.assertFalse(body["useRounding"])
        self.assertEqual(len(body["items"]), 1)
        item = body["items"][0]
        self.assertEqual(item["type"], "CORRECTION")
        self.assertEqual(item["referenceReceiptId"], "V-TEST-AAA")
        self.assertEqual(item["priceWithVat"], -100.0)
        self.assertEqual(item["quantity"], 1)
        self.assertEqual(item["vatRate"], 0)
        self.assertEqual(item["receiptItemName"], "Úhrada faktúry: %s" % invoice_number)
        self.assertEqual(len(body["payments"]), 1)
        pay = body["payments"][0]
        self.assertEqual(pay["type"], "EXPENSE")
        self.assertEqual(pay["sum"], -100.0)
        self.assertEqual(pay["amount"], -100.0)

        # The storno confirmed and the original flipped to cancelled/stornoed.
        self.assertEqual(storno.receipt_type, "storno")
        self.assertEqual(storno.state, "confirmed")
        self.assertEqual(storno.reversed_receipt_id, receipt)
        self.assertEqual(receipt.state, "cancelled")
        self.assertTrue(receipt.is_stornoed)
