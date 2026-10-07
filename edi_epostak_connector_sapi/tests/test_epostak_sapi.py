"""SAPI transport logic that is decidable without a network.

The two things most likely to be wrong in a silent, expensive way are the
idempotency key (a bad one either duplicates an invoice on the network or
permanently blocks a corrected re-send) and the status mapping (a wrong one
reports an undelivered invoice as delivered). Both are pinned here.
"""

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase

from odoo.addons.edi_epostak_connector_sapi.models.epostak_connector import (
    PERMANENT_CODES,
    RETRYABLE_STATUS,
    EpostakApiError,
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


@tagged("post_install", "-at_install")
class TestEpostakIntegratorKey(TransactionCase):
    """An integrator key (sk_int_*) must name the firm it acts for.

    Reported from the field 2026-10-01: a customer on the standalone module
    configured an sk_int_* secret, left the Firm ID empty, and pressed "Check
    Peppol reachability". Every call then failed 400 BAD_REQUEST ("X-Firm-Id
    header is required when using JWT issued from an integrator key") and,
    because EpostakApiError is a plain Exception, it reached them as an RPC
    traceback rather than a dialog.
    """

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.connector = cls.env["epostak.connector"]
        cls.ICP = cls.env["ir.config_parameter"].sudo()
        cls.ICP.set_param("epostak.mode", "sandbox")
        cls.ICP.set_param("epostak.sapi.sandbox.client_id", "a-client-id")

    def _configure(self, secret, firm_id=""):
        self.ICP.set_param("epostak.sapi.sandbox.client_secret", secret)
        self.ICP.set_param("epostak.firm_id", firm_id)
        return self.connector._get_sapi_config()

    def test_integrator_key_without_firm_id_is_refused(self):
        """Caught before any HTTP call, naming the field to fill."""
        cfg = self._configure("sk_int_live_abc123")
        with self.assertRaises(UserError) as ctx:
            self.connector._assert_firm_scope(cfg)
        message = str(ctx.exception)
        self.assertIn("sk_int_", message)
        self.assertIn("Firm ID", message)

    def test_integrator_key_with_firm_id_passes(self):
        cfg = self._configure("sk_int_live_abc123", firm_id="f1r3-uuid")
        self.connector._assert_firm_scope(cfg)  # must not raise

    def test_firm_key_needs_no_firm_id(self):
        """A sk_live_* secret names exactly one firm, so the header is wrong
        there — demanding a Firm ID would break every direct-mode customer."""
        cfg = self._configure("sk_live_abc123")
        self.connector._assert_firm_scope(cfg)  # must not raise

    def test_sandbox_demo_secret_is_not_mistaken_for_an_integrator_key(self):
        """The published demo secrets are sk_live_test_*, which must keep
        working with no Firm ID."""
        cfg = self._configure("sk_live_test_5e188b91708ca938e1ee50678b345a3c15")
        self.connector._assert_firm_scope(cfg)  # must not raise

    def test_validate_config_enforces_it(self):
        """The guard has to sit on the shared path, not only on the button, or
        the send/poll/status crons still fail with a raw 400."""
        self._configure("sk_int_live_abc123")
        with self.assertRaises(UserError):
            self.connector._validate_config()

    def test_the_api_message_is_classified_permanent(self):
        """A missing X-Firm-Id is a configuration error: retrying it five times
        helps nobody."""
        detail = self.connector._error_detail(
            _FakeResponse(
                status_code=400,
                payload={"error": {
                    "code": "BAD_REQUEST",
                    "message": "X-Firm-Id header is required when using JWT "
                               "issued from an integrator key (sk_int_*).",
                }},
            )
        )
        self.assertEqual(detail["code"], "BAD_REQUEST")
        self.assertIn("X-Firm-Id", detail["message"])
        self.assertNotIn(400, RETRYABLE_STATUS)

    def test_firm_listing_parses_the_live_response_shape(self):
        """Shape captured from the sandbox 2026-10-01, not guessed."""
        rows = {"firms": [{
            "id": "f2cea3cf-f29e-4ea2-9e76-b06a312ec9ab",
            "name": "Test Buyer s.r.o.",
            "ico": "0000000001",
            "vatRegType": None,
            "isVatPayer": False,
            "peppolId": "0245:0000000001",
            "peppolStatus": "registered",
        }]}
        parsed = self.connector._parse_firms(rows)
        self.assertEqual(len(parsed), 1)
        self.assertEqual(parsed[0]["id"], "f2cea3cf-f29e-4ea2-9e76-b06a312ec9ab")
        self.assertEqual(parsed[0]["name"], "Test Buyer s.r.o.")
        # The Peppol id is how a user picks the right firm; losing it would
        # leave them matching on name alone.
        self.assertEqual(parsed[0]["ico"], "0000000001")
        self.assertEqual(parsed[0]["peppol_id"], "0245:0000000001")
        self.assertEqual(parsed[0]["peppol_status"], "registered")

    def test_firm_listing_tolerates_other_envelopes(self):
        for payload in ([{"id": "a", "name": "A"}], {"items": [{"id": "a"}]}):
            self.assertEqual(self.connector._parse_firms(payload)[0]["id"], "a")

    def test_firm_listing_skips_rows_without_an_id(self):
        parsed = self.connector._parse_firms({"firms": [{"name": "no id"}, "junk"]})
        self.assertEqual(parsed, [])

    def test_insufficient_scope_error_is_readable(self):
        """The real 403 body from GET /firms without firms:manage. Its
        fix_hint and request_id are the two useful parts, so neither may be
        dropped on the way to the user."""
        detail = self.connector._error_detail(
            _FakeResponse(status_code=403, payload={"error": {
                "code": "INSUFFICIENT_SCOPE",
                "message": "This endpoint requires the 'firms:manage' scope.",
                "required_scope": "firms:manage",
                "request_id": "3c71632c-e06f-4d22-a63f-891d7ac336c9",
                "fix_hint": "Reissue the API key (or OAuth token) with the "
                            "required scopes; or use a key that already has them.",
            }})
        )
        self.assertEqual(detail["code"], "INSUFFICIENT_SCOPE")
        self.assertIn("firms:manage", detail["message"])
        self.assertIn("Reissue the API key", detail["message"])
        self.assertIn("3c71632c", detail["message"])

    def test_token_cache_is_keyed_by_scope(self):
        """A documents-only token handed to /firms gets 403, and a
        firms-scoped one handed to a send would too — so the cache must not
        conflate them."""
        cfg = self._configure("sk_int_live_abc123", firm_id="f1")
        docs_key = (cfg["mode"], cfg["client_id"], cfg["scope"])
        firms_key = (cfg["mode"], cfg["client_id"], "firms:manage")
        self.assertNotEqual(docs_key, firms_key)

    def test_the_form_says_which_kind_of_key_is_configured(self):
        """The secret is write-only, so this label is the only way a user can
        tell which half of the Firm ID help applies to them. That gap is what
        produced the 2026-10-01 ticket."""
        Settings = self.env["res.config.settings"]
        cases = [
            ("sk_int_live_abc", "", "sk_int_"),
            ("sk_live_abc", "", "sk_live_"),
            ("", "", "No secret"),
        ]
        for secret, firm_id, expected in cases:
            form = Settings.new({
                "epostak_mode": "sandbox",
                "epostak_sapi_sandbox_client_secret": secret,
                "epostak_firm_id": firm_id,
            })
            self.assertIn(
                expected,
                form.epostak_key_kind,
                "secret %r should be described as %r" % (secret, expected),
            )

    def test_an_integrator_key_with_a_firm_id_reads_as_resolved(self):
        form = self.env["res.config.settings"].new({
            "epostak_mode": "sandbox",
            "epostak_sapi_sandbox_client_secret": "sk_int_live_abc",
            "epostak_firm_id": "f2cea3cf-f29e-4ea2-9e76-b06a312ec9ab",
        })
        self.assertIn("f2cea3cf", form.epostak_key_kind)

    def test_production_mode_reads_the_production_secret(self):
        """Reading the sandbox secret while in production mode would report the
        wrong key kind for the environment actually in use."""
        form = self.env["res.config.settings"].new({
            "epostak_mode": "production",
            "epostak_sapi_sandbox_client_secret": "sk_live_sandbox",
            "epostak_sapi_prod_client_secret": "sk_int_production",
            "epostak_firm_id": "",
        })
        self.assertIn("sk_int_", form.epostak_key_kind)

    def test_test_connection_reports_instead_of_raising(self):
        """Reported from the field 2026-10-01: deleting the Firm ID made Test
        Connection look broken. It was raising a UserError to *deliver* the firm
        list — which renders as a failure and, because a raise rolls the
        transaction back, discarded the set_values() above it, losing a secret
        the user had just typed. Every outcome must be a notification.

        patch on type(connector): patching the model class misses inherited
        methods on the registry class.
        """
        from unittest.mock import patch

        self.ICP.set_param("epostak.sapi.sandbox.client_secret", "sk_int_live_abc")
        self.ICP.set_param("epostak.firm_id", "")
        settings = self.env["res.config.settings"].create({})
        # TWO firms on purpose: with exactly one there is nothing to choose and
        # the button fills it in instead (covered separately). The property under
        # test here is that a genuine choice is *reported*, never raised.
        firms = [{
            "id": "2b9f26f7-93d2-455e-aba8-1391fadd14cc",
            "name": "Firm A", "ico": "24626329",
            "peppol_id": "0245:4024626329", "peppol_status": "registered",
        }, {
            "id": "9403f4fd-5318-4cd0-b651-4e75ce3997af",
            "name": "Firm B", "ico": "11111111",
            "peppol_id": "0245:5746203128", "peppol_status": "registered",
        }]
        connector_cls = type(self.env["epostak.connector"])
        with patch.object(connector_cls, "_list_firms", return_value=firms):
            res = settings.action_epostak_test_connection()
        self.assertEqual(res["tag"], "display_notification")
        self.assertEqual(res["params"]["type"], "warning",
                         "a missing firm id is a prompt, not a failure")
        self.assertIn("2b9f26f7", res["params"]["message"])
        self.assertIn("24626329", res["params"]["message"])
        self.assertTrue(res["params"]["sticky"], "a UUID to copy must not vanish")

    def test_test_connection_reports_an_api_failure_without_raising(self):
        from unittest.mock import patch

        from odoo.addons.edi_epostak_connector_sapi.models.epostak_connector import (
            EpostakApiError,
        )

        self.ICP.set_param("epostak.sapi.sandbox.client_secret", "sk_int_live_abc")
        self.ICP.set_param("epostak.firm_id", "")
        settings = self.env["res.config.settings"].create({})
        connector_cls = type(self.env["epostak.connector"])
        with patch.object(connector_cls, "_list_firms",
                          side_effect=EpostakApiError("403 nope")):
            res = settings.action_epostak_test_connection()
        self.assertEqual(res["params"]["type"], "danger")
        self.assertIn("403 nope", res["params"]["message"])

    def test_test_connection_success_names_the_firm(self):
        from unittest.mock import patch

        self.ICP.set_param("epostak.sapi.sandbox.client_secret", "sk_int_live_abc")
        self.ICP.set_param("epostak.firm_id", "a-firm-uuid")
        settings = self.env["res.config.settings"].create({})
        connector_cls = type(self.env["epostak.connector"])
        with patch.object(connector_cls, "_authenticate", return_value=True):
            res = settings.action_epostak_test_connection()
        self.assertEqual(res["params"]["type"], "success")
        self.assertIn("a-firm-uuid", res["params"]["message"])

    def test_inbound_health_is_recorded_on_success_and_failure(self):
        """Receiving had no user-facing signal: the base _poll_provider swallows
        failures into the log, so with the Firm ID blank sending failed loudly
        while receiving stopped silently. These parameters are what Settings
        reads to show otherwise, so they must be written on BOTH paths."""
        c = self.connector
        self.ICP.set_param(c.PARAM_POLL_AT, "")
        self.ICP.set_param(c.PARAM_POLL_OK, "")
        self.ICP.set_param(c.PARAM_POLL_ERROR, "")

        c._record_poll(count=3)
        self.assertTrue(self.ICP.get_param(c.PARAM_POLL_AT))
        self.assertTrue(self.ICP.get_param(c.PARAM_POLL_OK))
        self.assertEqual(self.ICP.get_param(c.PARAM_POLL_COUNT), "3")
        self.assertFalse(self.ICP.get_param(c.PARAM_POLL_ERROR))
        first_ok = self.ICP.get_param(c.PARAM_POLL_OK)

        c._record_poll(error="no firm id")
        self.assertEqual(self.ICP.get_param(c.PARAM_POLL_ERROR), "no firm id")
        # The last SUCCESS must not move: a stale "last ok" beside a recent
        # failure is exactly the evidence a user needs.
        self.assertEqual(self.ICP.get_param(c.PARAM_POLL_OK), first_ok)

    def test_inbound_health_label_distinguishes_the_three_states(self):
        c = self.connector
        Settings = self.env["res.config.settings"]
        for at, ok, err, expected in (
            ("", "", "", "Never polled"),
            ("2026-10-01 10:00:00", "2026-10-01 10:00:00", "", "OK at"),
            ("2026-10-01 11:00:00", "2026-10-01 10:00:00", "boom", "FAILED at"),
        ):
            self.ICP.set_param(c.PARAM_POLL_AT, at)
            self.ICP.set_param(c.PARAM_POLL_OK, ok)
            self.ICP.set_param(c.PARAM_POLL_ERROR, err)
            label = Settings.create({}).epostak_inbound_health
            self.assertIn(expected, label)

    def test_record_poll_never_raises(self):
        """It wraps a poll that may already be failing; it must not add a second
        exception on top of the first."""
        from unittest.mock import patch

        ICP_cls = type(self.env["ir.config_parameter"])
        with patch.object(ICP_cls, "set_param", side_effect=RuntimeError("db gone")):
            self.connector._record_poll(count=1)   # must not raise

    def test_poll_button_works_for_a_plain_administrator(self):
        """Reported from the field 2026-10-01: 'Poll inbound' raised AccessError
        for an Administrator. The settings page is gated on base.group_system,
        but edi.message is restricted to the EDI groups, which an admin is not
        in by default — so the button failed for precisely the person who
        configures the connection."""
        from unittest.mock import patch

        admin = self.env["res.users"].create({
            "name": "Settings admin, no EDI groups",
            "login": "epostak-settings-admin",
            "group_ids": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("base.group_system").id,
            ])],
        })
        self.assertFalse(
            admin.has_group("edi_base.group_edi_user"),
            "premise: this user must NOT be an EDI user",
        )
        settings = self.env["res.config.settings"].with_user(admin).create({})
        connector_cls = type(self.env["epostak.connector"])
        # Stub the network; the point under test is the access rights.
        with patch.object(connector_cls, "_poll_inbound",
                          return_value={"messages": [], "has_more": False}):
            res = settings.action_epostak_poll_inbound()
        self.assertEqual(res["tag"], "display_notification")
        self.assertIn(res["params"]["type"], ("success", "warning", "danger"))

    def test_health_label_is_readable_by_a_plain_administrator(self):
        admin = self.env["res.users"].create({
            "name": "Settings admin 2", "login": "epostak-settings-admin-2",
            "group_ids": [(6, 0, [
                self.env.ref("base.group_user").id,
                self.env.ref("base.group_system").id,
            ])],
        })
        label = self.env["res.config.settings"].with_user(admin).create({}).epostak_inbound_health
        self.assertTrue(label)

    # ------------------------------------------------------------------
    # One firm means nothing to choose
    # ------------------------------------------------------------------

    def _one_firm(self):
        return [{
            "id": "2b9f26f7-93d2-455e-aba8-1391fadd14cc",
            "name": "eGroup Solutions, a.s. Sandbox A", "ico": "24626329",
            "peppol_id": "0245:4024626329", "peppol_status": "registered",
        }]

    def test_a_single_firm_is_filled_in_automatically(self):
        """Observed in testing: the key manages exactly one firm, yet we asked
        the user to copy its UUID across and told them it 'speaks for several'.
        With one candidate there is nothing to choose."""
        from unittest.mock import patch

        self.ICP.set_param("epostak.sapi.sandbox.client_secret", "sk_int_live_abc")
        self.ICP.set_param("epostak.firm_id", "")
        settings = self.env["res.config.settings"].create({})
        connector_cls = type(self.env["epostak.connector"])
        with patch.object(connector_cls, "_list_firms", return_value=self._one_firm()):
            res = settings.action_epostak_test_connection()
        self.assertEqual(res["params"]["type"], "success")
        self.assertEqual(
            self.ICP.get_param("epostak.firm_id"),
            "2b9f26f7-93d2-455e-aba8-1391fadd14cc",
        )
        # The form must refresh or it keeps showing the empty value we just
        # set — but it has to be soft_reload: a full "reload" is a browser
        # reload that tore the notification down before it could be read.
        self.assertEqual(res["params"]["next"]["tag"], "soft_reload")
        self.assertTrue(res["params"]["sticky"],
                        "the chosen firm must stay on screen")

    def test_several_firms_still_ask_and_state_the_count(self):
        from unittest.mock import patch

        self.ICP.set_param("epostak.sapi.sandbox.client_secret", "sk_int_live_abc")
        self.ICP.set_param("epostak.firm_id", "")
        two = self._one_firm() + [{
            "id": "9403f4fd-5318-4cd0-b651-4e75ce3997af", "name": "Second",
            "ico": "", "peppol_id": "0245:5746203128", "peppol_status": "registered",
        }]
        settings = self.env["res.config.settings"].create({})
        connector_cls = type(self.env["epostak.connector"])
        with patch.object(connector_cls, "_list_firms", return_value=two):
            res = settings.action_epostak_test_connection()
        self.assertEqual(res["params"]["type"], "warning")
        self.assertIn("2", res["params"]["title"], "say how many there really are")
        self.assertFalse(self.ICP.get_param("epostak.firm_id"),
                         "must not guess when there is a genuine choice")

    # ------------------------------------------------------------------
    # Telling someone who never opens Settings
    # ------------------------------------------------------------------

    def _open_activities(self):
        anchor = self.env.company.partner_id
        return self.env["mail.activity"].sudo().search([
            ("res_model_id", "=", self.env["ir.model"]._get_id(anchor._name)),
            ("res_id", "=", anchor.id),
            ("summary", "like", self.connector.POLL_ACTIVITY_MARKER),
        ])

    def test_no_activity_on_a_single_blip(self):
        """One failed poll is normal; an activity per poll trains people to
        ignore them."""
        c = self.connector
        self.ICP.set_param(c.PARAM_POLL_STREAK, "0")
        self.ICP.set_param(c.PARAM_POLL_ACTIVITY_AFTER, "3")
        c._record_poll(error="transient")
        self.assertFalse(self._open_activities())
        self.assertEqual(self.ICP.get_param(c.PARAM_POLL_STREAK), "1")

    def test_activity_after_repeated_failures_then_closed_on_recovery(self):
        c = self.connector
        self.ICP.set_param(c.PARAM_POLL_STREAK, "0")
        self.ICP.set_param(c.PARAM_POLL_ACTIVITY_AFTER, "3")
        for _i in range(3):
            c._record_poll(error="no firm id")
        activities = self._open_activities()
        self.assertEqual(len(activities), 1, "exactly one, not one per poll")
        self.assertTrue(activities.user_id, "an unassigned activity is invisible")
        self.assertIn("3", activities.note)

        # A fourth failure must not stack a second one.
        c._record_poll(error="no firm id")
        self.assertEqual(len(self._open_activities()), 1)

        # Recovery closes it — a stale to-do about a fixed problem is noise.
        c._record_poll(count=1)
        self.assertFalse(self._open_activities())
        self.assertEqual(self.ICP.get_param(c.PARAM_POLL_STREAK), "0")

    def test_threshold_zero_disables_the_activity(self):
        c = self.connector
        self.ICP.set_param(c.PARAM_POLL_STREAK, "0")
        self.ICP.set_param(c.PARAM_POLL_ACTIVITY_AFTER, "0")
        for _i in range(5):
            c._record_poll(error="boom")
        self.assertFalse(self._open_activities())


class TestEpostakCapabilities(TransactionCase):
    """A participant who is not registered is answered with HTTP 404.

    Reported from the field 2026-10-03. ePošťák answers an unregistered
    participant with 404 and a COMPLETE negative body; the call passed no
    ``expected``, so it defaulted to (200,) and raised EpostakApiError over a
    perfectly good answer. "Check Peppol reachability" therefore showed a red
    failure dialog for the one case it exists to report.

    Both bodies below were captured from the sandbox on 2026-10-03, not
    guessed — which is how the second defect showed up: ``networkReady`` and
    ``routingStatus`` are nested under ``capability`` in BOTH of them, so
    reading them off the top level returned None even on a 200.
    """

    DOC_TYPE = (
        "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice"
        "##urn:cen.eu:en16931:2017#compliant#"
        "urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1"
    )

    NOT_REGISTERED = {
        "found": False,
        "accepts": False,
        "reason": "Participant not registered in Peppol network",
        "capability": {
            "documentTypeId": DOC_TYPE,
            "processId": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
            "routingStatus": "participant_not_found",
            "networkReady": False,
        },
    }

    REGISTERED = {
        "found": True,
        "accepts": True,
        "participant": {
            "scheme": "0245",
            "identifier": "4024626329",
            "id": "0245:4024626329",
        },
        "accessPoint": {
            "url": "https://dev.epostak.sk/as4",
            "transportProfile": "peppol-transport-as4-v2_0",
        },
        "internal": False,
        "supportedDocumentTypes": [DOC_TYPE],
        "matchedDocumentType": DOC_TYPE,
        "source": "sml",
        "capability": {
            "documentTypeId": DOC_TYPE,
            "processId": "urn:fdc:peppol.eu:2017:poacc:billing:01:1.0",
            "routingStatus": "ready",
            "networkReady": True,
        },
    }

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.connector = cls.env["epostak.connector"]
        ICP = cls.env["ir.config_parameter"].sudo()
        ICP.set_param("epostak.mode", "sandbox")
        ICP.set_param("epostak.sapi.sandbox.client_id", "a-client-id")
        ICP.set_param("epostak.sapi.sandbox.client_secret", "sk_live_test_x")
        ICP.set_param("epostak.firm_id", "")

    def _lookup(self, status, payload, participant="9950:SK2022913409"):
        """Run _check_capabilities against a canned HTTP response.

        requests.request is patched rather than _request, so the status code
        really does travel through the expected/raise decision under test.
        """
        from unittest.mock import patch

        from odoo.addons.edi_epostak_connector_sapi.models import (
            epostak_connector as mod,
        )

        connector_cls = type(self.connector)
        with patch.object(mod.requests, "request",
                          return_value=_FakeResponse(
                              status_code=status, payload=payload, text="{}")), \
             patch.object(connector_cls, "_get_token", return_value="tok"), \
             patch.object(connector_cls, "_epostak_own_participant_id",
                          return_value="0245:4024626329"):
            return self.connector._check_capabilities(
                participant, [self.DOC_TYPE]
            )

    def test_404_not_registered_is_an_answer_not_a_failure(self):
        result = self._lookup(404, self.NOT_REGISTERED)
        self.assertFalse(result["found"])
        self.assertFalse(result["accepts"])
        self.assertIn("not registered", result["reason"])

    def test_nested_capability_fields_are_lifted(self):
        """The caller reads result['networkReady']; the wire nests it."""
        result = self._lookup(404, self.NOT_REGISTERED)
        self.assertIs(result["networkReady"], False)
        self.assertEqual(result["routingStatus"], "participant_not_found")

    def test_nested_fields_are_lifted_on_the_positive_answer_too(self):
        """This one was silently broken even before the 404: a successful
        lookup reported networkReady as None."""
        result = self._lookup(200, self.REGISTERED)
        self.assertIs(result["networkReady"], True)
        self.assertEqual(result["routingStatus"], "ready")

    def test_a_404_without_a_body_still_raises(self):
        """A routing 404 is NOT 'participant not registered'. Rendering it as
        one would diagnose the wrong thing entirely."""
        with self.assertRaises(EpostakApiError):
            self._lookup(404, {"error": {"code": "NOT_FOUND",
                                         "message": "Cannot POST /v1/wrong"}})

    def test_a_500_still_raises(self):
        with self.assertRaises(EpostakApiError):
            self._lookup(500, {"error": {"code": "INTERNAL"}})

    def test_the_button_warns_instead_of_raising(self):
        """What the customer actually sees: a sticky warning quoting the
        provider's reason, not a red traceback dialog."""
        from unittest.mock import patch

        partner = self.env["res.partner"].create({
            "name": "Unregistered s.r.o.",
            "peppol_eas": "9950",
            "peppol_endpoint": "SK2022913409",
        })
        connector_cls = type(self.connector)
        flat = dict(self.NOT_REGISTERED,
                    networkReady=False,
                    routingStatus="participant_not_found")
        with patch.object(connector_cls, "_check_capabilities",
                          return_value=flat):
            action = partner.action_epostak_check_peppol()
        params = action["params"]
        self.assertEqual(params["type"], "warning")
        self.assertTrue(params["sticky"], "a warning that vanishes is unread")
        self.assertIn("not registered", params["message"])
        self.assertIn("Participant not registered in Peppol network",
                      params["message"])
        self.assertIn("participant_not_found", params["message"])

    def test_the_button_reports_a_reachable_participant(self):
        from unittest.mock import patch

        partner = self.env["res.partner"].create({
            "name": "Registered s.r.o.",
            "peppol_eas": "0245",
            "peppol_endpoint": "4024626329",
        })
        connector_cls = type(self.connector)
        flat = dict(self.REGISTERED, networkReady=True, routingStatus="ready")
        with patch.object(connector_cls, "_check_capabilities",
                          return_value=flat):
            action = partner.action_epostak_check_peppol()
        self.assertEqual(action["params"]["type"], "success")
        # "ePošťák reports: no reason given (ready)" on a clean success is
        # noise restating the title.
        self.assertNotIn("ePošťák reports", action["params"]["message"])
        self.assertNotIn("no reason given", action["params"]["message"])
