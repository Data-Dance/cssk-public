# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""III. časť, tabuľky A and B as return lines; r130/r150/r250 derived."""

import base64
from datetime import date

from lxml import etree

from odoo import Command
from odoo.exceptions import UserError
from odoo.tools.misc import file_path
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestDppoTables(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.l10n_sk_dic = "2020317068"
        cls.company.company_registry = "36000001"
        cls.company.write({"city": "Bratislava", "zip": "81101",
                           "street": "Test 1"})

    # ------------------------------------------------------------------
    def _version(self, suffix):
        version = self.env.ref("l10n_sk_dppo.dppo_version_%s" % suffix)
        if not version.rate_bands:
            version.rate_bands = [[None, 21.0]]
        return version

    def _return(self, suffix="2025", year=2025, type_code="R", **extra):
        version = self._version(suffix)
        stype = version.statement_type_ids.filtered(
            lambda t: t.fa_xml_value == type_code)
        vals = {"company_id": self.company.id, "version_id": version.id,
                "statement_type_id": stype.id,
                "date_from": "%d-01-01" % year, "date_to": "%d-12-31" % year}
        vals.update(extra)
        ret = self.env["cssk.income.tax.return"].create(vals)
        ret.action_compute_lines()
        return ret

    @staticmethod
    def _set(ret, **values):
        for code, value in values.items():
            line = ret.line_ids.filtered(lambda l, c=code: l.code == c)
            line.ensure_one()
            line.write({"is_overridden": True, "manual_value": value,
                        "value": value})
        ret.action_compute_lines()

    @staticmethod
    def _v(ret, code):
        return ret.line_ids.filtered(lambda l: l.code == code).value

    def _export(self, ret):
        ret.action_export_xml()
        return etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))

    # ------------------------------------------------------------------
    # The derivation
    # ------------------------------------------------------------------
    def test_r130_is_the_table_a_total(self):
        ret = self._return()
        self._set(ret, a06=1200.0, a16=300.5)
        self.assertAlmostEqual(self._v(ret, "a17"), 1500.5, 2)
        self.assertAlmostEqual(self._v(ret, "r130"), 1500.5, 2)
        # ... and flows through the spine exactly like a typed r130 did
        self.assertAlmostEqual(self._v(ret, "r200"), 1500.5, 2)

    def test_table_b_feeds_r150_and_r250(self):
        """B6 = B2 − B3 − B4 + B5; r150/r250 = ±(B1 − B6), floored at 0.

        The figures are the PR's worked case: B1 3 345, B5 3 000 -> r150 345;
        then B2 6 000, B3 1 000, B4 500 -> B6 4 500 and r250 1 155.
        """
        ret = self._return()
        self._set(ret, b01=3345.0, b05=3000.0)
        self.assertAlmostEqual(self._v(ret, "b06"), 3000.0, 2)
        self.assertAlmostEqual(self._v(ret, "r150"), 345.0, 2)
        self.assertAlmostEqual(self._v(ret, "r250"), 0.0, 2)
        self._set(ret, b02=6000.0, b03=1000.0, b04=500.0, b05=0.0)
        self.assertAlmostEqual(self._v(ret, "b06"), 4500.0, 2)
        self.assertAlmostEqual(self._v(ret, "r150"), 0.0, 2)
        self.assertAlmostEqual(self._v(ret, "r250"), 1155.0, 2)
        self.assertAlmostEqual(self._v(ret, "r300"), 1155.0, 2)

    def test_b06_is_floored_at_zero_like_the_eform(self):
        ret = self._return()
        self._set(ret, b01=100.0, b03=50.0)
        self.assertEqual(self._v(ret, "b06"), 0.0)
        self.assertAlmostEqual(self._v(ret, "r150"), 100.0, 2)

    def test_a_typed_main_row_with_empty_tables_still_files(self):
        """How every return was filed before the tables: r150 typed, tables empty."""
        ret = self._return()
        self._set(ret, r130=700.0, r150=250.0)
        self.assertAlmostEqual(self._v(ret, "r200"), 950.0, 2)
        root = self._export(ret)
        self.assertEqual(root.findtext(".//r130"), "700.00")
        self.assertEqual(root.findtext(".//r150"), "250.00")
        self.assertFalse(root.findtext(".//tabA/r17"))
        self.assertFalse(root.findtext(".//tabB/r01"))

    # ------------------------------------------------------------------
    # The kontrola
    # ------------------------------------------------------------------
    def test_an_override_against_a_filled_table_blocks_the_export(self):
        ret = self._return()
        self._set(ret, a06=1000.0, r130=900.0)
        with self.assertRaisesRegex(UserError, "r130"):
            ret.action_export_xml()
        self._set(ret, r130=1000.0)      # agreeing override is fine
        ret.action_export_xml()
        self.assertEqual(ret.state, "exported")

    def test_table_b_override_and_its_total_are_checked(self):
        ret = self._return()
        self._set(ret, b01=500.0, r150=100.0)
        with self.assertRaisesRegex(UserError, "r150"):
            ret.action_export_xml()
        ret = self._return()
        self._set(ret, b02=800.0, b06=700.0)
        with self.assertRaisesRegex(UserError, "b06"):
            ret.action_export_xml()

    # ------------------------------------------------------------------
    # XML
    # ------------------------------------------------------------------
    def test_2025_export_carries_the_tables_and_validates_both_schemas(self):
        ret = self._return()
        self._set(ret, a06=1200.0, b01=3345.0, b05=3000.0)
        root = self._export(ret)       # validates against dppo2025_v2.xsd
        self.assertEqual(root.findtext(".//tabA/r06"), "1200.00")
        self.assertEqual(root.findtext(".//tabA/r17"), "1200.00")
        self.assertFalse(root.findtext(".//tabA/r01"))     # untouched: empty
        self.assertEqual(root.findtext(".//tabB/r01"), "3345.00")
        self.assertEqual(root.findtext(".//tabB/r06"), "3000.00")
        self.assertEqual(root.findtext(".//r130"), "1200.00")
        self.assertEqual(root.findtext(".//r150"), "345.00")
        with open(file_path("l10n_sk_dppo/data/dppo2025.xsd"), "rb") as fh:
            schema = etree.XMLSchema(etree.parse(fh))
        schema.assertValid(root)

    def test_2024_vzor_return_with_tables(self):
        ret = self._return("2024", 2024)
        self._set(ret, a01=10.0, a10=90.0, b01=1000.0, b02=1400.0)
        self.assertAlmostEqual(self._v(ret, "r130"), 100.0, 2)
        self.assertAlmostEqual(self._v(ret, "r250"), 400.0, 2)
        root = self._export(ret)
        self.assertEqual(root.findtext(".//tabA/r17"), "100.00")
        self.assertEqual(root.findtext(".//tabB/r06"), "1400.00")
        self.assertEqual(root.findtext(".//r250"), "400.00")

    def test_2013_layout_fifteen_and_four_rows(self):
        """2013/2014: r. 15 is the úhrn; tabB r. 2 účtovné, r. 1 daňové."""
        ret = self._return("2013", 2013)
        self._set(ret, a14=40.0, b01=300.0, b02=500.0)
        self.assertAlmostEqual(self._v(ret, "a15"), 40.0, 2)
        self.assertAlmostEqual(self._v(ret, "r130"), 40.0, 2)
        self.assertAlmostEqual(self._v(ret, "r150"), 200.0, 2)
        root = self._export(ret)
        self.assertEqual(root.findtext(".//tabA/r15"), "40.00")
        self.assertEqual(root.findtext(".//tabB/r02"), "500.00")

    def test_a_table_row_no_longer_leaks_into_every_table(self):
        """The 2013–2022 vzory had ONE line per two-digit code feeding row N of
        every table and section; a value typed there landed everywhere, and an
        untouched one filed 0.00 everywhere."""
        ret = self._return("2022", 2022)
        codes = set(ret.line_ids.mapped("code"))
        self.assertFalse({"r01", "r02", "r17", "r31"} & codes)
        self._set(ret, a01=55.0)
        root = self._export(ret)       # validates against dppo2022.xsd
        self.assertEqual(root.findtext(".//tabA/r01"), "55.00")
        for path in (".//tabB/r01", ".//tabC1/r01", ".//tabD/r01",
                     ".//podielyNaZisku/r01", ".//tabA/r02"):
            node = root.find(path)
            if node is not None:
                self.assertFalse(node.text, "%s leaked a value" % path)

    def test_every_vintage_carries_both_tables(self):
        for suffix, a, b in (("2013", 15, 4), ("2014", 15, 4), ("2015", 17, 6),
                             ("2017", 17, 6), ("2018", 17, 6), ("2019", 17, 6),
                             ("2020", 17, 6), ("2021", 17, 6), ("2022", 17, 6),
                             ("2024", 17, 6), ("2025", 17, 6)):
            codes = set(self._version(suffix).line_def_ids.mapped("code"))
            self.assertEqual({c for c in codes if c[:1] == "a"},
                             {"a%02d" % i for i in range(1, a + 1)}, suffix)
            self.assertEqual({c for c in codes if c[:1] == "b"},
                             {"b%02d" % i for i in range(1, b + 1)}, suffix)
            derived = self._version(suffix).line_def_ids.filtered(
                lambda d: d.code in ("r130", "r150", "r250"))
            self.assertEqual(set(derived.mapped("kind")), {"aggregate"}, suffix)

    # ------------------------------------------------------------------
    # Dodatočné priznanie
    # ------------------------------------------------------------------
    def test_an_amendment_recomputes_from_its_own_tables(self):
        original = self._return()
        self._set(original, r100=100000.0, a06=1000.0, r560=150000.0)
        original.action_export_xml()
        original.action_submit()
        action = original.action_create_amendment()
        amendment = self.env["cssk.income.tax.return"].browse(action["res_id"])
        amendment.statement_type_id = self.env.ref(
            "l10n_sk_dppo.dppo_type_D_2025")
        amendment.action_compute_lines()
        self.assertAlmostEqual(self._v(amendment, "r130"), 1000.0, 2)
        self._set(amendment, a06=1500.0)
        self.assertAlmostEqual(self._v(amendment, "r130"), 1500.0, 2)
        self.assertAlmostEqual(self._v(amendment, "r200"), 1500.0, 2)
        # dodatočné rows: the tax rose by 21 % of the extra 500
        self.assertAlmostEqual(
            self._v(amendment, "r1130"),
            self._v(amendment, "r1050") - self._v(original, "r1050"), 2)
        self.assertGreater(self._v(amendment, "r1130"), 0.0)
        amendment.action_export_xml()
        self.assertEqual(amendment.state, "exported")


@tagged("post_install", "-at_install")
class TestDppoTablesFromRegister(AccountTestInvoicingCommon):
    """Table B from the asset tax register (``account_asset_tax_oca``).

    Skipped where the OCA bridge is not installed; the scratch suite for this
    change installs it.
    """

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.l10n_sk_dic = "2020317068"
        cls.company.company_registry = "36000001"
        cls.company.write({"city": "Bratislava", "zip": "81101",
                           "street": "Test 1"})

    def setUp(self):
        super().setUp()
        if "account.asset.profile" not in self.env or \
                "tax_line_ids" not in self.env["account.asset"]._fields:
            self.skipTest("account_asset_tax_oca is not installed")

    def _profile(self, code):
        def acc(acode, name, atype):
            return self.env["account.account"].create({
                "code": acode, "name": name, "account_type": atype,
                "company_ids": [Command.link(self.company.id)]})
        journal = self.env["account.journal"].create({
            "name": "Assets %s" % code, "code": "AS%s" % code[:3],
            "type": "general", "company_id": self.company.id})
        return self.env["account.asset.profile"].create({
            "name": "Profile %s" % code, "journal_id": journal.id,
            "company_id": self.company.id,
            "account_asset_id": acc(code, "Asset %s" % code, "asset_non_current").id,
            "account_depreciation_id": acc("08%s" % code[2:], "Dep %s" % code,
                                           "asset_non_current").id,
            "account_expense_depreciation_id": acc("5519%s" % code[1:3], "Exp %s" % code,
                                                   "expense").id,
            "method_time": "year", "method_number": 6, "method_period": "year",
        })

    def _asset(self, profile, name, **tax):
        group = self.env["account.asset.tax.class"].search(
            [("country_code", "=", "SK"), ("group_number", "=", 2)], limit=1)
        if not group:
            group = self.env["account.asset.tax.class"].create({
                "code": "T-SK2", "name": "SK2", "country_code": "SK",
                "group_number": 2, "useful_life_years": 6, "allow_linear": True})
        asset = self.env["account.asset"].create({
            "name": name, "profile_id": profile.id, "company_id": self.company.id,
            "purchase_value": 60000, "date_start": date(2023, 1, 1)})
        asset.write(dict({
            "tax_depreciation_enabled": True, "tax_class_id": group.id,
            "tax_method": "linear", "tax_entry_value": 60000,
            "tax_in_service_date_override": date(2023, 1, 1)}, **tax))
        asset.compute_tax_depreciation_board()
        return asset

    def test_table_b_is_prefilled_and_r150_r250_are_unchanged(self):
        tangible = self._profile("022990")
        intangible = self._profile("013990")
        self._asset(tangible, "Running")
        suspended = self._asset(tangible, "Suspended")
        suspended._add_tax_event("suspension", date(2025, 1, 1), duration_years=1)
        sold = self._asset(tangible, "Sold", tax_sk_disposal_months=True)
        sold._add_tax_event("disposal", date(2025, 4, 10))
        self._asset(intangible, "Software")

        company = self.company
        diff = company._cssk_asset_book_tax_difference(
            date(2025, 1, 1), date(2025, 12, 31))
        # 10 000 a year: running 10 000, suspended 0 (would have been 10 000),
        # sold 3/12 of 10 000 = 2 500 under § 22 ods. 12
        self.assertAlmostEqual(diff["b_suspended"], 10000.0, 2)
        self.assertAlmostEqual(diff["b_sale"], 2500.0, 2)
        self.assertAlmostEqual(diff["b_tax"], 12500.0, 2)
        self.assertAlmostEqual(diff["b_tax_gross"], 20000.0, 2)
        # the software is on 013: not hmotný majetok, out of Table B
        self.assertAlmostEqual(diff["tax"], 22500.0, 2)

        version = self.env.ref("l10n_sk_dppo.dppo_version_2025")
        ret = self.env["cssk.income.tax.return"].create({
            "company_id": company.id, "version_id": version.id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2025").id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        ret.action_compute_lines()
        value = {line.code: line.value for line in ret.line_ids}
        self.assertAlmostEqual(value["b01"], diff["b_book"], 2)
        self.assertAlmostEqual(value["b02"], 20000.0, 2)
        self.assertAlmostEqual(value["b03"], 0.0, 2)
        self.assertAlmostEqual(value["b04"], 10000.0, 2)
        self.assertAlmostEqual(value["b05"], 2500.0, 2)
        self.assertAlmostEqual(value["b06"], 12500.0, 2)
        # With B3 = 0 the rows equal what the register fed them before 1.5.0,
        # restricted to tangible assets (the software's board is left out).
        tangible_diff = diff["b_book"] - diff["b_tax"]
        self.assertAlmostEqual(value["r150"], max(tangible_diff, 0.0), 2)
        self.assertAlmostEqual(value["r250"], max(-tangible_diff, 0.0), 2)
        # B3 is the accountant's: entering it moves r250 by exactly that much
        ret.line_ids.filtered(lambda l: l.code == "b03").write(
            {"is_overridden": True, "manual_value": 1000.0})
        ret.action_compute_lines()
        self.assertAlmostEqual(
            ret.line_ids.filtered(lambda l: l.code == "r250").value,
            max(-tangible_diff, 0.0) - 1000.0, 2)
