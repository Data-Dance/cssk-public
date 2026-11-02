# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import Command
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


class ExecutiveSummaryMixin:
    """Sale 1000 (604), goods 400 bought on credit and expensed (504/321),
    300 of the sale collected in cash: every figure below follows."""

    def _account(self, prefix):
        return self.env["account.account"].search([
            ("company_ids", "in", self.company.id), ("code", "=like", prefix + "%")], order="code", limit=1)

    def _post(self, debit, credit, amount):
        journal = self.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", self.company.id)], limit=1)
        move = self.env["account.move"].create({
            "move_type": "entry", "date": "2026-03-15", "journal_id": journal.id,
            "line_ids": [Command.create({"account_id": self._account(debit).id, "debit": amount}),
                         Command.create({"account_id": self._account(credit).id, "credit": amount})]})
        move.action_post()

    def _values(self):
        self._post("311", "604", 1000.0)
        self._post("504", "321", 400.0)
        self._post("211", "311", 300.0)
        report = self.env.ref("l10n_cssk_mis_executive_summary.mis_report_executive_summary")
        instance = self.env["mis.report.instance"].create({
            "name": "Summary", "report_id": report.id, "company_id": self.company.id,
            "period_ids": [(0, 0, {"name": "March", "mode": "fix", "source": "actuals",
                                   "manual_date_from": "2026-03-01", "manual_date_to": "2026-03-31"})]})
        matrix = instance._compute_matrix()
        subcol = list(next(matrix.iter_cols()).iter_subcols())[0]
        return {r.kpi.name: subcol.get_cell_for_row(r).val for r in matrix.iter_rows()}

    def test_summary_figures(self):
        v = self._values()
        expected = {
            "revenue": 1000.0, "cost_of_sales": 400.0, "gross_profit": 600.0,
            "income_total": 1000.0, "expense_total": 400.0, "net_profit": 600.0,
            "gross_margin": 0.6, "net_margin": 0.6,
            "cash_in": 300.0, "cash_out": 0.0, "cash_close": 300.0,
            "receivables": 700.0, "payables": 400.0, "period_days": 31,
            "dso": 700.0 / 1000.0 * 31, "dpo": 31.0,
            "current_ratio": 2.5, "roa": 0.6,
        }
        for name, value in expected.items():
            self.assertAlmostEqual(v[name] or 0.0, value, places=6, msg=name)


@tagged("post_install", "-at_install")
class TestExecutiveSummarySk(ExecutiveSummaryMixin, AccountTestInvoicingCommon):
    # Odoo collects test methods from the class's own __dict__ only.
    allow_inherited_tests_method = True

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]


@tagged("post_install", "-at_install")
class TestExecutiveSummaryCz(ExecutiveSummaryMixin, AccountTestInvoicingCommon):
    # Odoo collects test methods from the class's own __dict__ only.
    allow_inherited_tests_method = True

    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
