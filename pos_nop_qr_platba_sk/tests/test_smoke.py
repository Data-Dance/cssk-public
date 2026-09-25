"""End-to-end smoke test for the QR Platba POS flow.

Provisions a pos.config with NOP cert, opens a session, creates a draft
pos.order, and exercises: mint → confirm; mint → mismatch; cancel; close
without confirmation; timeout propagation.
"""

from unittest import mock

from odoo.tests import tagged

from odoo.addons.nop_kverkom_base.tests.common import NopBaseCase


@tagged("post_install", "-at_install")
class TestQrPlatbaPosSmoke(NopBaseCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()

        cls.provider = cls.env["payment.provider"].search(
            [("code", "=", "qr_platba_sk")], limit=1
        )
        assert cls.provider, "qr_platba_sk provider must be pre-loaded by data XML"
        bank_journal = cls.env["account.journal"].search(
            [("type", "=", "bank"), ("company_id", "=", cls.company.id)], limit=1
        )
        if not bank_journal:
            bank_journal = cls.env["account.journal"].create({
                "name": "Test Bank", "type": "bank", "code": "TBNK",
            })
        cls.provider.write({
            "state": "test", "is_published": True, "journal_id": bank_journal.id,
        })

        cls.product = cls.env["product.product"].create({
            "name": "Test product", "type": "consu",
            "list_price": 10.0, "available_in_pos": True,
        })

        cls.pos_payment_method = cls.env["pos.payment.method"].create({
            "name": "QR Platba",
            "is_online_payment": True,
            "online_payment_provider_ids": [(6, 0, cls.provider.ids)],
            "company_id": cls.company.id,
        })

        # Re-use the NOP-configured pos.config from the base fixture.
        cls.pos_config = cls.nop_pos_config
        # Close any leftover session so payment_method_ids can be changed.
        if cls.pos_config.current_session_id:
            cls.pos_config.current_session_id.sudo().write({"state": "closed"})
            cls.env.flush_all()
        cls.pos_config.write({
            "payment_method_ids": [(6, 0, cls.pos_payment_method.ids)],
        })

        pos_manager_group = cls.env.ref("point_of_sale.group_pos_manager")
        pos_user = pos_manager_group.all_user_ids.filtered(lambda u: u.id != 1)[:1]
        if not pos_user:
            pos_user = cls.env["res.users"].create({
                "name": "POS Smoke User",
                "login": "pos_smoke_user",
                "group_ids": [(4, pos_manager_group.id)],
            })
        cls.pos_config.with_user(pos_user).open_ui()
        cls.pos_session = cls.pos_config.current_session_id

        cls.pos_order = cls.env["pos.order"].create({
            "session_id": cls.pos_session.id,
            "company_id": cls.company.id,
            "pricelist_id": cls.pos_config.pricelist_id.id if cls.pos_config.pricelist_id else False,
            "lines": [(0, 0, {
                "product_id": cls.product.id, "qty": 1,
                "price_unit": 10.0, "price_subtotal": 10.0, "price_subtotal_incl": 10.0,
            })],
            "amount_tax": 0.0, "amount_total": 10.0,
            "amount_paid": 0.0, "amount_return": 0.0,
        })

    def _patch_accounting_side_effects(self):
        return mock.patch.object(
            type(self.env["payment.transaction"]),
            "_process_pos_online_payment",
            lambda self: None,
        )

    def _close_session(self):
        self.pos_session.sudo().write({"state": "closed"})
        self.env.flush_all()

    # --- Timeout config ---------------------------------------------------

    def test_qr_platba_timeout_seconds_default_and_propagation(self):
        self.assertEqual(self.pos_payment_method.qr_platba_timeout_seconds, 300)
        self.pos_payment_method.qr_platba_timeout_seconds = 120

        with mock.patch.object(
            self.env["nop.client"].__class__,
            "_generate_transaction_id",
            return_value="QR-" + "7" * 32,
        ):
            result = self.pos_order.create_qr_platba_transaction(10.0)

        self.assertEqual(result["timeout_seconds"], 120)
        nop_tx = self.env["nop.transaction"].browse(result["nop_transaction_id"])
        delta = (nop_tx.expires_at - nop_tx.create_date).total_seconds()
        self.assertAlmostEqual(delta, 120, delta=5)

    def test_qr_platba_timeout_seconds_minimum_validation(self):
        from odoo.exceptions import ValidationError
        with self.assertRaises(ValidationError):
            self.pos_payment_method.qr_platba_timeout_seconds = 5

    # --- Core flow --------------------------------------------------------

    def test_is_qr_platba_sk_computed(self):
        self.assertTrue(self.pos_payment_method.is_qr_platba_sk)
        self.assertTrue(self.pos_payment_method.is_online_payment)

    def test_create_qr_platba_transaction(self):
        with mock.patch.object(
            self.env["nop.client"].__class__,
            "_generate_transaction_id",
            return_value="QR-" + "a" * 32,
        ):
            result = self.pos_order.create_qr_platba_transaction(10.0)

        self.assertEqual(result["transaction_id"], "QR-" + "a" * 32)
        self.assertTrue(result["qr_url"].startswith("https://payme.sk/2/p/PME?"))
        self.assertIn("AM=10.00", result["qr_url"])
        self.assertIn("PI=QR-" + "a" * 32, result["qr_url"])

        nop_tx = self.env["nop.transaction"].browse(result["nop_transaction_id"])
        self.assertEqual(nop_tx.state, "pending")
        self.assertEqual(nop_tx.source_model, "pos.order")
        self.assertEqual(nop_tx.pos_config_id, self.pos_config)

    def test_happy_path_ingest_confirms_payment(self):
        with mock.patch.object(
            self.env["nop.client"].__class__,
            "_generate_transaction_id",
            return_value="QR-" + "b" * 32,
        ):
            result = self.pos_order.create_qr_platba_transaction(10.0)

        nop_tx = self.env["nop.transaction"].browse(result["nop_transaction_id"])
        payment_tx = self.env["payment.transaction"].browse(result["payment_transaction_id"])
        notification = self._build_notification(nop_tx.transaction_id, 10.0)

        with self._patch_accounting_side_effects():
            nop_tx._ingest_notification(notification)

        self.assertEqual(payment_tx.state, "done")
        self.assertEqual(nop_tx.state, "confirmed")

    def test_mismatch_does_not_confirm(self):
        with mock.patch.object(
            self.env["nop.client"].__class__,
            "_generate_transaction_id",
            return_value="QR-" + "c" * 32,
        ):
            result = self.pos_order.create_qr_platba_transaction(10.0)

        nop_tx = self.env["nop.transaction"].browse(result["nop_transaction_id"])
        payment_tx = self.env["payment.transaction"].browse(result["payment_transaction_id"])
        nop_tx._ingest_notification(
            self._build_notification(nop_tx.transaction_id, 10.0, corrupt_hash=True)
        )
        self.assertEqual(nop_tx.state, "mismatch")
        self.assertNotEqual(payment_tx.state, "done")

    def test_cancel_clears_pending(self):
        with mock.patch.object(
            self.env["nop.client"].__class__,
            "_generate_transaction_id",
            return_value="QR-" + "d" * 32,
        ):
            result = self.pos_order.create_qr_platba_transaction(10.0)

        self.pos_order.cancel_qr_platba_transaction(result["nop_transaction_id"])
        nop_tx = self.env["nop.transaction"].browse(result["nop_transaction_id"])
        payment_tx = self.env["payment.transaction"].browse(result["payment_transaction_id"])
        self.assertEqual(nop_tx.state, "cancelled")
        self.assertEqual(payment_tx.state, "cancel")

    # --- Close-without-confirmation ---------------------------------------

    def test_close_unconfirmed_returns_receipt_data(self):
        with mock.patch.object(
            self.env["nop.client"].__class__,
            "_generate_transaction_id",
            return_value="QR-" + "e" * 32,
        ):
            result = self.pos_order.create_qr_platba_transaction(10.0)

        with mock.patch.object(
            self.env["pos.config"].__class__,
            "_nop_poll_if_due",
            return_value=0,
        ):
            response = self.pos_order.close_qr_platba_unconfirmed(result["nop_transaction_id"])

        self.assertFalse(response["already_confirmed"])
        receipt = response["receipt"]
        self.assertEqual(receipt["transaction_id"], "QR-" + "e" * 32)
        self.assertTrue(receipt["created_at"])
        self.assertEqual(receipt["amount"], 10.0)
        self.assertEqual(receipt["currency"], "EUR")
        self.assertIn("kdejemojaplatba", receipt["public_history_url"])
        self.assertTrue(receipt["iban"])
        self.assertEqual(receipt["merchant_dic"], self.nop_pos_config.nop_vatsk)
        self.assertEqual(receipt["merchant_vat"], self.company.vat or "")
        self.assertEqual(receipt["merchant_ico"], self.company.company_registry or "")

        nop_tx = self.env["nop.transaction"].browse(result["nop_transaction_id"])
        payment_tx = self.env["payment.transaction"].browse(result["payment_transaction_id"])
        self.assertEqual(nop_tx.state, "unconfirmed_closed")
        self.assertEqual(payment_tx.state, "cancel")

    def test_close_unconfirmed_no_op_when_already_confirmed(self):
        with mock.patch.object(
            self.env["nop.client"].__class__,
            "_generate_transaction_id",
            return_value="QR-" + "f" * 32,
        ):
            result = self.pos_order.create_qr_platba_transaction(10.0)
        nop_tx = self.env["nop.transaction"].browse(result["nop_transaction_id"])
        with self._patch_accounting_side_effects():
            nop_tx._ingest_notification(
                self._build_notification(nop_tx.transaction_id, 10.0)
            )
        with mock.patch.object(
            self.env["pos.config"].__class__,
            "_nop_poll_if_due",
            return_value=0,
        ):
            response = self.pos_order.close_qr_platba_unconfirmed(result["nop_transaction_id"])
        self.assertTrue(response["already_confirmed"])
        self.assertIn(response["state"], ("received", "confirmed"))
