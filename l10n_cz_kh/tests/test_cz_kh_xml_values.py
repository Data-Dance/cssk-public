# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Element values of the exported DPHKH1, for representative documents.

Every assertion reads the XML that ``action_export_xml`` produced — which is
validated against the official DPHKH1 XSD on the way out — because that is the
artefact that is filed. The XSD cannot see any of these errors: every value
below was schema-valid while it was wrong.
"""

import base64
import datetime

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzKhXmlValues(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        Partner = cls.env["res.partner"].with_context(no_vat_validation=True)
        cls.cz_partner = Partner.create({
            "name": "Odběratel CZ", "country_id": cls.env.ref("base.cz").id,
            "vat": "CZ46342958"})
        cls.de_partner = Partner.create({
            "name": "Kunde DE", "country_id": cls.env.ref("base.de").id,
            "vat": "DE284625197"})
        cls.gr_partner = Partner.create({
            "name": "Promitheftis GR", "country_id": cls.env.ref("base.gr").id,
            "vat": "EL094014201"})
        cls.us_partner = Partner.create({
            "name": "Vendor US", "country_id": cls.env.ref("base.us").id})
        cls.version = cls.env.ref("l10n_cz_kh.cz_kh_version_2025")
        cls.day = datetime.date.today()

    # ------------------------------------------------------------------
    def _tax(self, xmlid):
        tax = self.env["account.chart.template"].with_company(self.company).ref(
            xmlid, raise_if_not_found=False)
        self.assertTrue(tax, "l10n_cz ships %s" % xmlid)
        return tax

    def _move(self, move_type, partner, lines, day=None, ref=None):
        move = self.env["account.move"].create({
            "move_type": move_type, "partner_id": partner.id,
            "invoice_date": day or self.day, "ref": ref,
            # Pinned rather than derived: a past invoice date alone left the
            # accounting date / tax point outside the period under test.
            "date": day or self.day, "taxable_supply_date": day or self.day,
            "invoice_line_ids": [
                Command.create({
                    "name": "line", "quantity": 1, "price_unit": amount,
                    "tax_ids": [Command.set(tax.ids)],
                    **({"product_id": product.id} if product else {}),
                })
                for amount, tax, product in lines
            ],
        })
        move.action_post()
        return move

    def _export(self, day=None):
        day = day or self.day
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": day.replace(day=1),
            "date_to": (day.replace(day=28) + datetime.timedelta(days=4)).replace(
                day=1) - datetime.timedelta(days=1),
            "period_type": "month",
            "statement_type_id": self.env.ref("l10n_cz_kh.cz_kh_type_B").id,
        })
        st.action_compute_lines()
        st.action_export_xml()
        return st, etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))

    def _product(self, code):
        return self.env["product.product"].create({
            "name": "Kód %s" % code, "cssk_kh_commodity_code": code})

    # ------------------------------------------------------------------
    # 1. VetaC totals
    # ------------------------------------------------------------------
    def test_vetac_totals_follow_the_structure(self):
        """pln_rez_pren is A.1, rez_pren23/rez_pren5 are B.1 by rate, and
        celk_zd_a2 is the whole of A.2 — all three used to be crossed or
        partial: A.1 was written as rez_pren23 and B.1 as pln_rez_pren,
        rez_pren5 was never written and celk_zd_a2 held only A.2's standard
        rate."""
        rc_sale = self._tax("l10n_cz_tax_reverse_charge_mode")
        rc21 = self._tax("l10n_cz_21_tax_reverse_charge_scheme")
        rc12 = self._tax("l10n_cz_12_tax_reverse_charge_scheme")
        eu21 = self._tax("l10n_cz_21_acquisition_goods_eu")
        eu12 = self._tax("l10n_cz_12_purchase_goods_eu")
        self.assertTrue(rc21.cssk_control_is_reverse_charge)
        code4 = self._product("4")
        self._move("out_invoice", self.cz_partner, [(30000.0, rc_sale, code4)])
        self._move("in_invoice", self.cz_partner,
                   [(20000.0, rc21, code4), (5000.0, rc12, code4)], ref="PDP-1")
        self._move("in_invoice", self.de_partner,
                   [(40000.0, eu21, None), (7000.0, eu12, None)], ref="EU-1")
        st, root = self._export()

        a1 = root.findall(".//VetaA1")
        self.assertEqual(len(a1), 1, "the 0 % RC sale tax reaches A.1")
        self.assertEqual(a1[0].get("zakl_dane1"), "30000",
                         "A.1 base is rate-less: the 0 % RC base belongs in it")
        self.assertEqual(a1[0].get("kod_pred_pl"), "4")

        c = root.find(".//VetaC")
        self.assertEqual(c.get("pln_rez_pren"), "30000", "A.1 total -> ř. 25")
        self.assertEqual(c.get("rez_pren23"), "20000", "B.1 standard -> ř. 10")
        self.assertEqual(c.get("rez_pren5"), "5000", "B.1 reduced -> ř. 11")
        self.assertEqual(c.get("celk_zd_a2"), "47000",
                         "A.2 total of every rate -> ř. 3, 4, 5, 6, 9, 12, 13")

        a2 = root.find(".//VetaA2")
        self.assertEqual(a2.get("zakl_dane1"), "40000")
        self.assertEqual(a2.get("zakl_dane2"), "7000")

    # ------------------------------------------------------------------
    # 2. second reduced rate (zakl_dane3 / dan3) for DPPD <= 31. 12. 2023
    # ------------------------------------------------------------------
    def test_second_reduced_rate_goes_to_zakl_dane3(self):
        tax21 = self._tax("l10n_cz_21_domestic_supplies")
        tax15 = tax21.copy({"name": "15% G (2023)", "amount": 15.0})
        tax10 = tax21.copy({"name": "10% G (2023)", "amount": 10.0})
        day = datetime.date(2023, 6, 15)
        self._move("out_invoice", self.cz_partner, [
            (20000.0, tax21, None), (10000.0, tax15, None),
            (8000.0, tax10, None)], day=day)
        # and one small document for the aggregate
        self._move("out_invoice", self.cz_partner, [(1000.0, tax10, None)],
                   day=day)
        st, root = self._export(day)
        a4 = root.find(".//VetaA4")
        self.assertEqual(a4.get("zakl_dane1"), "20000")
        self.assertEqual(a4.get("zakl_dane2"), "10000",
                         "first reduced rate (15 %) stays in zakl_dane2")
        self.assertEqual(a4.get("dan2"), "1500")
        self.assertEqual(a4.get("zakl_dane3"), "8000",
                         "second reduced rate (10 %) is zakl_dane3")
        self.assertEqual(a4.get("dan3"), "800")
        a5 = root.find(".//VetaA5")
        self.assertEqual(a5.get("zakl_dane3"), "1000")
        self.assertEqual(a5.get("zakl_dane2"), "0")
        c = root.find(".//VetaC")
        self.assertEqual(c.get("obrat23"), "20000")
        self.assertEqual(c.get("obrat5"), "19000",
                         "ř. 2 carried both reduced rates until 2023")

    def test_no_zakl_dane3_without_a_second_reduced_rate(self):
        tax21 = self._tax("l10n_cz_21_domestic_supplies")
        self._move("out_invoice", self.cz_partner, [(20000.0, tax21, None)])
        st, root = self._export()
        a4 = root.find(".//VetaA4")
        self.assertIsNone(a4.get("zakl_dane3"))
        self.assertIsNone(a4.get("dan3"))

    # ------------------------------------------------------------------
    # 3. §92a commodity codes
    # ------------------------------------------------------------------
    def test_one_row_per_commodity_code(self):
        """Two kinds of § 92a supply on one document are two rows with the same
        evidence number — the first code no longer speaks for the document."""
        rc21 = self._tax("l10n_cz_21_tax_reverse_charge_scheme")
        bill = self._move("in_invoice", self.cz_partner, [
            (20000.0, rc21, self._product("4")),
            (3000.0, rc21, self._product("5"))], ref="PDP-2")
        st, root = self._export()
        rows = {r.get("kod_pred_pl"): r for r in root.findall(".//VetaB1")}
        self.assertEqual(set(rows), {"4", "5"})
        self.assertEqual(rows["4"].get("zakl_dane1"), "20000")
        self.assertEqual(rows["5"].get("zakl_dane1"), "3000")
        self.assertEqual({r.get("c_evid_dd") for r in rows.values()}, {bill.ref})

    def test_a_missing_commodity_code_blocks_the_export(self):
        """No default: '1' filed every uncoded reverse charge as GOLD."""
        rc21 = self._tax("l10n_cz_21_tax_reverse_charge_scheme")
        rc21.cssk_kh_commodity_code = False
        bill = self._move("in_invoice", self.cz_partner,
                          [(20000.0, rc21, None)], ref="PDP-NOCODE")
        with self.assertRaises(UserError) as cm:
            self._export()
        self.assertIn("B1", str(cm.exception))
        self.assertIn(bill.ref, str(cm.exception))

    # ------------------------------------------------------------------
    # 4. sectioning
    # ------------------------------------------------------------------
    def test_czech_vat_charged_to_an_eu_customer_is_a_domestic_supply(self):
        """Charging 21 % to a customer with a German VAT number is a domestic
        taxable supply (ř. 1). It used to vanish from the KH as an intra-EU
        supply; and A.4 cannot identify a customer without a Czech DIČ, so it
        is reported in A.5."""
        tax21 = self._tax("l10n_cz_21_domestic_supplies")
        self._move("out_invoice", self.de_partner, [(15000.0, tax21, None)])
        st, root = self._export()
        self.assertFalse(root.findall(".//VetaA4"),
                         "a German number must not be filed as dic_odb")
        a5 = root.find(".//VetaA5")
        self.assertIsNotNone(a5)
        self.assertEqual(a5.get("zakl_dane1"), "15000")
        self.assertEqual(root.find(".//VetaC").get("obrat23"), "15000")

    def test_zero_rated_eu_supply_stays_out(self):
        eu_goods = self._tax("l10n_cz_supply_goods_eu")
        move = self._move("out_invoice", self.de_partner,
                          [(15000.0, eu_goods, None)])
        self.assertFalse(move.invoice_line_ids.cssk_control_section_code)

    def test_third_country_service_is_a2_not_b2(self):
        """ř. 12 — the recipient is liable under § 108 odst. 3 — is reported in
        A.2, with no supplier identification (no EU VAT ID)."""
        ex_s = self._tax("l10n_cz_21_receipt_service_person_non_eu")
        bill = self._move("in_invoice", self.us_partner,
                          [(12000.0, ex_s, None)], ref="US-SVC-1")
        self.assertEqual(bill.invoice_line_ids.cssk_control_section_code, "A2")
        st, root = self._export()
        self.assertFalse(root.findall(".//VetaB2"))
        a2 = root.find(".//VetaA2")
        self.assertEqual(a2.get("c_evid_dd"), "US-SVC-1")
        self.assertEqual(a2.get("zakl_dane1"), "12000")
        self.assertEqual(a2.get("dan1"), "2520")
        self.assertIsNone(a2.get("k_stat"))
        self.assertIsNone(a2.get("vatid_dod"))
        self.assertEqual(root.find(".//VetaC").get("celk_zd_a2"), "12000")

    def test_import_of_goods_is_not_reported(self):
        """Metodická informace k vyplnění KH, bod 1.2: dovoz zboží (§ 23,
        ř. 7, 8) se do kontrolního hlášení neuvádí."""
        ex_g = self._tax("l10n_cz_21_import_goods")
        bill = self._move("in_invoice", self.us_partner,
                          [(50000.0, ex_g, None)], ref="IMPORT-1")
        self.assertFalse(bill.invoice_line_ids.cssk_control_section_code)

    def test_greece_is_el_in_a2(self):
        eu21 = self._tax("l10n_cz_21_acquisition_goods_eu")
        self._move("in_invoice", self.gr_partner, [(9000.0, eu21, None)],
                   ref="GR-1")
        st, root = self._export()
        a2 = root.find(".//VetaA2")
        self.assertEqual(a2.get("k_stat"), "EL")
        self.assertEqual(a2.get("vatid_dod"), "094014201")

    def test_a2_section_label_cites_108_2_and_3(self):
        a2 = self.version.section_code_ids.filtered(lambda s: s.code == "A2")
        self.assertIn("§ 108 odst. 2 a 3", a2.name)

    # ------------------------------------------------------------------
    # manual override of a row reaches the export and survives a recompute
    # ------------------------------------------------------------------
    def test_an_override_is_filed_and_survives_recompute(self):
        """An override used to edit tax_base_amount / tax_amount, which no CZ
        export reads: the row was filed with its computed split."""
        tax21 = self._tax("l10n_cz_21_domestic_supplies")
        self._move("out_invoice", self.cz_partner, [(20000.0, tax21, None)])
        st, root = self._export()
        a4 = st.cz_a4_ids
        self.assertEqual(len(a4), 1)
        st.action_reset_to_draft()
        a4.write({"is_overridden": True, "base_std": 19000.0,
                  "tax_std": 3990.0})
        st.action_compute_lines()
        a4 = st.cz_a4_ids
        self.assertTrue(a4.is_overridden)
        self.assertEqual((a4.base_std, a4.tax_std), (19000.0, 3990.0),
                         "the override is re-applied to the recomputed row")
        st.action_export_xml()
        root = etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))
        row = root.find(".//VetaA4")
        self.assertEqual((row.get("zakl_dane1"), row.get("dan1")),
                         ("19000", "3990"))

    def test_an_override_key_tells_commodity_codes_apart(self):
        rc_sale = self._tax("l10n_cz_tax_reverse_charge_mode")
        self._move("out_invoice", self.cz_partner,
                   [(30000.0, rc_sale, self._product("4")),
                    (10000.0, rc_sale, self._product("5"))])
        st, _root = self._export()
        a1 = st.cz_a1_ids
        self.assertEqual(len(a1), 2)
        self.assertEqual(len({r._kv_override_key() for r in a1}), 2,
                         "one document, two § 92a codes, two override keys")

    def test_the_sections_offer_the_override(self):
        arch = self.env["cssk.control.statement"].get_views(
            [(False, "form")])["views"]["form"]["arch"]
        tree = etree.fromstring(arch)
        for name in ("cz_a1_ids", "cz_a2_ids", "cz_a4_ids", "cz_a5_ids",
                     "cz_b1_ids", "cz_b2_ids", "cz_b3_ids"):
            field = tree.find(".//field[@name='%s']" % name)
            self.assertIsNotNone(
                field.find(".//field[@name='is_overridden']"), name)
            self.assertIsNotNone(
                field.find(".//field[@name='base_std']"), name)

    # ------------------------------------------------------------------
    # § 92a kód předmětu plnění on the SALE reverse-charge tax
    # ------------------------------------------------------------------
    def test_the_sale_rc_tax_code_is_used(self):
        """The stock "0% RC" sale tax carries no Reverse charge mark (A.1 is
        recognised by its ř. 25 row), so a code set on it was ignored and a
        sale without a coded product could not be exported."""
        rc_sale = self._tax("l10n_cz_tax_reverse_charge_mode")
        self.assertFalse(rc_sale.cssk_control_is_reverse_charge,
                         "premise: the sale RC tax is unmarked")
        self.assertTrue(rc_sale.cssk_kh_domestic_rc,
                        "the field is offered on the tax form")
        rc_sale.cssk_kh_commodity_code = "4"
        self._move("out_invoice", self.cz_partner, [(30000.0, rc_sale, None)])
        _st, root = self._export()
        a1 = root.findall(".//VetaA1")
        self.assertEqual([r.get("kod_pred_pl") for r in a1], ["4"])

    def test_an_ordinary_sale_tax_code_is_not_a_92a_code(self):
        tax21 = self._tax("l10n_cz_21_domestic_supplies")
        self.assertFalse(tax21.cssk_kh_domestic_rc)

    def test_the_code_help_lists_the_form_codes(self):
        help_text = self.env["account.tax"]._fields[
            "cssk_kh_commodity_code"].help
        self.assertIn("6 = goods originally provided as a guarantee", help_text)
        self.assertIn("11 = greenhouse-gas emission allowances", help_text)
        self.assertNotIn("6 = emission allowances", help_text)
