# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import base64

from lxml import etree

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged
from odoo.tools import date_utils
from odoo.tests.common import TransactionCase


class TestCzEcSalesSeed(TransactionCase):
    def test_version_seeded(self):
        version = self.env.ref("l10n_cz_ec_sales.dphshv_version_2025")
        self.assertEqual(version.country_id.code, "CZ")
        self.assertEqual(version.xml_root_element, "Pisemnost")
        self.assertEqual(len(version.statement_type_ids), 3)


@tagged("post_install", "-at_install")
class TestCzEcSales(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "CZ25663585", "city": "Praha"})
        # EPO requires the competent tax office (c_ufo); assign the seeded one.
        # FÚ pro hl. m. Prahu — seeded by l10n_cz_statutory's hook without an
        # xmlid (the old l10n_cssk_core.cz_ufo_* ids were removed in 1.2.0);
        # look it up by its stable submission code instead.
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.partner_eu = cls.env["res.partner"].create({
            "name": "Kunde BE", "country_id": cls.env.ref("base.be").id,
            "vat": "BE0477472701",
        })
        cls.tax_ic = cls.env["account.tax"].create({
            "name": "Intra-EU goods 0%", "amount": 0.0, "amount_type": "percent",
            "type_tax_use": "sale", "company_id": cls.company.id,
            "country_id": cls.company.account_fiscal_country_id.id,
            "tax_group_id": cls.tax_sale_a.tax_group_id.id,
            "cssk_ec_summary_code": "0",
        })
        cls.version = cls.env.ref("l10n_cz_ec_sales.dphshv_version_2025")

    def _statement(self):
        from odoo import fields
        today = fields.Date.context_today(self.env.user)
        return self.env["cssk.ec.summary.statement"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "date_from": today.replace(day=1),
            "date_to": date_utils.end_of(today, "month"),
            "period_type": "month",
            "statement_type_id": self.version.statement_type_ids[0].id,
        })

    def test_a_nasledne_hlaseni_cancels_with_storno_rows(self):
        """DPHSHV k_storno: a následné hlášení withdraws a filed row with a
        storno row (matched on k_stat, c_vat, k_pln_eu) and reports the
        corrected row anew; unchanged rows are not repeated. It used to
        re-file every row of the period and never wrote a storno."""
        from odoo import fields
        today = fields.Date.context_today(self.env.user)
        de = self.env["res.partner"].create({
            "name": "Kunde DE", "country_id": self.env.ref("base.de").id,
            "vat": "DE811907980"})
        pl = self.env["res.partner"].create({
            "name": "Klient PL", "country_id": self.env.ref("base.pl").id,
            "vat": "PL8942520778"})
        invoices = {}
        for partner, amount in ((self.partner_eu, 1000.0), (de, 500.0),
                                (pl, 300.0)):
            invoices[partner] = self.init_invoice(
                "out_invoice", partner=partner, invoice_date=today,
                amounts=[amount], taxes=self.tax_ic, post=True)
        radne = self._statement()
        radne.action_compute_lines()
        radne.action_export_xml()
        radne.action_submit()

        self.init_invoice(
            "out_invoice", partner=self.partner_eu, invoice_date=today,
            amounts=[200.0], taxes=self.tax_ic, post=True)
        invoices[pl].button_draft()
        invoices[pl].button_cancel()
        nasledne = self.env["cssk.ec.summary.statement"].browse(
            radne.action_create_amendment()["res_id"])
        nasledne.statement_type_id = self.version.statement_type_ids.filtered(
            lambda t: t.code == "E")
        nasledne.action_compute_lines()
        rows = sorted((l.partner_vat, l.is_storno, l.total_amount)
                      for l in nasledne.line_ids)
        self.assertEqual(rows, [
            ("BE0477472701", False, 1200.0),
            ("BE0477472701", True, 0.0),
            ("PL8942520778", True, 0.0),
        ])
        nasledne.action_export_xml()   # validates against dphshv_epo2.xsd
        root = etree.fromstring(base64.b64decode(nasledne.xml_attachment_id.datas))
        vetar = root.findall(".//VetaR")
        self.assertEqual([(v.get("c_vat"), v.get("k_storno"), v.get("pln_hodnota"))
                          for v in vetar],
                         [("0477472701", "A", None), ("0477472701", None, "1200"),
                          ("8942520778", "A", None)])

    def test_compute_and_export(self):
        self.init_invoice(
            "out_invoice", partner=self.partner_eu, amounts=[1000.0],
            taxes=self.tax_ic, post=True,
        )
        st = self._statement()
        st.action_compute_lines()
        self.assertEqual(len(st.line_ids), 1)
        self.assertEqual(st.line_ids.partner_country_code, "BE")
        self.assertEqual(st.line_ids.transaction_code, "0")
        self.assertAlmostEqual(st.line_ids.total_amount, 1000.0, places=2)

        st.action_export_xml()
        self.assertEqual(st.state, "exported")
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        self.assertEqual(etree.QName(root).localname, "Pisemnost")
        vetar = root.findall(".//VetaR")
        self.assertEqual(len(vetar), 1)
        self.assertEqual(vetar[0].get("k_stat"), "BE")
        self.assertEqual(vetar[0].get("c_vat"), "0477472701")
        self.assertEqual(vetar[0].get("pln_hodnota"), "1000")

    def test_filer_block_leaves_out_what_the_form_lacks(self):
        """The souhrnné hlášení's VetaP has no e-mail and no telephone; the
        XSD validation in the export rejects them if they appear."""
        self.company.write({"phone": "+420 511 447 174", "email": "a@b.cz",
                            "street": "Příhon 943", "city": "Čejkovice"})
        self.init_invoice(
            "out_invoice", partner=self.partner_eu, amounts=[1000.0],
            taxes=self.tax_ic, post=True,
        )
        st = self._statement()
        st.action_compute_lines()
        st.action_export_xml()
        veta_p = etree.fromstring(
            base64.b64decode(st.xml_attachment_id.datas)).find(".//VetaP")
        self.assertIsNone(veta_p.get("email"))
        self.assertIsNone(veta_p.get("c_telef"))
        self.assertEqual(veta_p.get("ulice"), "Příhon")
        self.assertEqual(veta_p.get("c_pop"), "943")

    # -- DPHSHV values the XSD cannot check ---------------------------------
    def _partner(self, name, country, vat):
        return self.env["res.partner"].with_context(no_vat_validation=True).create({
            "name": name, "country_id": self.env.ref(country).id, "vat": vat})

    def _export(self, type_code="B"):
        st = self._statement()
        st.statement_type_id = self.version.statement_type_ids.filtered(
            lambda t: t.code == type_code)
        st.action_compute_lines()
        st.action_export_xml()
        return st, etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))

    def test_greece_is_el_and_northern_ireland_is_xi(self):
        """k_stat is the code of the state that issued the VAT number, as the
        DPHSHV table lists it: ŘECKO EL, SEVERNÍ IRSKO XI."""
        gr = self._partner("Pelatis GR", "base.gr", "EL094014201")
        ni = self._partner("Customer NI", "base.uk", "XI123456789")
        for partner in (gr, ni):
            self.init_invoice("out_invoice", partner=partner, amounts=[500.0],
                              taxes=self.tax_ic, post=True)
        st, root = self._export()
        rows = {r.get("k_stat"): r.get("c_vat") for r in root.findall(".//VetaR")}
        self.assertEqual(rows, {"EL": "094014201", "XI": "123456789"})

    def test_a_service_to_northern_ireland_is_refused(self):
        from odoo.exceptions import UserError
        ni = self._partner("Customer NI", "base.uk", "XI123456789")
        tax_srv = self.tax_ic.copy({"name": "EU services 0%",
                                    "cssk_ec_summary_code": "3"})
        self.init_invoice("out_invoice", partner=ni, amounts=[500.0],
                          taxes=tax_srv, post=True)
        with self.assertRaises(UserError) as cm:
            self._export()
        self.assertIn("XI123456789", str(cm.exception))

    def test_value_is_rounded_up_to_whole_crowns(self):
        """"Celková hodnota plnění se zaokrouhlí na celé koruny nahoru." """
        self.init_invoice("out_invoice", partner=self.partner_eu,
                          amounts=[1000.40], taxes=self.tax_ic, post=True)
        st, root = self._export()
        self.assertEqual(root.find(".//VetaR").get("pln_hodnota"), "1001")

    def test_form_is_r_or_n(self):
        """shvies_forma: "R - souhrnné hlášení, N - následné souhrnné
        hlášení" — B / O / E are not values of the structure."""
        forms = dict(self.version.statement_type_ids.mapped(
            lambda t: (t.code, t.fa_xml_value)))
        self.assertEqual(forms, {"B": "R", "O": "N", "E": "N"})
        self.init_invoice("out_invoice", partner=self.partner_eu,
                          amounts=[1000.0], taxes=self.tax_ic, post=True)
        st, root = self._export("B")
        self.assertEqual(root.find(".//VetaD").get("shvies_forma"), "R")


@tagged("post_install", "-at_install")
class TestSchemaPin(TransactionCase):
    """data/SCHEMA_VERSION pins the bundled XSD (digest, size) and the
    structure version, and the template's ``verzePis`` must say the same.
    Nothing local can tell a stale schema from a current one — the pin makes
    a refresh a deliberate change instead of a silent one."""

    def _pin(self):
        import os
        here = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        with open(os.path.join(here, "data", "SCHEMA_VERSION"), encoding="utf-8") as fh:
            lines = [raw.split() for raw in fh]
        return here, lines

    def test_every_bundled_schema_matches_its_pin(self):
        import hashlib
        import os
        here, lines = self._pin()
        pins = {p[0]: (p[1], int(p[2])) for p in lines
                if len(p) == 3 and p[0].endswith(".xsd")}
        on_disk = {f for f in os.listdir(os.path.join(here, "data"))
                   if f.endswith(".xsd")}
        self.assertEqual(on_disk, set(pins), "unpinned or missing schema")
        for name, (digest, size) in pins.items():
            blob = open(os.path.join(here, "data", name), "rb").read()
            self.assertEqual((hashlib.md5(blob).hexdigest(), len(blob)),
                             (digest, size), "%s moved without its pin" % name)

    def test_the_template_declares_the_pinned_structure_version(self):
        import os
        here, lines = self._pin()
        version = [p[1] for p in lines if len(p) >= 2 and p[0].isupper()
                   and not p[0].endswith(".xsd")][0]
        template = open(os.path.join(here, "report/l10n_cz_ec_sales_templates.xml"), encoding="utf-8").read()
        self.assertIn('verzePis="%s"' % version, template)
