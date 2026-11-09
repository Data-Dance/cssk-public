# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Who files (VetaP), and the header of a následné hlášení / výzva answer.

Every export here goes through ``action_export_xml``, which validates against
the official DPHKH1 XSD, so a wrong attribute fails the test by itself.
"""

import base64

from lxml import etree

from odoo import Command, fields
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools import date_utils


@tagged("post_install", "-at_install")
class TestCzKhFiler(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({
            "vat": "CZ25663585",
            "street": "Diabasová 1141/11",
            "zip": "155 00",
            "city": "Praha 13",
            "phone": "+420 511 447 174",
            "email": "dph@example.cz",
            "l10n_cz_epo_signatory_first_name": "Jana",
            "l10n_cz_epo_signatory_last_name": "Nováková",
            "l10n_cz_epo_signatory_position": "jednatelka",
            "l10n_cz_epo_preparer_first_name": "Petr",
            "l10n_cz_epo_preparer_last_name": "Svoboda",
        })
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.partner = cls.env["res.partner"].create({
            "name": "Odber CZ", "country_id": cls.env.ref("base.cz").id,
            "vat": "CZ46342958",
        })
        vat1 = cls.env["account.account.tag"]._get_tax_tags(
            "VAT 1 Base", cls.env.ref("base.cz").id)
        cls.tax21 = cls.env["account.tax"].search([
            ("type_tax_use", "=", "sale"), ("amount", "=", 21.0),
            ("company_id", "=", cls.company.id),
            ("invoice_repartition_line_ids.tag_ids", "in", vat1.ids),
        ], limit=1)
        cls.version = cls.env.ref("l10n_cz_kh.cz_kh_version_2025")

    def _sale(self, amount):
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": amount,
                "tax_ids": [Command.set(self.tax21.ids)]})],
        })
        inv.action_post()
        return inv

    def _statement(self, type_xmlid="l10n_cz_kh.cz_kh_type_B", **vals):
        today = fields.Date.context_today(self.env.user)
        st = self.env["cssk.control.statement"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "date_from": today.replace(day=1), "date_to": date_utils.end_of(today, "month"),
            "period_type": "month",
            "statement_type_id": self.env.ref(type_xmlid).id,
            **vals,
        })
        st.action_compute_lines()
        return st

    def _export(self, st):
        st.action_export_xml()
        return etree.fromstring(base64.b64decode(st.xml_attachment_id.datas))

    def test_a_legal_entity_files_with_its_signatory_and_address(self):
        self._sale(15000.0)
        veta_p = self._export(self._statement()).find(".//VetaP")
        self.assertEqual(veta_p.get("typ_ds"), "P")
        self.assertEqual(veta_p.get("zkrobchjm"), self.company.name[:255])
        self.assertEqual(veta_p.get("ulice"), "Diabasová")
        self.assertEqual(veta_p.get("c_pop"), "1141")
        self.assertEqual(veta_p.get("c_orient"), "11")
        self.assertEqual(veta_p.get("psc"), "15500")
        self.assertEqual(veta_p.get("naz_obce"), "Praha 13")
        self.assertEqual(veta_p.get("c_telef"), "+420511447174")
        self.assertEqual(veta_p.get("opr_prijmeni"), "Nováková")
        self.assertEqual(veta_p.get("opr_postaveni"), "jednatelka")
        self.assertEqual(veta_p.get("sest_prijmeni"), "Svoboda")
        self.assertIsNone(veta_p.get("jmeno"))

    def test_a_natural_person_files_as_f(self):
        self.company.write({
            "l10n_cssk_person_type_id": self.env.ref(
                "l10n_cz_statutory.cz_person_type_fo").id,
            "l10n_cz_epo_title": "Ing.",
            "l10n_cz_epo_first_name": "Jan",
            "l10n_cz_epo_last_name": "Dvořák",
        })
        self._sale(15000.0)
        veta_p = self._export(self._statement()).find(".//VetaP")
        self.assertEqual(veta_p.get("typ_ds"), "F")
        self.assertEqual(veta_p.get("prijmeni"), "Dvořák")
        self.assertEqual(veta_p.get("titul"), "Ing.")
        self.assertIsNone(veta_p.get("zkrobchjm"))
        self.assertIsNone(veta_p.get("opr_prijmeni"))

    def test_a_tax_adviser_files_for_the_client(self):
        adviser = self.env["res.partner"].create({
            "name": "Daně s.r.o.", "is_company": True,
            "company_registry": "25596641",
        })
        self.company.write({
            "l10n_cz_epo_agent_partner_id": adviser.id,
            "l10n_cz_epo_agent_code": "4c",
        })
        self._sale(15000.0)
        veta_p = self._export(self._statement()).find(".//VetaP")
        self.assertEqual(veta_p.get("zast_typ"), "P")
        self.assertEqual(veta_p.get("zast_kod"), "4c")
        self.assertEqual(veta_p.get("zast_nazev"), "Daně s.r.o.")
        self.assertEqual(veta_p.get("zast_ic"), "25596641")

    def test_an_answer_to_a_vyzva_carries_no_rows(self):
        self._sale(15000.0)
        st = self._statement(
            cz_kh_notice_number="12345678/26/2000-00000-123456",
            cz_kh_notice_answer="P")
        root = self._export(st)
        veta_d = root.find(".//VetaD")
        self.assertEqual(veta_d.get("vyzva_odp"), "P")
        self.assertEqual(veta_d.get("c_jed_vyzvy"), "12345678/26/2000-00000-123456")
        self.assertIsNone(root.find(".//VetaA4"))
        self.assertIsNone(root.find(".//VetaC"))

    def test_an_answer_needs_the_reference(self):
        st = self._statement(cz_kh_notice_answer="B")
        with self.assertRaisesRegex(UserError, "č.j. výzvy"):
            st.action_export_xml()

    def test_a_nasledne_hlaseni_needs_its_discovery_date(self):
        self._sale(15000.0)
        st = self._statement("l10n_cz_kh.cz_kh_type_N")
        with self.assertRaisesRegex(UserError, "d_zjist"):
            st.action_export_xml()
        st.cz_kh_discovery_date = "2026-09-01"
        veta_d = self._export(st).find(".//VetaD")
        self.assertEqual(veta_d.get("khdph_forma"), "N")
        self.assertEqual(veta_d.get("d_zjist"), "01.09.2026")

    def test_n_and_e_are_what_the_form_calls_them(self):
        self.assertEqual(self.env.ref("l10n_cz_kh.cz_kh_type_N").name, "Následné")
        self.assertEqual(
            self.env.ref("l10n_cz_kh.cz_kh_type_E").name, "Následné/opravné")

    def test_a_flagged_correction_without_a_dic_is_refused(self):
        partner = self.env["res.partner"].create({
            "name": "Bez DIC", "country_id": self.env.ref("base.cz").id})
        origin = self._sale(3000.0)
        origin.button_draft()
        origin.partner_id = partner
        origin.action_post()
        refund = origin._reverse_moves()
        refund.l10n_cz_bad_debt = "P"
        refund.action_post()
        with self.assertRaisesRegex(UserError, "bad-debt correction"):
            self._statement()

    def test_an_old_section_44_correction_exports_tax_only(self):
        """GFŘ 4. 12. 2019: for A the base is not accessible on the row."""
        origin = self._sale(3000.0)
        self.env.cr.execute(
            "UPDATE account_move SET taxable_supply_date = '2019-02-10' WHERE id = %s",
            [origin.id])
        origin.invalidate_recordset(["taxable_supply_date"])
        refund = origin._reverse_moves()
        refund.l10n_cz_bad_debt = "A"
        refund.action_post()
        rows = self._export(self._statement()).findall(".//VetaA4")
        row = next(r for r in rows if r.get("c_evid_dd") == refund.name)
        self.assertEqual(row.get("zdph_44"), "A")
        self.assertIsNone(row.get("zakl_dane1"))
        self.assertEqual(row.get("dan1"), "-630")

    def test_the_threshold_reads_company_currency(self):
        """100 000 HUF is about 6 667 CZK at this rate: an aggregate row."""
        huf = self.setup_other_currency("HUF", rates=[("2000-01-01", 15.0)])
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner.id,
            "currency_id": huf.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": 82644.63,
                "tax_ids": [Command.set(self.tax21.ids)]})],
        })
        inv.action_post()
        st = self._statement()
        self.assertFalse(st.cz_a4_ids.filtered(lambda r: r.move_id == inv))
        self.assertTrue(st.cz_a5_ids)

    def test_investment_gold_goes_to_a3(self):
        gold = self.env["account.chart.template"].ref("l10n_cz_investment_gold")
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner.id,
            "invoice_date": fields.Date.context_today(self.env.user),
            "invoice_line_ids": [Command.create({
                "name": "zlato", "quantity": 1, "price_unit": 50000.0,
                "tax_ids": [Command.set(gold.ids)]})],
        })
        inv.action_post()
        st = self._statement()
        self.assertFalse(st.cz_a4_ids)
        row = self._export(st).find(".//VetaA3")
        self.assertEqual(row.get("osv_plneni"), "50000")
        self.assertEqual(row.get("vatid_odb"), "46342958")
        self.assertEqual(row.get("k_stat"), "CZ")
        self.assertIsNone(row.get("jm_prijm_obch"))

    def test_a_bad_debt_correction_is_a4_whatever_its_amount(self):
        """A small correction would otherwise vanish into the A.5 aggregate,
        which has no zdph_44 to carry the flag."""
        origin = self._sale(3000.0)
        refund = origin._reverse_moves()
        refund.l10n_cz_bad_debt = "P"
        refund.action_post()
        st = self._statement()
        a4 = st.cz_a4_ids.filtered(lambda r: r.move_id == refund)
        self.assertEqual(len(a4), 1)
        self.assertEqual(st.cz_a5_ids.filtered(lambda r: r.move_id == refund),
                         st.cz_a5_ids.browse())
        rows = self._export(st).findall(".//VetaA4")
        flags = {r.get("c_evid_dd"): r.get("zdph_44") for r in rows}
        self.assertEqual(flags.get(refund.name), "P")
