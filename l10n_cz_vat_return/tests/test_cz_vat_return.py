# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzVatReturn(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        # EPO requires the competent tax office (c_ufo); assign the seeded one.
        # FÚ pro hl. m. Prahu — seeded by l10n_cz_statutory's hook without an
        # xmlid (the old l10n_cssk_core.cz_ufo_* ids were removed in 1.2.0);
        # look it up by its stable submission code instead.
        cls.company.l10n_cssk_tax_authority_id = cls.env["cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")], limit=1)
        cls.version = cls.env.ref("l10n_cz_vat_return.dphdp3_version_2025")
        cls.type_b = cls.env.ref("l10n_cz_vat_return.dphdp3_type_B")
        # The domestic standard-rate sale tax is the one carrying the R1
        # ("VAT 1 Base") tag — pick it deterministically.
        vat1_base = cls.env["account.account.tag"]._get_tax_tags(
            "VAT 1 Base", cls.env.ref("base.cz").id
        )
        cls.tax21 = cls.env["account.tax"].search([
            ("type_tax_use", "=", "sale"), ("amount", "=", 21.0),
            ("company_id", "=", cls.company.id),
            ("invoice_repartition_line_ids.tag_ids", "in", vat1_base.ids),
        ], limit=1)

    def _return(self):
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id,
            "version_id": self.version.id,
            "statement_type_id": self.type_b.id,
            "period_type": "month",
            "date_from": "2025-06-01", "date_to": "2025-06-30",
        })
        ret.action_compute_lines()
        return ret

    def _v(self, ret, code):
        return ret.line_ids.filtered(lambda l: l.code == code).value

    def test_export_root_and_wellformed(self):
        ret = self._return()
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")
        self.assertTrue(ret.xml_attachment_id)

    def _root(self, ret):
        import base64

        from lxml import etree
        return etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))

    def test_filer_block_and_payer_type(self):
        """VetaP comes from the company (l10n_cz_statutory), typ_platce from
        the company's status on the last day of the period."""
        self.company.write({"phone": "+420 511 447 174", "email": "a@b.cz"})
        self.company.partner_id.nace_code = "62101"
        ret = self._return()
        ret.action_export_xml()
        root = self._root(ret)
        # c_okec: the prevailing CZ-NACE 2025 activity (EPO: serious error if
        # missing); d_poddp: the filing date.
        self.assertEqual(root.find(".//VetaD").get("c_okec"), "62101")
        self.assertRegex(root.find(".//VetaD").get("d_poddp") or "", r"^\d{2}\.\d{2}\.\d{4}$")
        self.assertEqual(root.find(".//VetaP").get("typ_ds"), "P")
        self.assertEqual(root.find(".//VetaP").get("email"), "a@b.cz")
        self.assertEqual(root.find(".//VetaD").get("typ_platce"), "P")

    def test_a_dodatecne_priznani_needs_its_discovery_date(self):
        from odoo.exceptions import UserError

        ret = self._return()
        ret.statement_type_id = self.env.ref("l10n_cz_vat_return.dphdp3_type_D")
        with self.assertRaisesRegex(UserError, "d_zjist"):
            ret.action_export_xml()
        ret.cz_discovery_date = "2025-07-20"
        ret.action_export_xml()
        veta_d = self._root(ret).find(".//VetaD")
        self.assertEqual(veta_d.get("dapdph_forma"), "D")
        self.assertEqual(veta_d.get("d_zjist"), "20.07.2025")

    def test_d_and_e_are_what_the_form_calls_them(self):
        self.assertEqual(
            self.env.ref("l10n_cz_vat_return.dphdp3_type_D").name, "Dodatečné")
        self.assertEqual(
            self.env.ref("l10n_cz_vat_return.dphdp3_type_E").name,
            "Dodatečné/opravné")

    def test_standard_sale_populates_base_and_tax(self):
        from odoo import Command
        self.assertTrue(self.tax21, "CZ 21% sale tax present")
        inv = self.env["account.move"].create({
            "move_type": "out_invoice",
            "partner_id": self.partner_a.id,
            # DUZP set explicitly: the return selects its period by the tax
            # point, and l10n_cz otherwise defaults this to the day the record
            # is created — which would put a June-2025 invoice's supply date in
            # whatever month the suite happens to run.
            "invoice_date": "2025-06-15", "date": "2025-06-15",
            "taxable_supply_date": "2025-06-15",
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": 1000.0,
                "tax_ids": [Command.set(self.tax21.ids)]})],
        })
        inv.action_post()
        ret = self._return()
        # R1: domestic supply 21% -> obrat23 = base 1000, dan23 = tax 210
        self.assertAlmostEqual(self._v(ret, "obrat23"), 1000.0, places=2)
        self.assertAlmostEqual(self._v(ret, "dan23"), 210.0, places=2)
