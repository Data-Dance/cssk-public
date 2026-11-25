# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""ř. 50 / ř. 150: the difference between accounting and tax depreciation."""

import base64
from datetime import date
from unittest.mock import patch

from lxml import etree

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.modules.module import get_module_path, load_script
from odoo.tests import tagged


def _register(book, tax):
    """What ``res.company._cssk_asset_book_tax_difference`` returns."""
    diff = book - tax

    def difference(self, date_from, date_to):
        return {"book": book, "tax": tax, "difference": diff,
                "addback": max(diff, 0.0), "deduction": max(-diff, 0.0)}
    return difference


class DepreciationCase(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.vat = "CZ25663585"
        cls.company.l10n_cssk_tax_authority_id = cls.env[
            "cssk.tax.authority"].search(
            [("country_code", "=", "CZ"), ("submission_code", "=", "451")],
            limit=1)
        cls.version = cls.env.ref("l10n_cz_dppo.cz_dppo_version_2025")
        cls.type_b = cls.env.ref("l10n_cz_dppo.cz_dppo_type_B")

    def _return(self, date_from="2025-01-01", date_to="2025-12-31"):
        return self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id, "version_id": self.version.id,
            "statement_type_id": self.type_b.id,
            "date_from": date_from, "date_to": date_to})

    def _values(self, ret):
        return {line.code: line.value for line in ret.line_ids}

    def _typed(self, ret, code, value):
        ret.line_ids.filtered(lambda l: l.code == code).write(
            {"is_overridden": True, "manual_value": value})

    def _patched(self, book, tax):
        return patch.object(
            self.registry["res.company"], "_cssk_asset_book_tax_difference",
            _register(book, tax), create=True)

    def _veta_o(self, ret):
        ret.action_export_xml()
        root = etree.fromstring(base64.b64decode(ret.xml_attachment_id.datas))
        return root.find(".//VetaO")


@tagged("post_install", "-at_install")
class TestCzDppoDepreciation(DepreciationCase):

    def test_accounting_above_tax_goes_to_row_50(self):
        """Pokyny 25 5404/1, K ř. 50: the amount by which the depreciation
        claimed in the books exceeds the depreciation under § 26 to 33."""
        with self._patched(book=120000.0, tax=100000.0):
            ret = self._return()
            ret.action_compute_lines()
            self._typed(ret, "r70_other", 3000.0)
            ret.action_compute_lines()
            values = self._values(ret)
            self.assertEqual(values["r50"], 20000.0)
            self.assertEqual(values["r150"], 0.0, "one row or the other")
            self.assertEqual(values["r70"], 23000.0)
            self.assertEqual(values["r170"], 0.0)
            self.assertEqual(values["r200"], values["r10"] + 23000.0)
            veta_o = self._veta_o(ret)
        self.assertEqual(veta_o.get("kc_ii60_50"), "20000")
        self.assertEqual(veta_o.get("kc_ii80_70"), "23000")
        self.assertIsNone(veta_o.get("kc_ii170_150"))

    def test_tax_above_accounting_goes_to_row_150(self):
        with self._patched(book=100000.0, tax=145000.0):
            ret = self._return()
            ret.action_compute_lines()
            self._typed(ret, "r170_other", 5000.0)
            ret.action_compute_lines()
            values = self._values(ret)
            self.assertEqual(values["r150"], 45000.0)
            self.assertEqual(values["r50"], 0.0)
            self.assertEqual(values["r170"], 50000.0)
            self.assertEqual(values["r200"], values["r10"] - 50000.0)
            veta_o = self._veta_o(ret)
        self.assertEqual(veta_o.get("kc_ii170_150"), "45000")
        self.assertEqual(veta_o.get("kc_ii190_170"), "50000")
        self.assertIsNone(veta_o.get("kc_ii60_50"))

    def test_the_rows_are_whole_crowns(self):
        """Each row is filed rounded on its own, so ř. 50 must not carry
        haléře into the sum ř. 70."""
        with self._patched(book=100000.5, tax=90000.0):
            ret = self._return()
            ret.action_compute_lines()
            self.assertEqual(self._values(ret)["r50"], 10001.0)
        with self._patched(book=90000.0, tax=100000.4):
            ret.action_compute_lines()
            self.assertEqual(self._values(ret)["r150"], 10000.0)

    def test_a_typed_subtotal_must_contain_its_rows(self):
        from odoo.exceptions import UserError

        with self._patched(book=120000.0, tax=100000.0):
            ret = self._return()
            ret.action_compute_lines()
            self._typed(ret, "r70", 50000.0)
            ret.action_compute_lines()
            with self.assertRaisesRegex(UserError, "ostatní položky"):
                ret.action_export_xml()
            # typed so that it does contain ř. 50: accepted
            self._typed(ret, "r70_other", 30000.0)
            ret.action_compute_lines()
            veta_o = self._veta_o(ret)
        self.assertEqual(veta_o.get("kc_ii80_70"), "50000")
        self.assertEqual(veta_o.get("kc_ii60_50"), "20000")

    def test_a_typed_row_50_wins_over_the_register(self):
        with self._patched(book=120000.0, tax=100000.0):
            ret = self._return()
            ret.action_compute_lines()
            self._typed(ret, "r50", 7000.0)
            ret.action_compute_lines()
            values = self._values(ret)
        self.assertEqual(values["r50"], 7000.0)
        self.assertEqual(values["r70"], 7000.0)

    def test_a_period_across_a_year_end_is_not_computed(self):
        """The tax board is kept by calendar year; a hospodářský rok would
        get the tax depreciation of two calendar years."""
        with self._patched(book=120000.0, tax=100000.0):
            ret = self._return("2024-07-01", "2025-06-30")
            before = len(ret.message_ids)
            ret.action_compute_lines()
            values = self._values(ret)
            self.assertEqual(values["r50"], 0.0)
            self.assertEqual(values["r150"], 0.0)
            self.assertEqual(len(ret.message_ids), before + 1,
                             "the return says the rows were not computed")
            self._typed(ret, "r50", 9000.0)
            ret.action_compute_lines()
            self.assertEqual(self._values(ret)["r50"], 9000.0)
            self.assertEqual(len(ret.message_ids), before + 1,
                             "nothing to say once the row is typed")

    def test_no_register_no_figure(self):
        """Without account_asset_tax the rows stay empty and typed."""
        company_cls = self.registry["res.company"]
        if hasattr(company_cls, "_cssk_asset_book_tax_difference"):
            self.skipTest("account_asset_tax is installed")
        ret = self._return()
        ret.action_compute_lines()
        values = self._values(ret)
        self.assertEqual((values["r50"], values["r150"]), (0.0, 0.0))


@tagged("post_install", "-at_install")
class TestCzDppoDepreciationMigration(DepreciationCase):
    """19.0.1.7.0 on a database that has the rows as 1.6.0 shipped them."""

    def _downgrade_rows(self):
        defs = self.version.line_def_ids
        defs.filtered(lambda d: d.code in (
            "r50", "r150", "r70_other", "r170_other")).unlink()
        defs.exists().filtered(lambda d: d.code in ("r70", "r170")).write(
            {"kind": "manual", "aggregate_formula": False})

    def _migrate(self, installed="19.0.1.6.0"):
        script = load_script(
            get_module_path("l10n_cz_dppo")
            + "/migrations/19.0.1.7.0/post-migrate.py", "cz_dppo_1_7_0")
        script.migrate(self.env.cr, installed)
        self.version.invalidate_recordset()

    def test_rows_are_added_and_subtotals_become_sums(self):
        self._downgrade_rows()
        self._migrate()
        by_code = {d.code: d for d in self.version.line_def_ids}
        self.assertEqual(by_code["r50"].kind, "asset_diff")
        self.assertEqual(by_code["r50"].account_formula, "addback")
        self.assertEqual(by_code["r150"].account_formula, "deduction")
        self.assertEqual(by_code["r70"].aggregate_formula, "r70_other + r50")
        self.assertEqual(by_code["r170"].aggregate_formula,
                         "r170_other + r150")
        self._migrate()
        self.assertEqual(
            len(self.version.line_def_ids.filtered(lambda d: d.code == "r50")),
            1, "running it twice adds nothing")

    def test_an_interrupted_run_is_completed(self):
        self._downgrade_rows()
        self.env["cssk.income.tax.line.def"].create({
            "version_id": self.version.id, "code": "r50", "name": "ř.50",
            "kind": "asset_diff", "account_formula": "addback"})
        self._migrate()
        by_code = {d.code: d for d in self.version.line_def_ids}
        self.assertIn("r170_other", by_code)
        self.assertEqual(by_code["r70"].kind, "aggregate")

    def test_an_open_return_keeps_its_typed_subtotal(self):
        """The base must not move because the module was upgraded."""
        self._downgrade_rows()
        ret = self._return()
        ret.action_compute_lines()
        self._typed(ret, "r70", 50000.0)
        ret.action_compute_lines()
        base = self._values(ret)["r200"]
        filed = self._return("2024-01-01", "2024-12-31")
        filed.action_compute_lines()
        filed.state = "exported"
        notes = len(ret.message_ids)
        self._migrate()
        self.assertEqual(len(ret.message_ids), notes + 1)
        self.assertFalse(filed.message_ids.filtered(
            lambda m: "19.0.1.7.0" in (m.body or "")))
        with self._patched(book=120000.0, tax=100000.0):
            ret.action_compute_lines()
            values = self._values(ret)
        self.assertEqual(values["r50"], 20000.0)
        self.assertEqual(values["r70"], 50000.0, "the typed subtotal stays")
        self.assertEqual(values["r200"], base)

    def test_a_rebuilt_subtotal_is_left_alone(self):
        self._downgrade_rows()
        r70 = self.version.line_def_ids.filtered(lambda d: d.code == "r70")
        r70.write({"kind": "aggregate", "aggregate_formula": "r10 * 0"})
        self._migrate()
        self.assertEqual(r70.aggregate_formula, "r10 * 0")

    def test_a_fresh_install_is_not_migrated(self):
        before = self.version.line_def_ids
        self._migrate(installed=None)
        self.assertEqual(self.version.line_def_ids, before)


@tagged("post_install", "-at_install")
class TestCzDppoDepreciationFromRegister(DepreciationCase):
    """The real register (``account_asset_tax_oca``); skipped without it."""

    def setUp(self):
        super().setUp()
        if "account.asset.profile" not in self.env or \
                "tax_line_ids" not in self.env["account.asset"]._fields:
            self.skipTest("account_asset_tax_oca is not installed")

    def test_rows_follow_the_register(self):
        def acc(code, name, atype):
            return self.env["account.account"].create({
                "code": code, "name": name, "account_type": atype,
                "company_ids": [Command.link(self.company.id)]})
        journal = self.env["account.journal"].create({
            "name": "Majetek", "code": "MAJT", "type": "general",
            "company_id": self.company.id})
        profile = self.env["account.asset.profile"].create({
            "name": "Stroje", "journal_id": journal.id,
            "company_id": self.company.id,
            "account_asset_id": acc("022990", "Stroje", "asset_non_current").id,
            "account_depreciation_id": acc(
                "082990", "Oprávky", "asset_non_current").id,
            "account_expense_depreciation_id": acc(
                "551990", "Odpisy", "expense").id,
            "method_time": "year", "method_number": 5, "method_period": "year",
        })
        group = self.env["account.asset.tax.class"].search(
            [("country_code", "=", "CZ"), ("allow_linear", "=", True)],
            limit=1)
        if not group:
            group = self.env["account.asset.tax.class"].create({
                "code": "T-CZ2", "name": "CZ2", "country_code": "CZ",
                "group_number": 2, "useful_life_years": 5,
                "allow_linear": True})
        asset = self.env["account.asset"].create({
            "name": "Lis", "profile_id": profile.id,
            "company_id": self.company.id,
            "purchase_value": 500000, "date_start": date(2024, 1, 1)})
        asset.write({
            "tax_depreciation_enabled": True, "tax_class_id": group.id,
            "tax_method": "linear", "tax_entry_value": 500000,
            "tax_in_service_date_override": date(2024, 1, 1)})
        asset.compute_tax_depreciation_board()
        diff = self.company._cssk_asset_book_tax_difference(
            date(2025, 1, 1), date(2025, 12, 31))
        self.assertTrue(diff["tax"], "the board has a 2025 line")
        ret = self._return()
        ret.action_compute_lines()
        values = self._values(ret)
        self.assertAlmostEqual(values["r50"], diff["addback"], 2)
        self.assertAlmostEqual(values["r150"], diff["deduction"], 2)
        self.assertEqual(values["r170"], values["r150"])
