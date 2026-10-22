import base64

from lxml import etree

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tests.common import TransactionCase


class TestSkEcSales(TransactionCase):
    """Smoke tests for the SK Súhrnný výkaz country layer (run at install)."""

    def test_version_seeded(self):
        version = self.env.ref("l10n_sk_ec_sales.sdv_version_2025")
        self.assertEqual(version.country_id.code, "SK")
        self.assertEqual(version.xml_root_element, "dokument")
        self.assertTrue(version.xml_schema_data, "SDV XSD not loaded")
        self.assertEqual(len(version.statement_type_ids), 3)


@tagged("post_install", "-at_install")
class TestSkEcSalesCompute(AccountTestInvoicingCommon):
    """Functional: post an intra-EU supply, compute + export the Súhrnný výkaz."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # Identification fields the official svdph20 schema needs.
        cls.company.write({
            "vat": "SK2023456787", "city": "Bratislava",
            "country_id": cls.env.ref("base.sk").id,
        })

        # EU customer (Belgium) with a real, valid BE VAT.
        cls.partner_eu = cls.env["res.partner"].create({
            "name": "Kunde BE", "country_id": cls.env.ref("base.be").id,
            "vat": "BE0477472701",
        })
        # Intra-community goods supply tax (0 %), tagged for the EC sales list.
        cls.tax_ic_goods = cls.env["account.tax"].create({
            "name": "Intra-EU goods 0%", "amount": 0.0,
            "amount_type": "percent", "type_tax_use": "sale",
            "company_id": cls.company.id,
            "country_id": cls.company.account_fiscal_country_id.id,
            "tax_group_id": cls.tax_sale_a.tax_group_id.id,
            "cssk_ec_summary_code": "0",
        })
        cls.version = cls.env.ref("l10n_sk_ec_sales.sdv_version_2025")

    def _make_statement(self):
        return self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": "2026-06-01",
            "date_to": "2026-06-30",
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })

    def test_compute_and_export(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(len(st.line_ids), 1)
        line = st.line_ids
        self.assertEqual(line.partner_country_code, "BE")
        self.assertEqual(line.partner_vat, "BE0477472701")
        self.assertEqual(line.transaction_code, "0")
        self.assertAlmostEqual(line.total_amount, 1000.0, places=2)

        # Validates against the OFFICIAL svdph20.xsd (root 'dokument', eForm
        # grid of 12-record pages).
        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "dokument")
        stranas = root.findall(".//telo/strana")
        self.assertEqual(len(stranas), 1)
        zaznamy = stranas[0].findall("zaznam")
        self.assertEqual(len(zaznamy), 12)  # fixed 12-record page
        first = zaznamy[0]
        self.assertEqual(first.findtext("kodStatu"), "BE")
        self.assertEqual(first.findtext("idCislo"), "0477472701")
        self.assertEqual(first.findtext("hodnota"), "1000")  # whole euros (SVDPHv20)
        # goods are reported BEZ KÓDU — kód column is blank (poučenie SVDPHv20),
        # even though the internal grouping/kontrola code stays "0".
        self.assertEqual(first.findtext("kod") or "", "")

    def test_negative_total_rounds_half_up_away_from_zero(self):
        """A negative per-partner total (corrections exceed supplies) must
        round half-up AWAY from zero: −9.70 → −10 in both hodnota and
        celkovaHodnota. The old int(x + 0.5) idiom truncated to −9."""
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[0.30],
            taxes=self.tax_ic_goods, post=True,
        )
        self.init_invoice(
            "out_refund", partner=self.partner_eu,
            invoice_date="2026-06-12", amounts=[10.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(len(st.line_ids), 1)
        self.assertAlmostEqual(st.line_ids.total_amount, -9.70, places=2)

        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        first = root.findall(".//telo/strana/zaznam")[0]
        self.assertEqual(first.findtext("hodnota"), "-10")
        self.assertEqual(root.findtext(".//hlavicka/celkovaHodnota"), "-10")

    def test_preflight_implausible_vat_prefix(self):
        """Master-data preflight: the svdph20 zaznam splits the customer VAT
        into kodStatu + idCislo by its 2-letter prefix — a VAT with an
        implausible prefix blocks the export early, naming the line."""
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        st.line_ids.partner_vat = "QQ0477472701"  # 'QQ' is no country code
        with self.assertRaises(UserError) as cm:
            st.action_export_xml()
        self.assertIn("QQ0477472701", str(cm.exception))
        self.assertEqual(st.state, "preview", "fail-early: nothing exported")

        # EL (Greece) and XI (Northern Ireland) are legitimate VAT prefixes
        # even though they are not ISO country codes — the preflight accepts
        # them (the VIES gate then judges EU membership separately).
        st.line_ids.partner_vat = "EL123456789"
        st._cssk_preflight_export()  # must not raise
        st.line_ids.partner_vat = "XI123456789"
        st._cssk_preflight_export()  # must not raise

    def test_kontroly_kod(self):
        """kód plnenia must be one of {0,1,2}: clean on a goods supply, and an
        invalid code is a hard block (SV_KOD)."""
        self.init_invoice(
            "out_invoice", partner=self.partner_eu,
            invoice_date="2026-06-10", amounts=[1000.0],
            taxes=self.tax_ic_goods, post=True,
        )
        st = self._make_statement()
        st.action_compute_lines()
        self.assertEqual(st.check_kontroly(), [], "kód '0' must be accepted")

        st.line_ids.transaction_code = "9"  # not a valid súhrnný-výkaz kód
        codes = [v["code"] for v in st.check_kontroly()]
        self.assertIn("SV_KOD", codes, "kontroly must reject an invalid kód")
