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


@tagged("post_install", "-at_install")
class TestCzAccountForms(TransactionCase):
    """The account on the bill is compared in the form ADIS publishes."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "CZ Supplier", "country_id": cls.env.ref("base.cz").id,
            "vat": "CZ25663585"})

    def _verdict(self, acc_number, response=ADIS_RESPONSE):
        bank = self.env["res.partner.bank"].create({
            "acc_number": acc_number, "partner_id": self.partner.id})
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.content = response
        with patch(POST, return_value=fake):
            return self.partner._cssk_reliability_verdict(bank)

    def test_a_domestic_account_matches_its_published_iban(self):
        for acc in ("2000145399/0800", "0-2000145399/0800", "000000-2000145399/0800"):
            vals, warnings = self._verdict(acc)
            self.assertEqual(vals["cssk_bank_acc_status"], "registered", acc)
            self.assertFalse(warnings)
            self.env["res.partner.bank"].search(
                [("partner_id", "=", self.partner.id)]).unlink()

    def test_another_domestic_account_is_still_not_registered(self):
        vals, warnings = self._verdict("19-2000145399/0800")
        self.assertEqual(vals["cssk_bank_acc_status"], "not_registered")
        self.assertTrue(warnings)

    def test_a_subject_that_is_no_vat_payer_is_not_reported_unregistered(self):
        """NENALEZEN: not a plátce, so there are no accounts to publish and
        § 109 does not apply. It used to read as NOT registered."""
        response = ADIS_RESPONSE.replace(
            b'nespolehlivyPlatce="NE"', b'nespolehlivyPlatce="NENALEZEN"'
        ).replace(
            b'<standardniUcet predcisli="0" cislo="2000145399" kodBanky="0800"/>', b"")
        vals, warnings = self._verdict("2000145399/0800", response)
        self.assertEqual(vals["cssk_bank_acc_status"], "not_vat_payer")
        self.assertEqual(vals["cssk_supplier_reliability"], "not_vat_payer")
        self.assertFalse(warnings)

    def test_a_payer_that_published_nothing_is_told_so(self):
        response = ADIS_RESPONSE.replace(
            b'<standardniUcet predcisli="0" cislo="2000145399" kodBanky="0800"/>', b"")
        vals, warnings = self._verdict("2000145399/0800", response)
        self.assertEqual(vals["cssk_bank_acc_status"], "not_registered")
        self.assertIn("published no bank account", warnings[0])

    def test_the_contact_keeps_its_rating(self):
        self._verdict("2000145399/0800")
        self.assertEqual(self.partner.cssk_tax_reliability, "reliable")
        self.assertTrue(self.partner.cssk_reliability_checked_on)
