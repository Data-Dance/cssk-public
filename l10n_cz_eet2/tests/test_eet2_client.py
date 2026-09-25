# -*- coding: utf-8 -*-
"""Hermetic tests for the EET 2.0 client library (no network, throwaway cert)."""
import base64

from lxml import etree
from cryptography import x509
from cryptography.x509.oid import NameOID
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa
from cryptography.hazmat.primitives.serialization import pkcs12

from odoo.tests.common import TransactionCase

from ..lib import eet2_client as e


def _throwaway_p12(password=b"pw"):
    import datetime
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    subject = issuer = x509.Name([
        x509.NameAttribute(NameOID.COUNTRY_NAME, "CZ"),
        x509.NameAttribute(NameOID.COMMON_NAME, "CZ00000019"),
    ])
    now = datetime.datetime(2026, 7, 1, tzinfo=datetime.timezone.utc)
    cert = (x509.CertificateBuilder()
            .subject_name(subject).issuer_name(issuer)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now)
            .not_valid_after(now + datetime.timedelta(days=366))
            .sign(key, hashes.SHA256()))
    return pkcs12.serialize_key_and_certificates(
        b"eet", key, cert, None,
        serialization.BestAvailableEncryption(password)), password


class TestEet2Client(TransactionCase):

    def test_fmt_amount(self):
        f = self.env["l10n.cz.eet2.transaction"]._fmt_amount
        self.assertEqual(f(188580.0), "188580.00")
        self.assertEqual(f(0.0), "0.00")
        self.assertEqual(f(-0.0), "0.00")      # -0.00 forbidden by the mask
        self.assertEqual(f(-187.2), "-187.20")
        self.assertEqual(f(0.56), "0.56")

    def test_build_and_selfverify(self):
        p12, pw = _throwaway_p12()
        cert = e.Certificate(p12, pw)
        trzba = e.Trzba(
            eic_popl="CZ00000019", id_jednotky=303, id_pokl="/5604/MA65",
            porad_cis="00/2224/SO57", dat_trzby="2026-07-01T09:02:18Z",
            celk_trzba="188580.00", urceno_cerp_zuct="25.00", cerp_zuct="302.00",
            overeni=True)
        env = e.build_signed_request(trzba, cert)
        self.assertLess(len(env), 12 * 1024, "message must stay under the 12 kB cap")

        root = etree.fromstring(env)
        body = root.find(".//{%s}Body" % e.NS["soapenv"])
        si = root.find(".//{%s}SignedInfo" % e.NS["ds"])
        dv = root.find(".//{%s}DigestValue" % e.NS["ds"]).text
        sv = root.find(".//{%s}SignatureValue" % e.NS["ds"]).text

        # DigestValue matches the exclusive-C14N of the Body
        got = base64.b64encode(e._sha256(e._c14n(body, ["v4"]))).decode()
        self.assertEqual(got, dv)
        # SignatureValue verifies against SignedInfo with the leaf public key
        cert.cert.public_key().verify(
            base64.b64decode(sv), e._c14n(si, ["soapenv", "v4"]),
            padding.PKCS1v15(), hashes.SHA256())

    def test_optional_attrs_dropped(self):
        trzba = e.Trzba(
            eic_popl="CZ00000019", id_jednotky=5, id_pokl="P1", porad_cis="1",
            dat_trzby="2026-07-01T09:02:18Z", celk_trzba="1.00")
        attrs = trzba.data_attrs()
        # empty-valued attributes are forbidden -> optionals must be absent
        self.assertNotIn("eic_poverujiciho", attrs)
        self.assertNotIn("cerp_zuct", attrs)
        self.assertNotIn("overeni", trzba.hlavicka_attrs())

    def test_parse_ack_error_warning(self):
        ack = b"""<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
        <soapenv:Body><eet:Odpoved xmlns:eet="http://fs.gov.cz/eet/schema/v4">
        <eet:Hlavicka uuid_zpravy="u" dat_prij="2027-03-04T18:25:21+01:00"/>
        <eet:Potvrzeni pok="b3a09b52-7c87-4014-a496-4c7a53cf9125-03"/>
        </eet:Odpoved></soapenv:Body></soapenv:Envelope>"""
        odp = e.parse_response(ack)
        self.assertTrue(odp.ok)
        self.assertEqual(odp.pok, "b3a09b52-7c87-4014-a496-4c7a53cf9125-03")

        err = b"""<S:Envelope xmlns:S="http://schemas.xmlsoap.org/soap/envelope/">
        <S:Body><eet:Odpoved xmlns:eet="http://fs.gov.cz/eet/schema/v4">
        <eet:Hlavicka dat_odmit="2027-03-04T18:25:21+01:00"/>
        <eet:Chyba kod="-1">Docasna technicka chyba</eet:Chyba>
        </eet:Odpoved></S:Body></S:Envelope>"""
        odp = e.parse_response(err)
        self.assertFalse(odp.ok)
        self.assertTrue(odp.retry)
        self.assertEqual(odp.chyba_kod, -1)
