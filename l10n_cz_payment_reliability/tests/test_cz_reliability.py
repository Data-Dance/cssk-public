# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

POST = "odoo.addons.l10n_cz_payment_reliability.models.res_partner.requests.post"

ADIS_RESPONSE = b"""<?xml version="1.0"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Body>
    <StatusNespolehlivyPlatceResponse xmlns="http://adis.mfcr.cz/rozhraniCRPDPH/">
      <status statusCode="0" statusText="OK"/>
      <statusPlatceDPH dic="25663585" nespolehlivyPlatce="NE">
        <zverejneneUcty>
          <ucet datumZverejneni="2013-04-01">
            <standardniUcet predcisli="0" cislo="2000145399" kodBanky="0800"/>
          </ucet>
        </zverejneneUcty>
      </statusPlatceDPH>
    </StatusNespolehlivyPlatceResponse>
  </soapenv:Body>
</soapenv:Envelope>"""


@tagged("post_install", "-at_install")
class TestCzReliability(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "CZ Supplier", "country_id": cls.env.ref("base.cz").id,
            "vat": "CZ25663585"})

    def _mock(self):
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.content = ADIS_RESPONSE
        return patch(POST, return_value=fake)

    def test_reliability_mapped(self):
        with self._mock():
            self.assertEqual(self.partner._cssk_get_tax_reliability(), "reliable")

    def test_registered_account_is_iban(self):
        with self._mock():
            accounts = self.partner._cssk_get_registered_accounts()
        self.assertEqual(len(accounts), 1)
        iban = accounts[0]
        self.assertTrue(iban.startswith("CZ") and len(iban) == 24)
        self.assertIn("0800", iban)  # bank code

    def test_iban_conversion_passes_mod97(self):
        iban = self.env["res.partner"]._cz_account_to_iban("0", "2000145399", "0800")
        rearranged = iban[4:] + iban[:4]
        numeric = "".join(
            str(int(c, 36)) if c.isalpha() else c for c in rearranged)
        self.assertEqual(int(numeric) % 97, 1)  # valid IBAN check digits

    def test_unreliable_mapped(self):
        resp = ADIS_RESPONSE.replace(b'nespolehlivyPlatce="NE"',
                                     b'nespolehlivyPlatce="ANO"')
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.content = resp
        with patch(POST, return_value=fake):
            self.assertEqual(self.partner._cssk_get_tax_reliability(), "unreliable")

    def test_network_error_returns_none(self):
        import requests as _r
        with patch(POST, side_effect=_r.exceptions.ConnectionError("boom")):
            self.assertIsNone(self.partner._cssk_get_tax_reliability())
            self.assertIsNone(self.partner._cssk_get_registered_accounts())

    # ------------------------------------------------------------------
    # Hardening regressions
    # ------------------------------------------------------------------

    def test_dic_is_escaped_in_soap_envelope(self):
        """A crafted VAT must not inject XML into the ADIS request."""
        from lxml import etree
        self.partner.with_context(no_vat_validation=True).write(
            {"vat": 'CZ123</roz:dic><injected attr="&x"/>'}
        )
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.content = ADIS_RESPONSE
        with patch(POST, return_value=fake) as mock_post:
            self.partner._cz_adis_status()
        body = mock_post.call_args.kwargs["data"]
        # The envelope stays well-formed XML: no element was injected and the
        # (sanitized) dic round-trips intact as text.
        root = etree.fromstring(body)
        self.assertEqual(
            [etree.QName(el).localname for el in root.iter()],
            ["Envelope", "Body", "StatusNespolehlivyPlatceRequest", "dic"],
        )
        dic_el = root.iter().__next__().find(".//{*}dic")
        self.assertEqual(dic_el.text, self.partner._cz_adis_dic())
        self.assertIn("<", dic_el.text)  # the payload really was hostile

    def test_adis_dic_normalisation(self):
        """_cz_adis_dic goes through the shared normalize_vat: tabs / NBSP /
        inner spaces and lowercase no longer leak into the SOAP dic, and only
        the CZ prefix is stripped (a foreign VAT passes through verbatim)."""
        p = self.env["res.partner"].create({"name": "Messy VAT"})
        p.with_context(no_vat_validation=True).write(
            {"vat": "cz\t25 663 585"})
        self.assertEqual(p._cz_adis_dic(), "25663585")
        p.with_context(no_vat_validation=True).write({"vat": "sk 2020 317 068"})
        self.assertEqual(p._cz_adis_dic(), "SK2020317068")
        p.with_context(no_vat_validation=True).write({"vat": False})
        self.assertEqual(p._cz_adis_dic(), "")

    def test_response_entities_not_resolved(self):
        """An (external) entity in the ADIS response must not be resolved
        (XXE) and must not break the parse of the rest of the response."""
        resp = (
            b'<?xml version="1.0"?>\n'
            b'<!DOCTYPE Envelope [<!ENTITY xxe SYSTEM "file:///etc/passwd">]>\n'
            b'<soapenv:Envelope'
            b' xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">'
            b"<soapenv:Body>"
            b'<StatusNespolehlivyPlatceResponse'
            b' xmlns="http://adis.mfcr.cz/rozhraniCRPDPH/">'
            b'<statusPlatceDPH dic="25663585" nespolehlivyPlatce="NE">'
            b"<zverejneneUcty><ucet>"
            b'<standardniUcet predcisli="0" cislo="2000145399" kodBanky="0800"/>'
            b"</ucet></zverejneneUcty>"
            b"<poznamka>&xxe;</poznamka>"
            b"</statusPlatceDPH>"
            b"</StatusNespolehlivyPlatceResponse>"
            b"</soapenv:Body></soapenv:Envelope>"
        )
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.content = resp
        with patch(POST, return_value=fake):
            self.assertEqual(
                self.partner._cssk_get_tax_reliability(), "reliable"
            )
            accounts = self.partner._cssk_get_registered_accounts()
        # The unresolved entity node is skipped, the accounts still parse.
        self.assertEqual(len(accounts), 1)
        self.assertTrue(accounts[0].startswith("CZ"))

    def test_combined_check_is_single_roundtrip(self):
        """One reliability check = ONE ADIS SOAP call for both answers."""
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.content = ADIS_RESPONSE
        with patch(POST, return_value=fake) as mock_post:
            accounts, reliability = self.partner._cssk_get_reliability_data()
        self.assertEqual(mock_post.call_count, 1)
        self.assertEqual(reliability, "reliable")
        self.assertEqual(len(accounts), 1)
        self.assertTrue(accounts[0].startswith("CZ"))
