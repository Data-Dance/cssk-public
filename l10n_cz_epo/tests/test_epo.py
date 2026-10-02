# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""EPO channel, with a throwaway self-signed certificate and EPO mocked.

No test here talks to EPO: every answer is a fixture shaped as the interface
specification (PodatelnaEPO.pdf v1.11) describes it.
"""

import base64
import datetime
from unittest.mock import MagicMock, patch

from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_cz_epo.lib import epo

POST = "odoo.addons.l10n_cz_epo.lib.epo.requests.post"
PISEMNOST = (b'<?xml version="1.0" encoding="UTF-8"?>\n<Pisemnost nazevSW="t">'
             b'<DPHDP3 verzePis="02.01"><VetaD dokument="DP3"/></DPHDP3></Pisemnost>')


def _make_p12(days_valid=365, not_before_days=-1):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Test Filer")])
    now = datetime.datetime.now(datetime.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(name).issuer_name(name).public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now + datetime.timedelta(days=not_before_days))
            .not_valid_after(now + datetime.timedelta(days=days_valid))
            .sign(key, hashes.SHA256()))
    p12 = pkcs12.serialize_key_and_certificates(
        b"t", key, cert, None,
        serialization.BestAvailableEncryption(b"secret"))
    return key, cert, p12


def _response(content, status=200):
    resp = MagicMock()
    resp.status_code = status
    resp.content = content
    return resp


@tagged("post_install", "-at_install")
class TestEpoLib(TransactionCase):

    def test_the_filing_is_embedded_der_signed_data(self):
        key, cert, _p12 = _make_p12()
        signed = epo.sign(PISEMNOST, key, cert)
        self.assertEqual(signed[0], 0x30)  # a DER SEQUENCE
        self.assertEqual(epo.unwrap(signed), PISEMNOST)  # data embedded, unchanged

    def test_a_clean_check_is_only_the_test_notice(self):
        answer = epo.parse_answer(
            b'<Chyby><Chyba Typ="I" Zkr="TEST_REZIM"><Text>Testovaci rezim</Text>'
            b'</Chyba></Chyby>')
        self.assertEqual(answer["kind"], "errors")
        self.assertTrue(answer["test_clean"])
        self.assertFalse(answer["blocking"])

    def test_a_signed_receipt_yields_the_filing_number(self):
        key, cert, _p12 = _make_p12()
        potvrzeni = epo.sign(
            b'<Pisemnost><Podani Cislo="12345/26" Datum="29.09.2026" Heslo="abc"/>'
            b'</Pisemnost>', key, cert)
        answer = epo.parse_answer(potvrzeni)
        self.assertEqual(
            (answer["kind"], answer["number"], answer["password"]),
            ("receipt", "12345/26", "abc"))


@tagged("post_install", "-at_install")
class TestEpoChannel(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.account_fiscal_country_id = cls.env.ref("base.cz")
        _key, _cert, p12 = _make_p12()
        cls.certificate = cls.env["l10n.cz.epo.certificate"].create({
            "name": "Test", "p12_file": base64.b64encode(p12),
            "password": "secret", "company_id": cls.company.id,
        })
        cls.company.l10n_cz_epo_certificate_id = cls.certificate
        partner = cls.env["res.partner"].create({"name": "Filing holder"})
        payload = cls.env["ir.attachment"].create({
            "name": "DPHDP3.xml", "raw": PISEMNOST, "mimetype": "application/xml",
        })
        cls.submission = cls.env["cssk.submission"].create({
            "res_model": "res.partner", "res_id": partner.id,
            "channel": "cz_epo", "company_id": cls.company.id,
            "payload_attachment_id": payload.id,
        })

    def test_the_certificate_is_read_on_upload(self):
        self.assertIn("Test Filer", self.certificate.subject)
        self.assertTrue(self.certificate.valid_to)

    def test_a_check_is_a_test_call_and_files_nothing(self):
        clean = b'<Chyby><Chyba Typ="I" Zkr="TEST_REZIM"><Text>ok</Text></Chyba></Chyby>'
        with patch(POST, return_value=_response(clean)) as post:
            self.submission.action_epo_check()
        self.assertEqual(post.call_args.kwargs["params"], {"test": "1"})
        self.assertEqual(self.submission.epo_check_result, "clean")
        self.assertEqual(self.submission.state, "draft")
        self.assertTrue(self.submission.epo_check_attachment_id)

    def test_a_check_with_errors_says_so(self):
        answer = (b'<Chyby><Chyba Typ="K" Zkr="DIC" Polozka="dic" Oddil="VetaP">'
                  b'<Text>Neplatne DIC</Text></Chyba></Chyby>')
        with patch(POST, return_value=_response(answer)):
            self.submission.action_epo_check()
        self.assertEqual(self.submission.epo_check_result, "errors")
        self.assertIn("Neplatne DIC", self.submission.epo_check_summary)

    def test_filing_is_refused_while_switched_off(self):
        self.company.l10n_cz_epo_allow_filing = False
        self.submission.action_queue()
        with patch(POST) as post:
            self.submission.action_send()
        post.assert_not_called()
        self.assertEqual(self.submission.state, "failed")
        self.assertIn("switched off", self.submission.last_error)

    def _file(self):
        self.company.l10n_cz_epo_allow_filing = True
        key, cert, _p12 = _make_p12()
        potvrzeni = epo.sign(
            b'<Pisemnost><Podani Cislo="98765/26" Datum="29.09.2026" Heslo="pw"/>'
            b'</Pisemnost>', key, cert)
        self.submission.action_queue()
        with patch(POST, return_value=_response(potvrzeni)) as post:
            self.submission.action_send()
        return post

    def test_a_filing_is_delivered_with_its_number_and_receipt(self):
        post = self._file()
        self.assertIsNone(post.call_args.kwargs["params"])  # no test flag
        self.assertEqual(self.submission.state, "delivered")
        self.assertEqual(self.submission.external_ref, "98765/26")
        self.assertTrue(self.submission.receipt_attachment_ids)
        self.assertTrue(self.submission.sealed_attachment_id)

    def test_the_tax_office_accepts(self):
        self._file()
        with patch(POST, return_value=_response(
                b'<Stav stav_podapl="3" stav_podpre="1"/>')):
            self.submission._channel_poll_cz_epo()
        self.assertEqual(self.submission.state, "accepted")

    def test_the_tax_office_rejects(self):
        self._file()
        with patch(POST, return_value=_response(b'<Stav stav_podapl="2"/>')):
            self.submission._channel_poll_cz_epo()
        self.assertEqual(self.submission.state, "rejected")

    def test_an_expired_certificate_is_refused(self):
        _key, _cert, p12 = _make_p12(days_valid=-1, not_before_days=-10)
        self.certificate.write({"p12_file": base64.b64encode(p12)})
        with self.assertRaisesRegex(UserError, "expired"):
            self.submission.action_epo_check()

    def test_an_unknown_outcome_is_not_retried(self):
        """A timeout after the request went out may mean it was filed:
        sending it again could file twice."""
        import requests

        self.company.l10n_cz_epo_allow_filing = True
        self.submission.action_queue()
        with patch(POST, side_effect=requests.ReadTimeout("slow")):
            self.submission.action_send()
        self.assertEqual(self.submission.state, "failed")
        self.assertIn("unknown", self.submission.last_error)

    def test_an_unreachable_epo_is_retried(self):
        import requests

        self.company.l10n_cz_epo_allow_filing = True
        self.submission.action_queue()
        with patch(POST, side_effect=requests.ConnectTimeout("down")):
            self.submission.action_send()
        self.assertEqual(self.submission.state, "queued")

    def test_a_user_who_may_not_file_cannot_call_epo(self):
        user = self.env["res.users"].create({
            "name": "Clerk", "login": "epo_clerk",
            "group_ids": [(6, 0, [self.env.ref(
                "l10n_cssk_submission_base.group_cssk_submission_user").id])],
        })
        with self.assertRaisesRegex(UserError, "allowed to file"):
            self.submission.with_user(user).action_epo_check()

    def test_an_entity_in_the_answer_is_not_expanded(self):
        answer = epo.parse_answer(
            b'<?xml version="1.0"?><!DOCTYPE x [<!ENTITY e "BOOM">]>'
            b'<Chyby><Chyba Typ="K" Zkr="X"><Text>&e;</Text></Chyba></Chyby>')
        self.assertNotIn("BOOM", answer["errors"][0]["text"])
