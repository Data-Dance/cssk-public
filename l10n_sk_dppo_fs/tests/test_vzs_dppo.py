# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkVzsDppo(AccountTestInvoicingCommon):
    """VZS r56 → DPPO r100, both built from the same posted SK data."""

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.company.write({"vat": "SK2023456787", "city": "Bratislava",
                           "country_id": cls.env.ref("base.sk").id})
        cls.recon = cls.env["l10n.sk.dph.reconciliation"]
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1)

    def _acc(self, code, account_type="expense"):
        acc = self.env["account.account"].search(
            [("code", "=like", code + "%"), ("company_ids", "in", self.company.id)],
            limit=1)
        if not acc:
            acc = self.env["account.account"].create({
                "name": code, "code": code, "account_type": account_type,
                "company_ids": [Command.set([self.company.id])]})
        return acc

    def _post_pnl(self):
        # P&L: revenue 602 = 5000, expense 501 = 3000 -> VH pred zdanením 2000.
        # Also post income tax 595 (dodatočné odvody) = 200 and prevod podielov
        # 596 = 100: both sit BELOW VH pred zdanením (VZS r57+/r60), so neither
        # the VZS r56 nor the corrected DPPO r100 (…,-595,-596) may include them.
        rev = self._acc("602", "income")
        exp, a595, a596 = self._acc("501"), self._acc("595"), self._acc("596")
        bank = self._acc("221", "asset_cash")
        self.env["account.move"].create({
            "move_type": "entry", "journal_id": self.journal.id,
            "date": "2025-06-30", "line_ids": [
                Command.create({"account_id": rev.id, "credit": 5000.0}),
                Command.create({"account_id": exp.id, "debit": 3000.0}),
                Command.create({"account_id": a595.id, "debit": 200.0}),
                Command.create({"account_id": a596.id, "debit": 100.0}),
                Command.create({"account_id": bank.id, "debit": 1700.0})],
        }).action_post()

    def _dppo(self):
        dppo = self.env["cssk.income.tax.return"].create({
            "company_id": self.company.id,
            "version_id": self.env.ref("l10n_sk_dppo.dppo_version_2025").id,
            "statement_type_id": self.env.ref("l10n_sk_dppo.dppo_type_R_2025").id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})
        dppo.action_compute_lines()
        return dppo

    def _uzpod(self):
        return self.env["l10n.sk.uzpod"].create({
            "company_id": self.company.id,
            "date_from": "2025-01-01", "date_to": "2025-12-31"})

    def test_vzs_dppo(self):
        self._post_pnl()
        dppo, uzpod = self._dppo(), self._uzpod()

        row = self.recon.reconcile_vzs_dppo(uzpod, dppo)[0]
        self.assertAlmostEqual(row["left"], 2000.0, places=2)   # VZS pred zdanením
        self.assertAlmostEqual(row["right"], 2000.0, places=2)  # DPPO r100
        self.assertEqual(row["status"], "ok")
        self.assertEqual(self.recon.check_kontroly_vzs_dppo(uzpod, dppo), [])

        # Break the tie (manual r100 override) -> VZSDPPO_RECON (error).
        r100 = dppo.line_ids.filtered(lambda l: l.code == "r100")
        r100.write({"is_overridden": True, "manual_value": 9999.0})
        dppo.action_compute_lines()
        self.assertIn("VZSDPPO_RECON",
                      [v["code"] for v in self.recon.check_kontroly_vzs_dppo(uzpod, dppo)])

    def test_action_reconcile_vzs_records_the_comparison(self):
        """The form button: find the závierka, record the rows, open them.

        It used to post the comparison to the chatter and return a toast
        saying "pozri záznam". The rows are the record now — and the left
        column holds THIS filing on every comparator, so the r100 the user is
        standing on is on the left and the VZS it is checked against is on the
        right, even though the reconciliation itself reads VZS-first.
        """
        self._post_pnl()
        self._uzpod()
        dppo = self._dppo()
        before = dppo.message_ids
        result = dppo.action_reconcile_vzs()
        self.assertFalse(dppo.message_ids - before,
                         "reconciling must not post to the chatter")
        self.assertEqual(result["type"], "ir.actions.act_window")
        self.assertEqual(result["res_model"], "cssk.filing.discrepancy")

        row = self.env["cssk.filing.discrepancy"].search([
            ("res_model", "=", "cssk.income.tax.return"),
            ("res_id", "=", dppo.id), ("basis", "=", "filing")])
        self.assertEqual(len(row), 1)
        self.assertEqual(row.kind, "ok")
        self.assertEqual(row.state, "agrees")
        self.assertAlmostEqual(row.filed, 2000.0, places=2)     # DPPO r100
        self.assertAlmostEqual(row.computed, 2000.0, places=2)  # VZS

    def test_two_comparisons_of_one_filing_do_not_overwrite_each_other(self):
        """``basis`` is in the key, and it has to be.

        A filing is compared against more than one right-hand side — itself
        recomputed, the ledger, another filing — and those comparisons can
        carry the same row code with different figures. Keyed without the
        basis, the second run overwrites the first and the screen shows one
        comparison wearing another's numbers.
        """
        self._post_pnl()
        self._uzpod()
        dppo = self._dppo()
        dppo.action_reconcile_vzs()
        Disc = self.env["cssk.filing.discrepancy"]
        row = Disc.search([("res_id", "=", dppo.id),
                           ("res_model", "=", "cssk.income.tax.return")])
        self.assertEqual(len(row), 1)
        dppo._cssk_upsert_comparison_rows(
            [{"code": row.code, "label": "same code, other basis",
              "filed": 1.0, "computed": 2.0, "diff": -1.0, "kind": "amount"}],
            "ledger", "účtovníctvo")
        both = Disc.search([("res_id", "=", dppo.id),
                            ("res_model", "=", "cssk.income.tax.return")])
        self.assertEqual(len(both), 2, "the same code on two bases is two rows")
        self.assertEqual(set(both.mapped("basis")), {"filing", "ledger"})

    def test_action_reconcile_vzs_without_a_zavierka(self):
        """And it must be *that* UserError — any other one would pass a bare
        ``assertRaises`` while the no-závierka branch never ran."""
        self._post_pnl()
        dppo = self._dppo()
        with self.assertRaisesRegex(UserError, "UZPODv14"):
            dppo.action_reconcile_vzs()
