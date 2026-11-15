# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPPDP9 ř. 10 ↔ "** Výsledek hospodaření před zdaněním" of the VZZ.

Both figures are built from the same posted entries by two mappings that
know nothing of each other — the return's ``account_formula`` and the
``l10n_cz_fs`` rows — so the tie is a test of both.
"""
import importlib.util
import os

from odoo.exceptions import UserError
from odoo.tests import tagged

from .test_cz_dppo_vykazy import TestCzDppoVykazy

MODULE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


@tagged("post_install", "-at_install")
class TestCzDppoFsCompare(TestCzDppoVykazy):

    def _rows(self, ret):
        return self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", ret._name), ("res_id", "=", ret.id),
            ("basis", "=", "filing")])

    def _r10(self, ret):
        return ret.line_ids.filtered(lambda line: line.code == "r10")

    def _vhb(self, statement):
        return statement.line_ids.filtered(
            lambda line: line.code == "VHB").current_value

    def test_r10_ties_to_the_profit_and_loss_statement(self):
        self._ledger()
        pl = self._statement(self.pl_version)
        ret = self._return(l10n_cz_fs_profit_loss_id=pl.id,
                           l10n_cz_fs_balance_sheet_id=self._statement(
                               self.bs_version).id)
        # 602 500 000 − 501 100 000 − 551 120 000 − 558 20 000
        self.assertAlmostEqual(self._r10(ret).value, 260000.0, places=2)
        self.assertAlmostEqual(self._vhb(pl), 260000.0, places=2)

        action = ret.action_l10n_cz_compare_fs()
        self.assertEqual(action["res_model"], "cssk.filing.discrepancy")
        row = self._rows(ret)
        self.assertEqual(len(row), 1)
        self.assertEqual(row.code, "vzz_r10")
        self.assertEqual(row.kind, "ok")
        self.assertAlmostEqual(row.difference, 0.0, places=2)

    def test_full_scope_statement_ties_too(self):
        self._ledger()
        pl = self._statement(self.pl_full)
        ret = self._return()
        row = ret._l10n_cz_fs_comparison_rows(pl)[0]
        self.assertEqual(row["kind"], "ok")
        self.assertAlmostEqual(row["computed"], 260000.0, places=2)

    def test_transfer_accounts_are_part_of_the_result_before_tax(self):
        """597 / 598 are costs above the line; 697 / 698 their counterparts.

        ř. 10 used to leave out the whole of skupina 59, so a company using
        the převodové účty had ř. 10 overstated by what stood on 597 and 598
        while the Výkaz zisku a ztráty netted them.
        """
        self._ledger()
        self._post("2025-09-30", [("597%", 7000.0, 0.0), ("697%", 0.0, 7000.0)])
        self._post("2025-09-30", [("598%", 300.0, 0.0), ("698%", 0.0, 300.0)])
        pl = self._statement(self.pl_version)
        ret = self._return()
        self.assertAlmostEqual(self._vhb(pl), 260000.0, places=2)
        self.assertAlmostEqual(self._r10(ret).value, 260000.0, places=2)
        self.assertEqual(ret._l10n_cz_fs_comparison_rows(pl)[0]["kind"], "ok")

    def test_tax_and_profit_transfer_are_below_both_results(self):
        self._ledger()
        self._post("2025-12-31", [("591%", 50000.0, 0.0), ("341%", 0.0, 50000.0)])
        self._post("2025-12-31", [("592%", 4000.0, 0.0), ("481%", 0.0, 4000.0)])
        self._post("2025-12-31", [("596%", 900.0, 0.0), ("364%", 0.0, 900.0)])
        pl = self._statement(self.pl_version)
        ret = self._return()
        self.assertAlmostEqual(self._r10(ret).value, 260000.0, places=2)
        self.assertEqual(ret._l10n_cz_fs_comparison_rows(pl)[0]["kind"], "ok")

    def test_every_class_5_and_6_account_ties(self):
        """One entry on every P&L account of the chart as shipped, distinct
        amounts: an account one mapping has and the other lacks, or has on
        the other side of the line, breaks the tie."""
        codes = [c for c in self._chart_codes() if c[0] in "56"]
        self.assertGreater(len(codes), 80)
        for index, code in enumerate(sorted(codes), start=1):
            if code[0] == "5":
                self._post("2025-05-31", [(code, float(index), 0.0),
                                          ("321000", 0.0, float(index))])
            else:
                self._post("2025-05-31", [("311000", float(index), 0.0),
                                          (code, 0.0, float(index))])
        ret = self._return()
        for version in (self.pl_version, self.pl_full):
            row = ret._l10n_cz_fs_comparison_rows(self._statement(version))[0]
            self.assertEqual(row["kind"], "ok", "%s: ř. 10 %s, VZZ %s" % (
                version.display_name, row["filed"], row["computed"]))

    def test_a_hand_entered_r10_is_reported_as_a_difference(self):
        self._ledger()
        pl = self._statement(self.pl_version)
        ret = self._return()
        self._r10(ret).write({"is_overridden": True, "manual_value": 300000.0})
        ret.action_compute_lines()
        ret.action_l10n_cz_compare_fs()
        row = self._rows(ret)
        self.assertEqual(row.kind, "amount")
        self.assertAlmostEqual(row.filed, 300000.0, places=2)
        self.assertAlmostEqual(row.computed, 260000.0, places=2)
        self.assertAlmostEqual(row.difference, 40000.0, places=2)
        self.assertTrue(row.detail)
        self.assertEqual(pl, ret._l10n_cz_find_profit_loss())

    def test_the_linked_statement_wins_over_a_later_one(self):
        self._ledger()
        linked = self._statement(self.pl_version)
        bs = self._statement(self.bs_version)
        self._statement(self.pl_version)    # a later one, not linked
        ret = self._return(l10n_cz_fs_profit_loss_id=linked.id,
                           l10n_cz_fs_balance_sheet_id=bs.id)
        self.assertEqual(ret._l10n_cz_find_profit_loss(), linked)

    def test_only_a_statement_of_the_same_period_is_compared(self):
        self._ledger()
        other = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.pl_version.id,
            "date_from": "2025-01-01", "date_to": "2025-06-30"})
        other.action_compute_lines()
        ret = self._return()
        self.assertFalse(ret._l10n_cz_find_profit_loss())
        with self.assertRaises(UserError):
            ret.action_l10n_cz_compare_fs()

    def test_a_linked_statement_of_another_period_is_refused(self):
        self._ledger()
        other = self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.pl_version.id,
            "date_from": "2025-01-01", "date_to": "2025-06-30"})
        other.action_compute_lines()
        ret = self._return()
        ret.l10n_cz_fs_profit_loss_id = other
        with self.assertRaisesRegex(UserError, "zdaňovací období"):
            ret.action_l10n_cz_compare_fs()
        self.assertFalse(self._rows(ret))

    def test_a_filed_statement_wins_over_a_later_preview(self):
        self._ledger()
        filed = self._statement(self.pl_version)
        filed.state = "exported"
        self._statement(self.pl_version)    # a later working copy
        self.assertEqual(self._return()._l10n_cz_find_profit_loss(), filed)

    def test_a_draft_statement_is_not_compared(self):
        self._ledger()
        self.env["cssk.fs.statement"].create({
            "company_id": self.company.id, "version_id": self.pl_version.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        self.assertFalse(self._return()._l10n_cz_find_profit_loss())

    def test_upgrade_corrects_a_shipped_r10_and_keeps_an_edited_one(self):
        spec = importlib.util.spec_from_file_location(
            "l10n_cz_dppo_migration_1_6_0", os.path.join(
                MODULE_DIR, "migrations", "19.0.1.6.0", "post-migrate.py"))
        migration = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(migration)
        r10 = self.version.line_def_ids.filtered(lambda d: d.code == "r10")
        self.assertEqual(r10.account_formula, migration.NEW)

        r10.account_formula = migration.OLD
        migration.migrate(self.env.cr, "19.0.1.5.1")
        self.assertEqual(r10.account_formula, migration.NEW)

        r10.account_formula = "5,6,-59,597"
        migration.migrate(self.env.cr, "19.0.1.5.1")
        self.assertEqual(r10.account_formula, "5,6,-59,597")
