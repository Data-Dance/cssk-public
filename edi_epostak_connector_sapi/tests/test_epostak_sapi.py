"""SAPI transport logic that is decidable without a network.

The two things most likely to be wrong in a silent, expensive way are the
idempotency key (a bad one either duplicates an invoice on the network or
permanently blocks a corrected re-send) and the status mapping (a wrong one
reports an undelivered invoice as delivered). Both are pinned here.
"""

from odoo.tests.common import TransactionCase

from odoo.addons.edi_epostak_connector_sapi.models.epostak_connector import (
    PERMANENT_CODES,
    RETRYABLE_STATUS,
)


class _FakeResponse:
    """Minimal stand-in for requests.Response for the error-parsing path."""

    def __init__(self, status_code=422, payload=None, text="", headers=None,
                 reason=""):
        self.status_code = status_code
        self._payload = payload
        self.text = text
        self.headers = headers or {}
        self.reason = reason
        self.content = (text or "").encode()

    def json(self):
        if self._payload is None:
            raise ValueError("no json")
        return self._payload


class TestEpostakSapi(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.connector = cls.env["epostak.connector"]

    def _message(self, name="idem.xml"):
        return self.env["edi.message"].create(
            {
                "name": name,
                "direction": "out",
                "provider": "epostak",
                "state": "ready",
            }
        )

    # ------------------------------------------------------------------
    # Idempotency
    # ------------------------------------------------------------------

    def test_idempotency_key_is_stable_for_the_same_payload(self):
        """A retry must present the same key so the API collapses it —
        otherwise a timed-out send that actually succeeded is delivered
        twice."""
        msg = self._message()
        payload = b"<Invoice>same</Invoice>"
        first = self.connector._idempotency_key(msg, payload)
        second = self.connector._idempotency_key(msg, payload)
        self.assertEqual(first, second)

    def test_idempotency_key_changes_with_the_payload(self):
        """_peppol_emit regenerates a corrected document onto the SAME
        edi.message. Reusing the key there is a permanent
        IDEMPOTENCY_KEY_MISMATCH, so the corrected invoice could never be
        sent."""
        msg = self._message()
        first = self.connector._idempotency_key(msg, b"<Invoice>v1</Invoice>")
        second = self.connector._idempotency_key(msg, b"<Invoice>v2</Invoice>")
        self.assertNotEqual(first, second)

    def test_identical_payloads_collapse_across_records(self):
        """The key is content-addressed, NOT scoped to the record.

        Two edi.message rows carrying the same invoice bytes — a message
        re-created after the first was deleted, say — must present the same
        key so ePošťák collapses them. Scoping the key by ``msg.id`` would put
        the same VAT invoice on the network twice.
        """
        payload = b"<Invoice>same</Invoice>"
        self.assertEqual(
            self.connector._idempotency_key(self._message("a.xml"), payload),
            self.connector._idempotency_key(self._message("b.xml"), payload),
        )

    def test_idempotency_key_is_a_uuid(self):
        """The API documents this header as a UUID."""
        import uuid as _uuid

        key = self.connector._idempotency_key(self._message(), b"<Invoice/>")
        self.assertEqual(str(_uuid.UUID(key)), key)

    # ------------------------------------------------------------------
    # Error classification
    # ------------------------------------------------------------------

    def test_error_detail_unwraps_the_nested_error_object(self):
        """ePošťák nests everything under "error". Reading the top level only
        stringified that whole dict into the message shown on the record."""
        detail = self.connector._error_detail(
            _FakeResponse(
                status_code=401,
                payload={"error": {
                    "category": "AUTH",
                    "code": "SAPI-AUTH-001",
                    "message": "Invalid client credentials",
                    "retryable": False,
                    "correlation_id": "335d2119-91a2-47b6-b55e-5dfd29ee4eb7",
                }},
            )
        )
        self.assertEqual(detail["code"], "SAPI-AUTH-001")
        self.assertIn("Invalid client credentials", detail["message"])
        self.assertNotIn("{", detail["message"], "the dict repr leaked through")
        # The correlation id is the first thing ePošťák support asks for.
        self.assertIn("335d2119", detail["message"])
        self.assertIs(detail["retryable"], False)

    def test_stated_retryability_wins_over_the_status_heuristic(self):
        """A 409 is in RETRYABLE_STATUS, but if the API says otherwise it
        knows better than our heuristic — retrying would burn attempts."""
        detail = self.connector._error_detail(
            _FakeResponse(
                status_code=409,
                payload={"error": {"code": "SAPI-DOC-011", "message": "dup",
                                   "retryable": False}},
            )
        )
        self.assertIs(detail["retryable"], False)

    def test_retryability_is_none_when_unstated(self):
        """Falls back to the status heuristic rather than guessing False."""
        detail = self.connector._error_detail(
            _FakeResponse(status_code=503, payload={"code": "TEMPORARY"}))
        self.assertIsNone(detail["retryable"])

    def test_error_detail_reads_code_and_message(self):
        detail = self.connector._error_detail(
            _FakeResponse(
                status_code=422,
                payload={"code": "SAPI-DOC-025", "message": "EndpointID mismatch"},
                headers={"Retry-After": "30"},
            )
        )
        self.assertEqual(detail["code"], "SAPI-DOC-025")
        self.assertIn("EndpointID mismatch", detail["message"])
        self.assertEqual(detail["retry_after"], 30)

    def test_error_detail_survives_a_non_json_body(self):
        """An edge proxy can answer HTML; the user still needs something."""
        detail = self.connector._error_detail(
            _FakeResponse(status_code=502, text="<html>Bad Gateway</html>")
        )
        self.assertEqual(detail["code"], "")
        self.assertIn("Bad Gateway", detail["message"])
        self.assertIsNone(detail["retry_after"])

    def test_error_detail_ignores_a_malformed_retry_after(self):
        detail = self.connector._error_detail(
            _FakeResponse(status_code=429, headers={"Retry-After": "Wed, 21 Oct"})
        )
        self.assertIsNone(detail["retry_after"])

    def test_retry_policy_vocabulary(self):
        """Backpressure and in-flight conflicts retry; a key mismatch or a
        rejected document must not burn five attempts."""
        for status in (409, 423, 429, 500, 503):
            self.assertIn(status, RETRYABLE_STATUS)
        for status in (400, 403, 404, 422):
            self.assertNotIn(status, RETRYABLE_STATUS)
        self.assertIn("IDEMPOTENCY_KEY_MISMATCH", PERMANENT_CODES)

    # ------------------------------------------------------------------
    # Delivery status mapping
    # ------------------------------------------------------------------

    def test_status_mapping(self):
        """'sent' is intake, not delivery: only 'delivered' may close the
        message, and every documented failure must open it."""
        cases = {
            "delivered": "done",
            "rejected": "error",
            "send_failed": "error",
            "delivery_failed": "error",
            "validation_failed": "error",
            "queued": "sent",
            "sent": "sent",
            "something_new": "sent",
        }
        for api_status, expected in cases.items():
            msg = self._message("status-%s.xml" % api_status)
            msg.write({"state": "sent", "provider_interchange_id": "doc_1"})
            self.connector._apply_status(msg, {"status": api_status})
            self.assertEqual(
                msg.state,
                expected,
                "API status %r should map to %r" % (api_status, expected),
            )

    def test_status_error_carries_the_reason(self):
        msg = self._message("rejected.xml")
        msg.write({"state": "sent", "provider_interchange_id": "doc_2"})
        self.connector._apply_status(
            msg, {"status": "rejected", "statusReason": "BR-CO-10 violated"}
        )
        self.assertEqual(msg.state, "error")
        self.assertIn("BR-CO-10 violated", msg.error_message)

    def test_status_is_matched_despite_padding_and_case(self):
        """The two API surfaces disagree on case (SENT/DELIVERED vs
        delivered), and an unmatched terminal status would leave a delivered
        invoice stuck in 'sent' forever."""
        msg = self._message("upper.xml")
        msg.write({"state": "sent", "provider_interchange_id": "doc_3"})
        self.connector._apply_status(msg, {"status": "  DELIVERED  "})
        self.assertEqual(msg.state, "done")

    def test_status_non_string_does_not_break_the_cron(self):
        """A malformed status must not raise: the cron walks every pending
        message, and an AttributeError here would stall the whole run."""
        msg = self._message("weird.xml")
        msg.write({"state": "sent", "provider_interchange_id": "doc_4"})
        self.connector._apply_status(msg, {"status": 42})
        self.assertEqual(msg.state, "sent")

    # ------------------------------------------------------------------
    # Untrusted remote text
    # ------------------------------------------------------------------

    def test_remote_text_cannot_forge_log_lines(self):
        """Error bodies come from the network and land in the log and in a
        user-visible field; newlines there would let a peer inject lines."""
        detail = self.connector._error_detail(
            _FakeResponse(
                status_code=422,
                payload={
                    "code": "VALIDATION",
                    "message": "bad\nWARNING fake log line\r\n\x00trailing",
                },
            )
        )
        self.assertNotIn("\n", detail["message"])
        self.assertNotIn("\r", detail["message"])
        self.assertNotIn("\x00", detail["message"])
        self.assertIn("fake log line", detail["message"])

    def test_remote_text_is_truncated(self):
        detail = self.connector._error_detail(
            _FakeResponse(status_code=500, text="x" * 5000)
        )
        self.assertLessEqual(len(detail["message"]), 500)
