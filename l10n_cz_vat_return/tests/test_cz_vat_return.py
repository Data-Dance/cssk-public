# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import TransactionCase, tagged


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

        original = self._return()
        action = original.action_create_amendment()
        ret = self.env["cssk.vat.return"].browse(action["res_id"])
        ret.write({"statement_type_id": self.env.ref(
            "l10n_cz_vat_return.dphdp3_type_D").id, "discovery_date": False})
        ret.action_compute_lines()
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

    # --- ř. 46 and ř. 62 – 66 are computed (were manual, so filed as 0) ---
    def _sale(self, amount):
        from odoo import Command
        inv = self.env["account.move"].create({
            "move_type": "out_invoice", "partner_id": self.partner_a.id,
            "invoice_date": "2025-06-15", "date": "2025-06-15",
            "taxable_supply_date": "2025-06-15",
            "invoice_line_ids": [Command.create({
                "name": "x", "quantity": 1, "price_unit": amount,
                "tax_ids": [Command.set(self.tax21.ids)]})],
        })
        inv.action_post()
        return inv

    def test_the_total_rows_are_computed(self):
        """dphdp3_epo2.xsd: ř.62 = 1 + … + 13 − 61, ř.63 = 46 + 52 + 53 + 60,
        ř.64 = ř.62 − ř.63 when positive. They were manual lines and the
        return filed vlastní daň 0 on a period with 210 of output tax."""
        self._sale(1000.0)
        ret = self._return()
        self.assertAlmostEqual(self._v(ret, "dan_zocelk"), 210.0, places=2)
        self.assertAlmostEqual(self._v(ret, "odp_zocelk"), 0.0, places=2)
        self.assertAlmostEqual(self._v(ret, "dano_da"), 210.0, places=2)
        self.assertAlmostEqual(self._v(ret, "dano_no"), 0.0, places=2)
        self.assertAlmostEqual(self._v(ret, "dano"), 0.0, places=2)
        self.assertAlmostEqual(ret.to_pay, 210.0, places=2,
                               msg="the settlement now has its lines")
        ret.action_export_xml()
        veta6 = self._root(ret).find(".//Veta6")
        self.assertEqual((veta6.get("dan_zocelk"), veta6.get("dano_da"),
                          veta6.get("dano_no")), ("210", "210", "0"))

    def test_an_override_on_a_total_is_kept_and_flows_on(self):
        self._sale(1000.0)
        ret = self._return()
        row = ret.line_ids.filtered(lambda l: l.code == "dan_zocelk")
        row.write({"is_overridden": True, "manual_value": 250.0})
        ret.action_compute_lines()
        self.assertAlmostEqual(self._v(ret, "dan_zocelk"), 250.0, places=2)
        self.assertAlmostEqual(self._v(ret, "dano_da"), 250.0, places=2)

    def _amend(self, ret, code):
        """An amendment raised from ``ret`` the way the form raises it."""
        action = ret.action_create_amendment()
        amendment = self.env["cssk.vat.return"].browse(action["res_id"])
        amendment.write({
            "statement_type_id": self.env.ref(
                "l10n_cz_vat_return.dphdp3_type_%s" % code).id,
            "discovery_date": "2025-07-20",
        })
        return amendment

    def test_a_dodatecne_files_the_difference_row_only(self):
        """ř. 66 "vyplňuje se pouze při podání dodatečného přiznání";
        ř. 64 / 65 "při podání dodatečného přiznání se nevyplňuje"."""
        self._sale(1000.0)
        original = self._return()
        ret = self._amend(original, "D")
        self._sale(500.0)
        ret.action_compute_lines()
        # full values stay on the rows (the next amendment's baseline) …
        self.assertAlmostEqual(self._v(ret, "dan23"), 315.0, places=2)
        # … ř. 66 is the difference against the poslední známá daň
        self.assertAlmostEqual(self._v(ret, "dano"), 105.0, places=2)
        self.assertAlmostEqual(self._v(ret, "dano_da"), 0.0, places=2)
        # the settlement is ř. 66 (ř. 64 / 65 are empty on a dodatečné)
        self.assertAlmostEqual(ret.to_pay, 105.0, places=2)
        # one date: the shared one is what d_zjist files
        self.assertEqual(str(ret.cz_discovery_date), "2025-07-20")
        ret.action_export_xml()
        self.assertEqual(self._root(ret).find(".//VetaD").get("d_zjist"),
                         "20.07.2025")
        veta6 = self._root(ret).find(".//Veta6")
        self.assertEqual((veta6.get("dano"), veta6.get("dano_da"),
                          veta6.get("dano_no")), ("105", None, None),
                         "ř. 64 / 65 are not filled on a dodatečné")

    def test_a_dodatecne_files_differences_not_full_values(self):
        """Pokyny 25 5412: "V dodatečném přiznání se uvádí pouze rozdíly od
        údajů, ze kterých byla stanovena poslední známá daň". Every row used
        to be filed at its full value, so a dodatečné declared the whole
        period's tax again."""
        self._sale(1000.0)
        original = self._return()
        ret = self._amend(original, "D")
        self._sale(500.0)
        ret.action_compute_lines()
        ret.action_export_xml()
        root = self._root(ret)
        veta1 = root.find(".//Veta1")
        self.assertEqual((veta1.get("obrat23"), veta1.get("dan23")),
                         ("500", "105"))
        veta6 = root.find(".//Veta6")
        self.assertEqual((veta6.get("dan_zocelk"), veta6.get("dano")),
                         ("105", "105"))

    def test_a_dodatecne_opravne_differs_from_what_the_dodatecne_amended(self):
        """An E replaces the D it is raised from, so its baseline is the D's
        own baseline, not the D."""
        self._sale(1000.0)
        original = self._return()
        first = self._amend(original, "D")
        self._sale(500.0)
        first.action_compute_lines()
        replacement = self._amend(first, "E")
        replacement.action_compute_lines()
        self.assertEqual(replacement._cz_baseline_return(), original)
        self.assertAlmostEqual(self._v(replacement, "dano"), 105.0, places=2)

    def test_a_dodatecne_without_the_return_it_amends_is_refused(self):
        self._sale(1000.0)
        ret = self.env["cssk.vat.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "statement_type_id": self.env.ref("l10n_cz_vat_return.dphdp3_type_D").id,
            "period_type": "month", "date_from": "2025-06-01",
            "date_to": "2025-06-30", "discovery_date": "2025-07-20",
        })
        ret.action_compute_lines()
        with self.assertRaisesRegex(UserError, "differences"):
            ret.action_export_xml()

    # --- whole crowns: § 146 odst. 1 daňového řádu, § 76 odst. 3 ZDPH ------
    def test_whole_crowns_round_tax_up_and_bases_half_away_from_zero(self):
        from odoo.addons.l10n_cz_vat_return.models.cssk_vat_return import (
            _cz_whole)
        # a tax: up, to the next crown, ties included
        self.assertEqual(_cz_whole(210.50, "dan23"), 211.0)
        self.assertEqual(_cz_whole(210.01, "dan23"), 211.0)
        self.assertEqual(_cz_whole(211.50, "dan23"), 212.0)
        self.assertEqual(_cz_whole(-10.30, "dan23"), -10.0)
        self.assertEqual(_cz_whole(40.50, "odp_tuz23_nar"), 41.0)
        # float noise in a sum is not a part of a crown
        self.assertEqual(_cz_whole(210.0000000001, "dan23"), 210.0)
        # a base: nearest crown, .5 away from zero ('%.0f' gave 1002, 1000)
        self.assertEqual(_cz_whole(1002.50, "obrat23"), 1003.0)
        self.assertEqual(_cz_whole(1000.50, "obrat23"), 1001.0)
        self.assertEqual(_cz_whole(1000.49, "obrat23"), 1000.0)
        self.assertEqual(_cz_whole(-1000.50, "obrat23"), -1001.0)
        # a coefficient: whole percent, up
        self.assertEqual(_cz_whole(37.2, "koef_p20_nov"), 38.0)

    def test_export_files_whole_crowns_by_the_rule(self):
        """1 002.50 of base at 21 % is 210.53 of tax: the return files 1003
        and 211. '%.0f' (round-half-even) filed 1002 and 211."""
        self._sale(1002.50)
        ret = self._return()
        ret.action_export_xml()
        veta1 = self._root(ret).find(".//Veta1")
        self.assertEqual((veta1.get("obrat23"), veta1.get("dan23")),
                         ("1003", "211"))
        veta6 = self._root(ret).find(".//Veta6")
        self.assertEqual(veta6.get("dano_da"), "211")


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
        template = open(os.path.join(here, "report/dphdp3_report.xml"), encoding="utf-8").read()
        self.assertIn('verzePis="%s"' % version, template)
