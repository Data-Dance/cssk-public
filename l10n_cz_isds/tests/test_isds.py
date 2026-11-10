# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The data box client: every request validates against the operator's
schema (dmBaseTypes.xsd / dbTypes.xsd 3.11, bundled under tests/data), and
the answers are read from SOAP envelopes shaped like the operator's."""
import base64
import os
import ssl
import stat
from datetime import datetime, timedelta, timezone
from pathlib import Path
from unittest.mock import MagicMock, patch

import requests
from cryptography import x509
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from cryptography.hazmat.primitives.serialization import pkcs12
from cryptography.x509.oid import NameOID
from lxml import etree

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from ..lib import isds

DATA = Path(__file__).parent / "data"
NS = isds.NS


def _schema(name):
    return etree.XMLSchema(etree.parse(str(DATA / name)))


def soap(inner):
    return ('<?xml version="1.0" encoding="UTF-8"?>'
            '<SOAP-ENV:Envelope xmlns:SOAP-ENV="%s"><SOAP-ENV:Body>%s'
            '</SOAP-ENV:Body></SOAP-ENV:Envelope>' % (isds.NS_SOAP, inner)
            ).encode()


def status(code="0000", message="Provedeno úspěšně.", tag="dmStatus"):
    return "<p:%s><p:%sCode>%s</p:%sCode><p:%sMessage>%s</p:%sMessage></p:%s>" % (
        tag, tag, code, tag, tag, message, tag, tag)


def make_p12(password=b"pw"):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, "Odoo app")])
    now = datetime.now(timezone.utc)
    cert = (x509.CertificateBuilder().subject_name(name).issuer_name(name)
            .public_key(key.public_key())
            .serial_number(x509.random_serial_number())
            .not_valid_before(now - timedelta(days=1))
            .not_valid_after(now + timedelta(days=30))
            .sign(key, hashes.SHA256()))
    return pkcs12.serialize_key_and_certificates(
        b"app", key, cert, None,
        serialization.BestAvailableEncryption(password))


def response(status_code=200, content=b""):
    r = MagicMock()
    r.status_code = status_code
    r.content = content
    return r


@tagged("post_install", "-at_install")
class TestIsdsLib(TransactionCase):
    def test_requests_follow_the_schema(self):
        dm = _schema("dmBaseTypes.xsd")
        for element in (
            isds.create_message("9tsaf6s", "Podani CSSZ_JMHZ", [
                ("JMHZ.xml", b"<jmhz/>", "application/xml"),
                ("extra.xml", b"<x/>", "application/xml")],
                sender_ref="SUB/0001"),
            isds.list_received(datetime(2027, 2, 1), datetime(2027, 2, 8)),
            isds.message_download("12345678"),
        ):
            dm.assertValid(etree.fromstring(etree.tostring(element)))
        _schema("dbTypes.xsd").assertValid(
            etree.fromstring(etree.tostring(isds.owner_info())))

    def test_create_message_carries_the_files(self):
        element = isds.create_message("iie254d", "x", [
            ("JMHZ.xml", b"<jmhz/>", "application/xml")])
        f = element.find("{%s}dmFiles/{%s}dmFile" % (NS, NS))
        self.assertEqual(f.get("dmFileMetaType"), "main")
        self.assertEqual(base64.b64decode(f.findtext(
            "{%s}dmEncodedContent" % NS)), b"<jmhz/>")
        self.assertEqual(element.findtext(
            "{%s}dmEnvelope/{%s}dbIDRecipient" % (NS, NS)), "iie254d")

    def test_answers(self):
        p = 'xmlns:p="%s"' % NS
        self.assertEqual(isds.parse_create(soap(
            '<p:CreateMessageResponse %s><p:dmID>4711</p:dmID>%s'
            '</p:CreateMessageResponse>' % (p, status()))), "4711")
        with self.assertRaisesRegex(isds.IsdsError, "1214") as cm:
            isds.parse_create(soap(
                '<p:CreateMessageResponse %s>%s</p:CreateMessageResponse>'
                % (p, status("1214", "Adresát neexistuje"))))
        self.assertEqual(cm.exception.code, "1214")
        listing = isds.parse_list(soap(
            '<p:GetListOfReceivedMessagesResponse %s><p:dmRecords>'
            '<p:dmRecord><p:dmID>99</p:dmID><p:dbIDSender>5ffu6xk'
            '</p:dbIDSender><p:dmAnnotation>ČSSZ - Odpověď na e-Podání. '
            '[CSSZ_JMHZ-ABC-4711]</p:dmAnnotation></p:dmRecord>'
            '</p:dmRecords>%s</p:GetListOfReceivedMessagesResponse>'
            % (p, status())))
        self.assertEqual(listing[0]["id"], "99")
        self.assertIn("4711", listing[0]["annotation"])
        message = isds.parse_download(soap(
            '<p:MessageDownloadResponse %s><p:dmReturnedMessage><p:dmDm>'
            '<p:dmID>99</p:dmID><p:dmAnnotation>a</p:dmAnnotation>'
            '<p:dmFiles><p:dmFile dmMimeType="application/xml" '
            'dmFileMetaType="main" dmFileDescr="protokol.xml">'
            '<p:dmEncodedContent>%s</p:dmEncodedContent></p:dmFile>'
            '</p:dmFiles></p:dmDm></p:dmReturnedMessage>%s'
            '</p:MessageDownloadResponse>' % (
                p, base64.b64encode(b"<r/>").decode(), status())))
        self.assertEqual(message["files"], [
            ("protokol.xml", b"<r/>", "application/xml")])
        owner = isds.parse_owner(soap(
            '<p:GetOwnerInfoFromLoginResponse %s><p:dbOwnerInfo>'
            '<p:dbID>abc1234</p:dbID><p:firmName>Firma s.r.o.</p:firmName>'
            '</p:dbOwnerInfo>%s</p:GetOwnerInfoFromLoginResponse>'
            % (p, status(tag="dbStatus"))))
        self.assertEqual(owner, {"box": "abc1234", "name": "Firma s.r.o."})

    def test_certificate_sign_in(self):
        certificate = isds.load_p12(make_p12(), "pw")
        ok = soap('<p:GetOwnerInfoFromLoginResponse xmlns:p="%s">'
                  '<p:dbOwnerInfo><p:dbID>abc1234</p:dbID></p:dbOwnerInfo>%s'
                  '</p:GetOwnerInfoFromLoginResponse>'
                  % (NS, status(tag="dbStatus")))
        files, seen = [], {}
        real_mkstemp = isds.tempfile.mkstemp

        def mkstemp(*args, **kwargs):
            fd, path = real_mkstemp(*args, **kwargs)
            files.append(path)
            return fd, path

        real_load = ssl.SSLContext.load_cert_chain

        def load(context, path, *args, **kwargs):
            # On disk the key is encrypted, and readable by this process only.
            seen["pem"] = open(path, "rb").read()
            seen["mode"] = stat.S_IMODE(os.stat(path).st_mode)
            return real_load(context, path, *args, **kwargs)

        def post(url, **kwargs):
            seen.update(url=url, auth=kwargs["auth"],
                        redirects=kwargs["allow_redirects"],
                        on_disk=[f for f in files if os.path.exists(f)])
            return response(200, ok)

        system = isds.Client("test", auth="system_cert",
                             certificate=certificate)
        with patch.object(isds.tempfile, "mkstemp", side_effect=mkstemp), \
                patch.object(ssl.SSLContext, "load_cert_chain", load), \
                patch.object(isds.requests.Session, "post", side_effect=post):
            system.owner()
        self.assertEqual(
            seen["url"], "https://ws1c.datovka-test.gov.cz/cert/DS/DsManage")
        self.assertIsNone(seen["auth"])
        self.assertFalse(seen["redirects"])
        self.assertIn(b"ENCRYPTED PRIVATE KEY", seen["pem"])
        self.assertEqual(seen["mode"], 0o600)
        # Loaded and gone before the request went out.
        self.assertEqual(seen["on_disk"], [])
        self.assertTrue(files)
        user = isds.Client("production", "login", "secret",
                           auth="password_cert", certificate=certificate)
        with patch.object(isds.requests.Session, "post", side_effect=post):
            user.owner()
        self.assertEqual(
            seen["url"], "https://ws1c.datovka.gov.cz/certds/DS/DsManage")
        self.assertEqual(seen["auth"], ("login", "secret"))
        with self.assertRaises(ValueError):
            isds.Client("test", auth="system_cert")
        # A refused handshake: nothing went out.
        with patch.object(isds.requests.Session, "post",
                          side_effect=requests.exceptions.SSLError("bad")):
            with self.assertRaises(isds.IsdsError) as cm:
                system.send("9tsaf6s", "a", [("a.xml", b"<a/>",
                                              "application/xml")])
        self.assertEqual(cm.exception.code, "TLS")
        self.assertFalse(cm.exception.maybe_sent)
        # A redirect is not followed.
        with patch.object(isds.requests.Session, "post",
                          return_value=response(302, b"")):
            with self.assertRaisesRegex(isds.IsdsError, "redirect"):
                system.owner()

    def test_received_pages_through(self):
        client = isds.Client("test", "login", "secret")
        pages = [[{"id": str(i)} for i in range(3)],
                 [{"id": str(i)} for i in range(3, 6)], [{"id": "6"}]]
        with patch.object(isds.Client, "_post", return_value=b""), \
                patch.object(isds, "parse_list", side_effect=pages) as parse:
            got = client.received(datetime(2027, 2, 1), datetime(2027, 2, 8),
                                  page=3)
        self.assertEqual([r["id"] for r in got], [str(i) for i in range(7)])
        self.assertEqual(parse.call_count, 3)

    def test_a_soap_fault_is_an_error(self):
        with self.assertRaisesRegex(isds.IsdsError, "boom"):
            isds.parse_create(soap(
                '<SOAP-ENV:Fault><faultcode>x</faultcode><faultstring>boom'
                '</faultstring></SOAP-ENV:Fault>'))

    def test_transport(self):
        client = isds.Client("test", "login", "secret")
        p = 'xmlns:p="%s"' % NS
        ok = soap('<p:CreateMessageResponse %s><p:dmID>4711</p:dmID>%s'
                  '</p:CreateMessageResponse>' % (p, status()))
        with patch.object(isds.requests.Session, "post",
                          return_value=response(200, ok)) as post:
            self.assertEqual(client.send("9tsaf6s", "a", [
                ("a.xml", b"<a/>", "application/xml")]), "4711")
        self.assertEqual(post.call_args.args[0],
                         "https://ws1.datovka-test.gov.cz/DS/dz")
        self.assertEqual(post.call_args.kwargs["auth"], ("login", "secret"))
        with patch.object(isds.requests.Session, "post",
                          return_value=response(401, b"")):
            with self.assertRaisesRegex(isds.IsdsError, "refused the sign-in"):
                client.owner()
        # A message may have been created when the answer never came.
        with patch.object(isds.requests.Session, "post",
                          side_effect=requests.ReadTimeout("slow")):
            with self.assertRaises(isds.IsdsError) as cm:
                client.send("9tsaf6s", "a", [("a.xml", b"<a/>",
                                              "application/xml")])
        self.assertTrue(cm.exception.maybe_sent)
        self.assertFalse(cm.exception.retryable)
        with patch.object(isds.requests.Session, "post",
                          side_effect=requests.ConnectTimeout("down")):
            with self.assertRaises(isds.IsdsError) as cm:
                client.send("9tsaf6s", "a", [("a.xml", b"<a/>",
                                              "application/xml")])
        self.assertFalse(cm.exception.maybe_sent)
        self.assertTrue(cm.exception.retryable)


@tagged("post_install", "-at_install")
class TestIsdsCompany(TransactionCase):
    def test_test_connection_records_the_box(self):
        company = self.env.company
        with self.assertRaisesRegex(UserError, "no data box login"):
            company._l10n_cz_isds_client()
        company.sudo().write({"l10n_cz_isds_login": "u",
                              "l10n_cz_isds_password": "p"})
        p = 'xmlns:p="%s"' % NS
        answer = soap(
            '<p:GetOwnerInfoFromLoginResponse %s><p:dbOwnerInfo>'
            '<p:dbID>abc1234</p:dbID><p:firmName>Firma s.r.o.</p:firmName>'
            '</p:dbOwnerInfo>%s</p:GetOwnerInfoFromLoginResponse>'
            % (p, status(tag="dbStatus")))
        with patch.object(isds.requests.Session, "post",
                          return_value=response(200, answer)):
            company.action_l10n_cz_isds_test()
        self.assertEqual(company.sudo().l10n_cz_isds_box_id, "abc1234")

    def test_system_certificate(self):
        company = self.env.company.sudo()
        company.write({"l10n_cz_isds_auth": "system_cert",
                       "l10n_cz_isds_login": False,
                       "l10n_cz_isds_password": False})
        with self.assertRaisesRegex(UserError, "no data box certificate"):
            company._l10n_cz_isds_client()
        company.write({"l10n_cz_isds_p12": base64.b64encode(make_p12()),
                       "l10n_cz_isds_p12_password": "pw"})
        self.assertIn("Odoo app", company.l10n_cz_isds_cert_subject)
        self.assertTrue(company.l10n_cz_isds_cert_valid_to)
        client = company._l10n_cz_isds_client()
        self.assertIsNone(client.auth)
        self.assertTrue(client.host.endswith("/cert"))
        # A certificate that cannot be opened is refused when it is saved.
        with self.assertRaisesRegex(UserError, "cannot be opened"):
            company.l10n_cz_isds_p12_password = "wrong"
