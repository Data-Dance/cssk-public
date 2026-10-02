# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import hashlib
import os

from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.addons.l10n_cssk_oss_base.tests.common import OssReturnCommon


@tagged("post_install", "-at_install")
class TestCzOssReturn(OssReturnCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls._oss_setup("CZ25663585", "l10n_cz_oss.cz_oss_version_ossei1")
        cls.de = cls.env.ref("base.de")
        cls.at = cls.env.ref("base.at")
        cls.gr = cls.env.ref("base.gr")
        cls.sk = cls.env.ref("base.sk")

    def test_rows_split_by_state_rate_and_supply_type(self):
        self._oss_invoice(self.de, 100.0, 19.0, "2025-07-10")
        self._oss_invoice(self.de, 50.0, 19.0, "2025-08-10")
        self._oss_invoice(self.de, 20.0, 7.0, "2025-08-11")
        self._oss_invoice(self.at, 200.0, 20.0, "2025-09-12",
                          product=self.service)
        # outside the quarter: must not be counted
        self._oss_invoice(self.de, 999.0, 19.0, "2025-10-01")
        ret = self._oss_return(2025, 3)

        self.assertEqual(len(ret.line_ids), 3)
        de19 = self._row(ret, "DE", 19.0)
        self.assertAlmostEqual(de19.taxable_amount, 150.0)
        self.assertAlmostEqual(de19.vat_amount, 28.5)
        self.assertEqual(de19.rate_type, "standard")
        de7 = self._row(ret, "DE", 7.0)
        self.assertEqual(de7.rate_type, "reduced")
        self.assertAlmostEqual(de7.vat_amount, 1.4)
        at20 = self._row(ret, "AT", 20.0, "services")
        self.assertAlmostEqual(at20.vat_amount, 40.0)
        self.assertAlmostEqual(ret.booked_vat, 69.9)
        self.assertAlmostEqual(ret.total_due, 69.9)

        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")
        root = self._oss_xml(ret)
        self.assertEqual(root.tag, "Pisemnost")
        form = root.find("OSSEI1")
        self.assertEqual(form.get("verzePis"), "01.01.04")
        head = form.find("VetaD")
        self.assertEqual((head.get("quarter"), head.get("year")), ("3", "2025"))
        self.assertEqual(head.get("vat_number"), "25663585")
        self.assertEqual(head.get("trans"), "A")
        self.assertEqual(form.find("VetaP").get("dic"), "25663585")
        rows = {(r.get("state_consumption"), r.get("vat_rate"),
                 r.get("supply_type_code")): r for r in form.findall("VetaR")}
        self.assertEqual(set(rows), {("DE", "19.00", "G"), ("DE", "7.00", "G"),
                                     ("AT", "20.00", "S")})
        self.assertEqual(rows[("DE", "19.00", "G")].get("taxable_amount"),
                         "150.00")
        self.assertEqual(rows[("DE", "19.00", "G")].get("vat_rate_type_code"),
                         "Z")
        self.assertEqual(rows[("DE", "7.00", "G")].get("vat_rate_type_code"),
                         "S")
        self.assertEqual(rows[("AT", "20.00", "S")].get("country"), "CZ")

    def test_greece_is_filed_as_el(self):
        self._oss_invoice(self.gr, 100.0, 24.0, "2025-07-10")
        ret = self._oss_return(2025, 3)
        ret.action_export_xml()
        row = self._oss_xml(ret).find(".//VetaR")
        self.assertEqual(row.get("state_consumption"), "EL")

    def test_credit_note_of_an_earlier_quarter_is_a_correction(self):
        invoice = self._oss_invoice(self.de, 100.0, 19.0, "2025-05-20")
        self._oss_refund(invoice, "2025-08-05")
        self._oss_invoice(self.de, 300.0, 19.0, "2025-08-06")

        q2 = self._oss_return(2025, 2)
        self.assertAlmostEqual(self._row(q2, "DE", 19.0).vat_amount, 19.0)
        self.assertFalse(q2.correction_ids)

        q3 = self._oss_return(2025, 3)
        # the credit note is not netted into Q3's row ...
        self.assertAlmostEqual(self._row(q3, "DE", 19.0).taxable_amount, 300.0)
        # ... but corrects Q2
        corr = q3.correction_ids
        self.assertEqual(len(corr), 1)
        self.assertEqual((corr.year, corr.quarter, corr.member_state_id.code),
                         (2025, "2", "DE"))
        self.assertAlmostEqual(corr.vat_amount, -19.0)
        self.assertAlmostEqual(q3.total_due, 38.0)
        q3.action_export_xml()
        veta_o = self._oss_xml(q3).find(".//VetaO")
        self.assertEqual((veta_o.get("year"), veta_o.get("quarter"),
                          veta_o.get("state_consumption"),
                          veta_o.get("correction")),
                         ("2025", "2", "DE", "-19.00"))

    def test_credit_note_in_the_same_quarter_nets(self):
        invoice = self._oss_invoice(self.de, 100.0, 19.0, "2025-07-02")
        self._oss_refund(invoice, "2025-07-20")
        self._oss_invoice(self.de, 40.0, 19.0, "2025-07-21")
        ret = self._oss_return(2025, 3)
        self.assertFalse(ret.correction_ids)
        self.assertAlmostEqual(self._row(ret, "DE", 19.0).taxable_amount, 40.0)

    def test_czk_invoice_uses_the_ecb_rate_of_the_next_fixing_day(self):
        """Q3 2025 ends on 30. 9.; with no fixing that day, 1. 10. applies.

        The rate proposed from the company table must still be confirmed as
        the ECB rate before the return exports.
        """
        czk = self.company.currency_id
        self.assertEqual(czk.name, "CZK")
        Rate = self.env["res.currency.rate"]
        for day, czk_per_eur in (("2025-09-29", 25.0), ("2025-10-01", 24.5)):
            Rate.create({"currency_id": self.eur.id, "name": day,
                         "company_id": self.company.id,
                         "rate": 1.0 / czk_per_eur})
        self._oss_invoice(self.de, 2450.0, 19.0, "2025-08-10", currency=czk)
        ret = self._oss_return(2025, 3)
        rate = ret.rate_ids
        self.assertEqual(len(rate), 1)
        self.assertEqual(str(rate.fixing_date), "2025-10-01")
        self.assertAlmostEqual(rate.rate, 24.5, places=4)
        self.assertEqual(rate.source, "table")
        self.assertAlmostEqual(self._row(ret, "DE", 19.0).taxable_amount, 100.0)
        with self.assertRaisesRegex(UserError, "ECB reference rate"):
            ret.action_export_xml()
        ret.action_confirm_ecb_rates()
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")

    def test_correction_older_than_three_years_is_refused(self):
        """Q3 2021 was due 31. 10. 2021; its correction period ended
        31. 10. 2024 (CZ § 110zd odst. 3), so a 2025 return cannot carry it."""
        ret = self._oss_return(2025, 1)
        self.env["cssk.oss.return.correction"].create({
            "return_id": ret.id, "is_manual": True, "year": 2021,
            "quarter": "3", "member_state_id": self.de.id,
            "vat_amount": -5.0,
        })
        with self.assertRaisesRegex(UserError, "out of time"):
            ret.action_export_xml()

    def test_nil_return(self):
        ret = self._oss_return(2026, 1)
        self.assertTrue(ret.is_nil)
        ret.action_export_xml()
        form = self._oss_xml(ret).find("OSSEI1")
        self.assertEqual(form.find("VetaD").get("trans"), "N")
        self.assertFalse(form.findall("VetaR"))

    def test_filer_must_have_a_czech_dic(self):
        self.company.with_context(no_vat_validation=True).vat = "SK2022749619"
        ret = self._oss_return(2026, 1)
        with self.assertRaisesRegex(UserError, "DIČ"):
            ret.action_export_xml()

    def test_czech_twelve_percent_maps_to_slovak_five(self):
        """A CZ e-shop selling food or medicines to Slovak consumers."""
        oss_tag = self.env.ref("l10n_eu_oss.tag_oss")
        domestic_12 = self.env["account.tax"].search([
            ("company_id", "=", self.company.id), ("type_tax_use", "=", "sale"),
            ("amount", "=", 12.0),
        ]).filtered(lambda t: not (t.invoice_repartition_line_ids.tag_ids
                                   & oss_tag))
        self.assertTrue(domestic_12)
        sk_five = self._oss_tax(self.sk, 5.0)
        self.assertTrue(sk_five, "no 5 % OSS tax for Slovakia")
        self.assertTrue(sk_five.original_tax_ids & domestic_12)
        sk_std = self._oss_tax(self.sk, 23.0)
        self.assertTrue(sk_std)


@tagged("post_install", "-at_install")
class TestCzOssSchemaPins(TransactionCase):
    """The bundled schema must match data/SCHEMA_VERSION (see that file)."""

    def _pins(self):
        data = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data")
        pins = {}
        with open(os.path.join(data, "SCHEMA_VERSION"), encoding="utf-8") as fh:
            for raw in fh:
                parts = raw.split()
                if len(parts) == 3 and parts[0].endswith(".xsd"):
                    pins[parts[0]] = (parts[1], int(parts[2]))
        return data, pins

    def test_bundled_schemas_match_the_pinned_digests(self):
        data, pins = self._pins()
        self.assertTrue(pins, "SCHEMA_VERSION lists no schemas")
        for name, (digest, size) in pins.items():
            with open(os.path.join(data, name), "rb") as fh:
                blob = fh.read()
            self.assertEqual(len(blob), size, "%s size moved" % name)
            self.assertEqual(hashlib.md5(blob).hexdigest(), digest,
                             "%s does not match its pin" % name)

    def test_every_bundled_schema_is_pinned(self):
        data, pins = self._pins()
        on_disk = {f for f in os.listdir(data) if f.endswith(".xsd")}
        self.assertEqual(on_disk, set(pins),
                         "unpinned schema(s): %s" % sorted(on_disk - set(pins)))

    def test_the_version_carries_the_pinned_schema(self):
        import base64
        version = self.env.ref("l10n_cz_oss.cz_oss_version_ossei1")
        data, pins = self._pins()
        blob = base64.b64decode(version.xml_schema_data)
        self.assertEqual(hashlib.md5(blob).hexdigest(),
                         pins[version.xml_schema_filename][0])
