# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The kind of VAT registration, read from the register of VAT subjects.

No network: the SOAP answer is a synthetic one in the shape of
``StatusNespolehlivySubjektRozsirenyResponse``; the DIČ belongs to nobody.
"""
from unittest.mock import MagicMock, patch

from odoo.tests import TransactionCase, tagged

POST = "odoo.addons.l10n_cz_payment_reliability.models.res_partner.requests.post"
DIC = "87654326"

SUBJECT_RESPONSE = b"""<?xml version="1.0" encoding="utf-8"?>
<soapenv:Envelope xmlns:soapenv="http://schemas.xmlsoap.org/soap/envelope/">
  <soapenv:Header/>
  <soapenv:Body>
    <StatusNespolehlivySubjektRozsirenyResponse xmlns="http://adis.mfcr.cz/rozhraniCRPDPH/">
      <status odpovedGenerovana="2026-11-15" statusCode="0" statusText="OK"/>
      <statusSubjektu typSubjektu="IDENTIFIKOVANA_OSOBA" dic="87654326" nespolehlivyPlatce="NE" cisloFu="13">
        <nazevSubjektu>ZKUSEBNI ODBERATEL S.R.O.</nazevSubjektu>
      </statusSubjektu>
    </StatusNespolehlivySubjektRozsirenyResponse>
  </soapenv:Body>
</soapenv:Envelope>"""


@tagged("post_install", "-at_install")
class TestCzSubjectType(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.partner = cls.env["res.partner"].create({
            "name": "Zkušební odběratel s.r.o.",
            "country_id": cls.env.ref("base.cz").id,
            "vat": "CZ" + DIC,
        })
        cls.has_field = (
            "l10n_cz_vat_registration_category" in cls.env["res.partner"]._fields
        )

    def _mock(self, content=SUBJECT_RESPONSE):
        fake = MagicMock()
        fake.raise_for_status.return_value = None
        fake.content = content
        return patch(POST, return_value=fake)

    def test_the_subject_type_is_read_with_the_v2_operation(self):
        with self._mock() as post:
            self.assertEqual(
                self.partner._cz_adis_subject_type(), "IDENTIFIKOVANA_OSOBA")
        kwargs = post.call_args.kwargs
        self.assertEqual(
            kwargs["headers"]["SOAPAction"],
            "getStatusNespolehlivySubjektRozsirenyV2")
        self.assertIn(
            b"<roz:StatusNespolehlivySubjektRozsirenyV2Request>"
            b"<roz:dic>87654326</roz:dic>", kwargs["data"])

    def test_no_answer_is_none(self):
        import requests

        with patch(POST, side_effect=requests.exceptions.ConnectionError("down")):
            self.assertIsNone(self.partner._cz_adis_subject_type())
        with self._mock(b"<Envelope><Body/></Envelope>"):
            self.assertIsNone(self.partner._cz_adis_subject_type())

    def test_without_the_sibling_module_nothing_is_asked(self):
        if self.has_field:
            self.skipTest("l10n_cz_vat_registration is installed")
        with self._mock() as post:
            self.partner._cz_fill_vat_registration_category()
        post.assert_not_called()

    def test_the_category_is_filled_where_the_sibling_module_is_installed(self):
        if not self.has_field:
            self.skipTest("l10n_cz_vat_registration is not installed")
        with self._mock():
            self.partner._cz_fill_vat_registration_category()
        self.assertEqual(self.partner.l10n_cz_vat_registration_category, "identified")
        self.assertFalse(self.partner.l10n_cz_is_full_vat_payer)

    def test_not_found_does_not_erase_a_category_entered_by_hand(self):
        if not self.has_field:
            self.skipTest("l10n_cz_vat_registration is not installed")
        self.partner.l10n_cz_vat_registration_category = "non_payer"
        answer = SUBJECT_RESPONSE.replace(b"IDENTIFIKOVANA_OSOBA", b"NENALEZEN")
        with self._mock(answer):
            self.partner._cz_fill_vat_registration_category()
        self.assertEqual(self.partner.l10n_cz_vat_registration_category, "non_payer")

    def test_a_foreign_partner_is_not_asked(self):
        if not self.has_field:
            self.skipTest("l10n_cz_vat_registration is not installed")
        self.partner.country_id = self.env.ref("base.sk")
        with self._mock() as post:
            self.partner._cz_fill_vat_registration_category()
        post.assert_not_called()
