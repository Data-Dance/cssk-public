# -*- coding: utf-8 -*-
"""Automatic certificate renewal through the CA EET 2.0 API, with the CA and
the EET gateway both mocked: the JWT, the full happy path, a failed
verification (old certificate kept, download unacknowledged), a rejection
(one activity) and a rate limit (deferred, not failed)."""
import base64
import datetime
import json
from unittest.mock import patch

from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.serialization import pkcs12

from odoo import fields
from odoo.tests.common import TransactionCase

from ..lib import caeet_client, eet2_client
from .test_eet2_client import _throwaway_p12

UTC = datetime.timezone.utc
REQ_ID = "3fa85f64-5717-4562-b3fc-2c963f66afa6"


def _b64url_decode(text):
    return base64.urlsafe_b64decode(text + "=" * (-len(text) % 4))


class _Response:
    def __init__(self, status, body=None, headers=None):
        self.status_code = status
        self._body = body
        self.headers = headers or {}

    def json(self):
        if self._body is None:
            raise ValueError("no body")
        return self._body


class _FakeCA:
    """Scripted CA EET: ``status_script`` is consumed one answer per status call."""

    def __init__(self, new_p12, new_password):
        self.calls = []                 # (method, path, bearer)
        self.status_script = []
        self.renew_response = _Response(201, {"reqId": REQ_ID})
        self.new_p12 = new_p12
        self.new_password = new_password
        self.ack_response = _Response(204)

    def __call__(self, method, url, headers=None, timeout=None):
        path = url.split("/api", 1)[1]
        self.calls.append((method, path, (headers or {}).get("Authorization", "")))
        if path == "/request/renew":
            return self.renew_response
        if path.endswith("/status"):
            return self.status_script.pop(0) if self.status_script else _Response(500, {"code": 99, "message": "no script"})
        if path.endswith("/claim-download"):
            return _Response(200, {
                "pkcs12": base64.b64encode(self.new_p12).decode(),
                "password": self.new_password,
                "certificate": {"sn": "24961511666821687692", "state": "VALID",
                                "validFrom": "2026-10-01 00:00:00+00:00",
                                "validTo": "2027-10-02 00:00:00+00:00"},
            })
        if path.endswith("/ack-download"):
            return self.ack_response
        if path == "/request/not-finished":
            return _Response(200, {"count": 0, "data": []})
        return _Response(404, {"code": 4, "message": "Unknown object."})

    def paths(self):
        return [p for _m, p, _b in self.calls]


def _verified():
    return eet2_client.SendResult(eet2_client.Odpoved(chyba_kod=0, chyba_text="ok", test=True),
                                b"<v/>", "x")


def _bad_signature():
    return eet2_client.SendResult(eet2_client.Odpoved(chyba_kod=4, chyba_text="Neplatny podpis"),
                                b"<e/>", "x")


class TestEet2Renewal(TransactionCase):
    _REQ = "odoo.addons.l10n_cz_eet2.lib.caeet_client.requests.request"
    _SEND = "odoo.addons.l10n_cz_eet2.lib.eet2_client.send"

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        now = datetime.datetime.now(UTC)
        # The certificate in use expires in 10 days: due for renewal at 30.
        old_p12, _pw = _throwaway_p12(b"pw", not_before=now - datetime.timedelta(days=356))
        cls.old = cls.env["l10n.cz.eet2.certificate"].create({
            "name": "prod 2026", "company_id": cls.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(old_p12), "password": "pw",
        })
        cls.new_p12, _pw = _throwaway_p12(b"Ab12Cd34", not_before=now - datetime.timedelta(days=1))
        cls.company.write({
            "l10n_cz_eet2_enabled": True,
            "l10n_cz_eet2_environment": "playground",
            "l10n_cz_eet2_eic_popl": "CZ00000019",
            "l10n_cz_eet2_id_jednotky": 303,
            "l10n_cz_eet2_certificate_id": cls.old.id,
            "l10n_cz_eet2_renew_days_before": 30,
        })

    def setUp(self):
        super().setUp()
        self.ca = _FakeCA(self.new_p12, "Ab12Cd34")

    def _cron(self):
        self.env["l10n.cz.eet2.certificate"]._cron_renew_certificates()

    # --- the token -------------------------------------------------------
    def test_jwt_is_rs256_with_x5t_s256(self):
        cert = self.old._get_cert()
        token = caeet_client.make_jwt(cert.private_key, cert.cert)
        head, payload, signature = token.split(".")
        header = json.loads(_b64url_decode(head))
        self.assertEqual(header["alg"], "RS256")
        self.assertEqual(header["typ"], "JWT")
        der = cert.cert.public_bytes(serialization.Encoding.DER)
        digest = hashes.Hash(hashes.SHA256())
        digest.update(der)
        expected = base64.urlsafe_b64encode(digest.finalize()).rstrip(b"=").decode()
        self.assertEqual(header["x5t#S256"], expected)
        self.assertNotIn("x5c", header)
        self.assertEqual(json.loads(_b64url_decode(payload)), {})
        cert.cert.public_key().verify(
            _b64url_decode(signature), ("%s.%s" % (head, payload)).encode(),
            padding.PKCS1v15(), hashes.SHA256())

    def test_client_maps_errors(self):
        client = caeet_client.CaeetClient("https://ca.example/api", self.old._get_cert())
        with patch(self._REQ, return_value=_Response(429, {"code": 6, "message": "Too many"},
                                                    {"Retry-After": "120"})):
            with self.assertRaises(caeet_client.CaeetRateLimited) as cm:
                client.renew()
            self.assertEqual(cm.exception.retry_after, 120)
        with patch(self._REQ, return_value=_Response(401, {"code": 2, "message": "Unauthorized"})):
            with self.assertRaises(caeet_client.CaeetAuthError):
                client.status(REQ_ID)
        with patch(self._REQ, return_value=_Response(409, {"code": 5, "message": "Conflict"})):
            with self.assertRaises(caeet_client.CaeetConflict):
                client.ack_download(REQ_ID)
        with patch(self._REQ, return_value=_Response(200, {"state": "INPROCESS", "pollAfterSeconds": 2},
                                                    {"Retry-After": "7"})):
            info = client.status(REQ_ID)
        self.assertEqual(info["state"], "INPROCESS")
        self.assertEqual(info["poll_after"], 7, "the larger of body and header wins")

    # --- the cycle -------------------------------------------------------
    def test_happy_path_switches_only_after_verification(self):
        self.ca.status_script = [
            _Response(200, {"state": "INPROCESS", "pollAfterSeconds": 2, "reqId": REQ_ID}),
            _Response(200, {"state": "ISSUED", "reqId": REQ_ID}),
        ]
        with patch(self._REQ, side_effect=self.ca), patch(self._SEND, return_value=_verified()) as send:
            self._cron()
            self.assertEqual(self.old.renewal_state, "requested")
            self.assertEqual(self.old.renewal_req_id, REQ_ID)
            self.assertEqual(self.ca.paths(), ["/request/renew"])
            # the same run does not poll again before the request is due
            self.old.renewal_next_check = fields.Datetime.now()
            self._cron()
            self.assertEqual(self.old.renewal_state, "requested", "INPROCESS keeps waiting")
            self.assertGreater(self.old.renewal_next_check, fields.Datetime.now())
            self.old.renewal_next_check = fields.Datetime.now()
            self._cron()
            self.assertEqual(send.call_count, 1, "verification-mode message with the new certificate")
        new = self.old.renewed_by_id
        self.assertTrue(new)
        self.assertEqual(new.renews_id, self.old)
        self.assertEqual(new.password, "Ab12Cd34")
        self.assertEqual(new.subject_cn, "CZ00000019")
        self.assertTrue(new.valid_to > self.old.valid_to)
        self.assertEqual(new.environment, "playground")
        self.assertEqual(self.company.l10n_cz_eet2_certificate_id, new)
        self.assertEqual(self.old.renewal_state, "switched")
        self.assertFalse(self.old.active)
        paths = self.ca.paths()
        self.assertEqual(paths[-2:], ["/request/%s/claim-download" % REQ_ID,
                                      "/request/%s/ack-download" % REQ_ID])
        # every call carried a bearer token
        self.assertTrue(all(b.startswith("Bearer ") for _m, _p, b in self.ca.calls))
        # the verification message was sent with the NEW certificate
        tx = self.env["l10n.cz.eet2.transaction"].search(
            [("certificate_id", "=", new.id), ("overeni", "=", True)])
        self.assertEqual(len(tx), 1)
        self.assertEqual(tx.state, "verified")
        # a later run leaves a finished cycle alone
        with patch(self._REQ, side_effect=self.ca):
            n = len(self.ca.calls)
            self._cron()
        self.assertEqual(len(self.ca.calls), n)

    def test_failed_verification_keeps_old_and_never_acks(self):
        self.ca.status_script = [_Response(200, {"state": "DELIVERING", "reqId": REQ_ID})]
        with patch(self._REQ, side_effect=self.ca), patch(self._SEND, return_value=_bad_signature()):
            self._cron()                                   # request
            self.old.renewal_next_check = fields.Datetime.now()
            self._cron()                                   # poll -> claim -> verify fails
        self.assertEqual(self.old.renewal_state, "failed")
        self.assertTrue(self.old.active)
        self.assertEqual(self.company.l10n_cz_eet2_certificate_id, self.old)
        self.assertTrue(self.old.renewed_by_id, "the download is kept for a retry")
        self.assertNotIn("/request/%s/ack-download" % REQ_ID, self.ca.paths())
        self.assertEqual(len(self.old.activity_ids), 1)
        self.assertIn("Neplatny podpis", self.old.renewal_error)
        # a failed cycle is terminal for the cron: no further CA traffic
        with patch(self._REQ, side_effect=self.ca):
            n = len(self.ca.calls)
            self._cron()
        self.assertEqual(len(self.ca.calls), n)
        self.assertEqual(len(self.old.activity_ids), 1)
        # the button retries the verification with the download in hand
        with patch(self._REQ, side_effect=self.ca), patch(self._SEND, return_value=_verified()):
            self.old.action_renew()
        self.assertEqual(self.old.renewal_state, "switched")
        self.assertEqual(self.company.l10n_cz_eet2_certificate_id, self.old.renewed_by_id)
        self.assertEqual(self.ca.paths()[-1], "/request/%s/ack-download" % REQ_ID)

    def test_rejected_raises_one_activity(self):
        self.ca.status_script = [_Response(200, {
            "state": "REJECTED", "reqId": REQ_ID,
            "rejectedReason": "Selhani kontroly parametru zadosti"})]
        with patch(self._REQ, side_effect=self.ca):
            self._cron()
            self.old.renewal_next_check = fields.Datetime.now()
            self._cron()
            self.assertEqual(self.old.renewal_state, "rejected")
            self.assertIn("Selhani", self.old.renewal_error)
            self.assertEqual(len(self.old.activity_ids), 1)
            n = len(self.ca.calls)
            self._cron()
        self.assertEqual(len(self.ca.calls), n, "rejected is terminal for the cron")
        self.assertEqual(len(self.old.activity_ids), 1)
        self.assertTrue(self.old.active)
        self.assertEqual(self.company.l10n_cz_eet2_certificate_id, self.old)

    def test_rate_limit_defers_without_failing(self):
        self.ca.renew_response = _Response(429, {"code": 6, "message": "Too many requests."},
                                        {"Retry-After": "120"})
        with patch(self._REQ, side_effect=self.ca):
            self._cron()
            self.assertEqual(self.old.renewal_state, "none")
            self.assertFalse(self.old.activity_ids)
            self.assertFalse(self.old.renewal_req_id)
            self.assertGreaterEqual(
                self.old.renewal_next_check,
                fields.Datetime.now() + datetime.timedelta(seconds=100))
            # not due yet: the next run makes no call
            n = len(self.ca.calls)
            self._cron()
            self.assertEqual(len(self.ca.calls), n)
            # once due, the request goes through
            self.ca.renew_response = _Response(201, {"reqId": REQ_ID})
            self.old.renewal_next_check = fields.Datetime.now()
            self._cron()
        self.assertEqual(self.old.renewal_state, "requested")

    def test_unreachable_ca_defers(self):
        import requests
        with patch(self._REQ, side_effect=requests.ConnectionError("down")):
            self._cron()
        self.assertEqual(self.old.renewal_state, "none")
        self.assertTrue(self.old.renewal_next_check)
        self.assertFalse(self.old.activity_ids)

    def test_only_the_selected_and_due_certificate_is_renewed(self):
        now = datetime.datetime.now(UTC)
        spare_p12, _pw = _throwaway_p12(b"pw", not_before=now - datetime.timedelta(days=360))
        spare = self.env["l10n.cz.eet2.certificate"].create({
            "name": "spare, not selected", "company_id": self.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(spare_p12), "password": "pw",
        })
        fresh_p12, _pw = _throwaway_p12(b"pw", not_before=now - datetime.timedelta(days=10))
        fresh = self.env["l10n.cz.eet2.certificate"].create({
            "name": "fresh", "company_id": self.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(fresh_p12), "password": "pw",
        })
        self.company.l10n_cz_eet2_certificate_id = fresh
        with patch(self._REQ, side_effect=self.ca):
            self._cron()
        self.assertEqual(self.ca.calls, [], "nothing selected is due")
        self.assertEqual((spare.renewal_state, fresh.renewal_state), ("none", "none"))
        # opting out: the due, selected certificate is left alone at 0 days
        self.company.write({"l10n_cz_eet2_certificate_id": self.old.id,
                            "l10n_cz_eet2_renew_days_before": 0})
        with patch(self._REQ, side_effect=self.ca):
            self._cron()
        self.assertEqual(self.ca.calls, [])

    def test_expired_certificate_cannot_be_renewed(self):
        now = datetime.datetime.now(UTC)
        dead_p12, _pw = _throwaway_p12(b"pw", not_before=now - datetime.timedelta(days=400))
        dead = self.env["l10n.cz.eet2.certificate"].create({
            "name": "dead", "company_id": self.company.id,
            "environment": "playground",
            "p12_file": base64.b64encode(dead_p12), "password": "pw",
        })
        from odoo.exceptions import UserError
        with self.assertRaises(UserError):
            dead._renewal_request()

    def test_base_url_per_environment_is_a_system_parameter(self):
        Cert = self.env["l10n.cz.eet2.certificate"]
        self.assertEqual(Cert._caeet_base_url("production"), "https://ca.caeet.gov.cz/api")
        self.assertEqual(Cert._caeet_base_url("playground"), "https://ca.zkus.caeet.gov.cz/api")
        self.env["ir.config_parameter"].sudo().set_param(
            "l10n_cz_eet2.caeet_url_playground", "https://ca.test.caeet.gov.cz/api")
        self.assertEqual(Cert._caeet_base_url("playground"), "https://ca.test.caeet.gov.cz/api")
        self.assertEqual(self.old._caeet_client().base_url, "https://ca.test.caeet.gov.cz/api")

    def test_malformed_answer_fails_instead_of_crashing(self):
        self.ca.renew_response = _Response(201, {"unexpected": True})
        with patch(self._REQ, side_effect=self.ca):
            self._cron()
        self.assertEqual(self.old.renewal_state, "failed")
        self.assertIn("reqId", self.old.renewal_error)
        self.assertEqual(len(self.old.activity_ids), 1)

    def test_ack_conflict_still_completes_the_switch(self):
        """The company already runs on the new certificate when the ack goes
        out; a 409 (already finished) must not undo that."""
        self.ca.status_script = [_Response(200, {"state": "ISSUED", "reqId": REQ_ID})]
        self.ca.ack_response = _Response(409, {"code": 5, "message": "Conflict."})
        with patch(self._REQ, side_effect=self.ca), patch(self._SEND, return_value=_verified()):
            self._cron()
            self.old.renewal_next_check = fields.Datetime.now()
            self._cron()
        self.assertEqual(self.old.renewal_state, "switched")
        self.assertFalse(self.old.active)
        self.assertEqual(self.company.l10n_cz_eet2_certificate_id, self.old.renewed_by_id)
        self.assertIn("Conflict", self.old.renewal_error)

    def test_retry_after_http_date(self):
        from email.utils import format_datetime
        when = datetime.datetime.now(UTC) + datetime.timedelta(seconds=90)
        self.assertGreaterEqual(caeet_client._retry_after_seconds(format_datetime(when)), 80)
        self.assertEqual(caeet_client._retry_after_seconds("15"), 15)
        self.assertIsNone(caeet_client._retry_after_seconds("garbage"))
