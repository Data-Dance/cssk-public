from odoo.exceptions import UserError
from odoo.tests import tagged

from .common import NopBaseCase, TEST_IBAN


@tagged("post_install", "-at_install")
class TestNopTransaction(NopBaseCase):

    def _mint(self, amount=10.0):
        """Mint a pending nop.transaction without contacting NOP."""
        return self.env["nop.transaction"].with_context(nop_offline=True)._create_for_pos_config(
            self.nop_pos_config, amount=amount, comment="unit test"
        )

    def test_mint_creates_pending(self):
        tx = self._mint(42.50)
        self.assertEqual(tx.state, "pending")
        self.assertEqual(tx.expected_amount, 42.50)
        self.assertEqual(tx.expected_iban, TEST_IBAN.replace(" ", ""))
        self.assertTrue(tx.transaction_id.startswith("QR-"))
        self.assertEqual(len(tx.transaction_id), 3 + 32)  # "QR-" + 32 hex

    def test_ingest_happy_path(self):
        tx = self._mint(10.0)
        notification = self._build_notification(tx.transaction_id, 10.0)
        tx._ingest_notification(notification)
        self.assertEqual(tx.state, "received")
        self.assertTrue(tx.integrity_ok)
        self.assertTrue(tx.amount_ok)
        self.assertEqual(tx.received_amount, 10.0)

    def test_ingest_amount_mismatch(self):
        tx = self._mint(10.0)
        notification = self._build_notification(tx.transaction_id, 8.0)
        tx._ingest_notification(notification)
        self.assertEqual(tx.state, "mismatch")
        self.assertFalse(tx.amount_ok)
        self.assertTrue(tx.integrity_ok)  # hash recomputed against received amount

    def test_ingest_hash_mismatch(self):
        tx = self._mint(10.0)
        notification = self._build_notification(tx.transaction_id, 10.0, corrupt_hash=True)
        tx._ingest_notification(notification)
        self.assertEqual(tx.state, "mismatch")
        self.assertFalse(tx.integrity_ok)

    def test_late_arrival_on_cancelled_is_flagged(self):
        tx = self._mint(5.0)
        tx.action_cancel()
        self.assertEqual(tx.state, "cancelled")
        notification = self._build_notification(tx.transaction_id, 5.0)
        tx._ingest_notification(notification)
        self.assertEqual(tx.state, "mismatch", "late push on cancelled tx must be flagged")

    def test_duplicate_ingest_is_idempotent(self):
        tx = self._mint(7.0)
        notification = self._build_notification(tx.transaction_id, 7.0)
        tx._ingest_notification(notification)
        tx.state = "confirmed"
        # Second arrival (QoS-1 retransmit) must be a no-op.
        result = tx._ingest_notification(notification)
        self.assertFalse(result)
        self.assertEqual(tx.state, "confirmed")

    def test_cron_expires_old_pending(self):
        from datetime import datetime, timedelta
        tx = self._mint(1.0)
        self.env.cr.execute(
            "UPDATE nop_transaction SET create_date = %s WHERE id = %s",
            (datetime.utcnow() - timedelta(hours=3), tx.id),
        )
        tx.invalidate_recordset(["create_date"])
        self.env["nop.transaction"]._cron_expire_pending()
        self.assertEqual(tx.state, "expired")

    # ------------------------------------------------------------------
    # Close-without-confirmation / refund flow
    # ------------------------------------------------------------------

    def test_close_unconfirmed_transition(self):
        tx = self._mint(5.0)
        tx.action_close_unconfirmed()
        self.assertEqual(tx.state, "unconfirmed_closed")
        self.assertTrue(tx.closed_unconfirmed_at)
        self.assertEqual(tx.closed_unconfirmed_by_id, self.env.user)

    def test_close_unconfirmed_is_idempotent_after_confirm(self):
        """If NOP push arrived already, close-unconfirmed leaves 'received' in place."""
        tx = self._mint(5.0)
        tx._ingest_notification(self._build_notification(tx.transaction_id, 5.0))
        self.assertEqual(tx.state, "received")
        tx.action_close_unconfirmed()
        self.assertEqual(tx.state, "received")

    def test_late_push_on_unconfirmed_closed_flags_refund(self):
        tx = self._mint(5.0)
        tx.action_close_unconfirmed()
        tx._ingest_notification(self._build_notification(tx.transaction_id, 5.0))
        self.assertEqual(tx.state, "refund_pending")
        self.assertEqual(tx.received_amount, 5.0)

    def test_late_push_on_unconfirmed_with_bad_hash_is_mismatch(self):
        tx = self._mint(5.0)
        tx.action_close_unconfirmed()
        tx._ingest_notification(
            self._build_notification(tx.transaction_id, 5.0, corrupt_hash=True)
        )
        self.assertEqual(tx.state, "mismatch")

    def test_mark_refunded_requires_refund_pending(self):
        tx = self._mint(5.0)
        tx.action_close_unconfirmed()
        with self.assertRaises(UserError):
            tx.action_mark_refunded()

    def test_mark_refunded_happy_path(self):
        tx = self._mint(5.0)
        tx.action_close_unconfirmed()
        tx._ingest_notification(self._build_notification(tx.transaction_id, 5.0))
        self.assertEqual(tx.state, "refund_pending")
        tx.action_mark_refunded(refund_reference="BNK-2026-001")
        self.assertEqual(tx.state, "refunded")
        self.assertEqual(tx.refund_reference, "BNK-2026-001")
        self.assertEqual(tx.refunded_by_id, self.env.user)

    def test_cron_expires_unconfirmed_after_7_days(self):
        from datetime import datetime, timedelta
        tx = self._mint(1.0)
        tx.action_close_unconfirmed()
        self.env.flush_all()
        self.env.cr.execute(
            "UPDATE nop_transaction SET closed_unconfirmed_at = %s WHERE id = %s",
            (datetime.utcnow() - timedelta(days=8), tx.id),
        )
        tx.invalidate_recordset(["closed_unconfirmed_at"])
        self.env["nop.transaction"]._cron_expire_pending()
        self.assertEqual(tx.state, "expired_unreceived")

    def test_debtor_iban_captured_from_payload(self):
        tx = self._mint(5.0)
        notification = self._build_notification(tx.transaction_id, 5.0)
        notification["debtorAccount"] = {"iban": "SK9900000000000000000000"}
        tx._ingest_notification(notification)
        self.assertEqual(tx.debtor_iban, "SK9900000000000000000000")

    def test_public_history_url(self):
        tx = self._mint(5.0)
        self.assertTrue(tx.public_history_url)
        self.assertIn(tx.transaction_id, tx.public_history_url)
        self.assertIn("kdejemojaplatba", tx.public_history_url)
