"""Mocked REST tests for :class:`NopClient`."""

from unittest import mock
from odoo.tests import tagged
from .common import NopBaseCase, TEST_POKLADNICA


def _fake_response(json_data=None, status_code=200, headers=None):
    resp = mock.Mock()
    resp.status_code = status_code
    resp.json.return_value = json_data or {}
    resp.content = b"{}" if json_data else b""
    resp.text = ""
    resp.headers = headers or {}
    resp.raise_for_status = mock.Mock()
    return resp


@tagged("post_install", "-at_install")
class TestNopClient(NopBaseCase):

    def test_generate_transaction_id_roundtrip(self):
        fake_resp = _fake_response({
            "transaction_id": "QR-abcdef1234567890abcdef1234567890",
            "created_at": "2026-04-16T10:00:00Z",
        })
        with mock.patch("requests.request", return_value=fake_resp) as mocked:
            tx_id = self.env["nop.client"]._generate_transaction_id(
                self.nop_pos_config, comment="hello"
            )
        self.assertEqual(tx_id, "QR-abcdef1234567890abcdef1234567890")
        call = mocked.call_args
        self.assertEqual(call.args[0], "POST")
        self.assertTrue(call.args[1].endswith("/api/v1/generateNewTransactionId"))
        self.assertEqual(call.kwargs["json"], {"comment": "hello"})

    def test_generate_transaction_id_fallback_field_name(self):
        fake_resp = _fake_response({"id": "QR-" + "f" * 32, "created_at": "2026-04-16T10:00:00Z"})
        with mock.patch("requests.request", return_value=fake_resp):
            tx_id = self.env["nop.client"]._generate_transaction_id(self.nop_pos_config)
        self.assertEqual(tx_id, "QR-" + "f" * 32)

    def test_drain_ingests_pending_notifications(self):
        NopTx = self.env["nop.transaction"].with_context(nop_offline=True)
        tx1 = NopTx._create_for_pos_config(self.nop_pos_config, amount=1.50)
        tx2 = NopTx._create_for_pos_config(self.nop_pos_config, amount=9.99)
        notifications = [
            self._build_notification(tx1.transaction_id, 1.50),
            self._build_notification(tx2.transaction_id, 9.99),
        ]
        fake_resp = _fake_response(notifications, headers={"x-result-truncated": "false"})
        with mock.patch("requests.request", return_value=fake_resp) as mocked:
            ingested = self.env["nop.client"]._drain(self.nop_pos_config)
        self.assertEqual(ingested, 2)
        self.assertEqual(tx1.state, "received")
        self.assertEqual(tx2.state, "received")
        call = mocked.call_args
        self.assertIn(f"POKLADNICA-{TEST_POKLADNICA}", call.args[1])

    def test_drain_paginates(self):
        tx = self.env["nop.transaction"].with_context(nop_offline=True)._create_for_pos_config(
            self.nop_pos_config, amount=2.00
        )
        page1 = _fake_response(
            [self._build_notification(tx.transaction_id, 2.00)],
            headers={"x-result-truncated": "true"},
        )
        page2 = _fake_response([], headers={"x-result-truncated": "false"})
        with mock.patch("requests.request", side_effect=[page1, page2]) as mocked:
            ingested = self.env["nop.client"]._drain(self.nop_pos_config)
        self.assertEqual(ingested, 1)
        self.assertEqual(mocked.call_count, 2)
        second_call = mocked.call_args_list[1]
        self.assertIn("after_id", second_call.kwargs.get("params", {}))

    def test_drain_rate_limited(self):
        fake_resp = _fake_response([], headers={"x-result-truncated": "false"})
        with mock.patch("requests.request", return_value=fake_resp) as mocked:
            self.nop_pos_config._nop_poll_if_due(min_interval_seconds=30)
            self.nop_pos_config._nop_poll_if_due(min_interval_seconds=30)
            self.nop_pos_config._nop_poll_if_due(min_interval_seconds=30)
        self.assertEqual(
            mocked.call_count, 1, "rate-limit must prevent duplicate concurrent polls"
        )
