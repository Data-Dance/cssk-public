# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestSkMisPl(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.report = cls.env.ref("l10n_sk_mis_reports.mis_report_pl_sk")
        cls.journal = cls.env["account.journal"].search(
            [("type", "=", "general"), ("company_id", "=", cls.company.id)], limit=1
        )

    def _account(self, code):
        return self.env["account.account"].search(
            [("company_ids", "in", self.company.id), ("code", "=", code)], limit=1
        )

    def _post(self, debit_code, credit_code, amount, date="2026-03-31"):
        move = self.env["account.move"].create(
            {
                "move_type": "entry",
                "date": date,
                "journal_id": self.journal.id,
                "company_id": self.company.id,
                "line_ids": [
                    Command.create(
                        {
                            "account_id": self._account(debit_code).id,
                            "debit": amount,
                            "credit": 0.0,
                        }
                    ),
                    Command.create(
                        {
                            "account_id": self._account(credit_code).id,
                            "debit": 0.0,
                            "credit": amount,
                        }
                    ),
                ],
            }
        )
        move.action_post()
        return move

    def _evaluate(self):
        """Run the report for Q1 2026 and return {kpi name: value}."""
        instance = self.env["mis.report.instance"].create(
            {
                "name": "Test",
                "report_id": self.report.id,
                "company_id": self.company.id,
                "period_ids": [
                    Command.create(
                        {
                            "name": "Q1",
                            "mode": "fix",
                            "manual_date_from": "2026-01-01",
                            "manual_date_to": "2026-03-31",
                        }
                    )
                ],
            }
        )
        matrix = instance._compute_matrix()
        values = {}
        for row in matrix.iter_rows():
            for cell in row.iter_cells():
                if cell is not None and cell.val is not None:
                    values[row.kpi.name] = cell.val
        return values

    # ------------------------------------------------------------------
    def test_template_ships_the_expected_lines(self):
        names = self.report.kpi_ids.mapped("name")
        for expected in (
            "trzby_tovar",
            "vynosy_spolu",
            "naklady_spolu",
            "prevadzkovy",
            "vh_pred_zdanenim",
            "vh_po_zdaneni",
        ):
            self.assertIn(expected, names)

    def test_revenue_reads_positive(self):
        """Revenue is a credit balance; the template negates it so the report
        reads the way an accountant expects rather than showing minus signs."""
        self._post("311000", "604000", 1000.0)
        values = self._evaluate()
        self.assertEqual(values["trzby_tovar"], 1000.0)
        self.assertEqual(values["vynosy_spolu"], 1000.0)

    def test_costs_read_positive_and_subtotal(self):
        self._post("501000", "321000", 400.0)
        self._post("521000", "331000", 600.0)
        values = self._evaluate()
        self.assertEqual(values["spotreba"], 400.0)
        self.assertEqual(values["osobne"], 600.0)
        self.assertEqual(values["naklady_spolu"], 1000.0)

    def test_operating_result_is_revenue_less_costs(self):
        self._post("311000", "604000", 1000.0)
        self._post("501000", "321000", 400.0)
        values = self._evaluate()
        self.assertEqual(values["prevadzkovy"], 600.0)

    def test_depreciation_is_not_double_counted_in_other_costs(self):
        """551 sits inside trieda 55, so `ostatné náklady` subtracts it.

        Without that subtraction the depreciation would be counted twice — once
        as odpisy and once inside the 54/55 sweep — and the cost subtotal would
        be overstated.
        """
        self._post("551000", "082000", 300.0)
        values = self._evaluate()
        self.assertEqual(values["odpisy"], 300.0)
        self.assertEqual(values["ostatne_naklady"], 0.0)
        self.assertEqual(values["naklady_spolu"], 300.0)

    def test_full_chain_down_to_the_after_tax_result(self):
        self._post("311000", "604000", 1000.0)   # tržby
        self._post("501000", "321000", 400.0)    # spotreba
        self._post("562000", "321000", 50.0)     # finančné náklady (úroky)
        self._post("221000", "662000", 20.0)     # finančné výnosy
        self._post("591000", "341000", 100.0)    # daň z príjmov
        values = self._evaluate()

        self.assertEqual(values["prevadzkovy"], 600.0)
        self.assertEqual(values["fin_naklady"], 50.0)
        self.assertEqual(values["fin_vynosy"], 20.0)
        self.assertEqual(values["vh_pred_zdanenim"], 570.0)
        self.assertEqual(values["dan_z_prijmov"], 100.0)
        self.assertEqual(values["vh_po_zdaneni"], 470.0)

    def test_income_tax_is_not_swept_into_operating_costs(self):
        """59x must not land in the 5x cost groups, or the operating result
        would already be after tax."""
        self._post("591000", "341000", 100.0)
        values = self._evaluate()
        self.assertEqual(values["naklady_spolu"], 0.0)
        self.assertEqual(values["prevadzkovy"], 0.0)
        self.assertEqual(values["dan_z_prijmov"], 100.0)

    def test_every_class_5_and_6_account_reaches_the_result_once(self):
        """The after-tax result equals the ledger's, account by account.

        507 (predané nehnuteľnosti), 592 (odložená daň) and 596 (prevod
        podielov spoločníkom) reached no row, so the after-tax result was
        overstated by whatever sat on them. One entry per account of the
        chart, distinct amounts, one evaluation: a missing account or one
        counted twice both move the total.
        """
        accounts = self.env["account.account"].search([
            ("company_ids", "in", self.company.id),
            ("code", "=like", "5%"),
        ]) | self.env["account.account"].search([
            ("company_ids", "in", self.company.id),
            ("code", "=like", "6%"),
        ])
        expected = 0.0
        for index, account in enumerate(accounts.sorted("code"), start=1):
            amount = float(index)
            if account.code.startswith("5"):
                self._post(account.code, "321000", amount)
                expected -= amount
            else:
                self._post("311000", account.code, amount)
                expected += amount
        values = self._evaluate()
        self.assertAlmostEqual(values["vh_po_zdaneni"], expected, places=2)

    def test_deferred_tax_and_profit_transfer_are_below_the_line(self):
        self._post("311000", "604000", 1000.0)
        self._post("592000", "481000", 30.0)    # odložená daň
        self._post("596000", "364000", 70.0)    # prevod podielov
        self._post("507000", "123000", 200.0)   # predané nehnuteľnosti
        values = self._evaluate()
        self.assertEqual(values["predane_nehnutelnosti"], 200.0)
        self.assertEqual(values["prevadzkovy"], 800.0)
        self.assertEqual(values["dan_z_prijmov"], 30.0)
        self.assertEqual(values["prevod_podielov"], 70.0)
        self.assertEqual(values["vh_po_zdaneni"], 700.0)

    def test_the_helper_row_is_not_printed(self):
        helper = self.env.ref("l10n_sk_mis_reports.kpi_trieda_54_55")
        self.assertTrue(helper.style_id.hide_always)
        self.assertFalse(helper.style_id.hide_always_inherit)
