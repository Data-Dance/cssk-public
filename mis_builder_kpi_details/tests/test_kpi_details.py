# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.exceptions import ValidationError
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestKpiDetails(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        income = cls.company_data["default_account_revenue"]
        cls.init_invoice("out_invoice", partner=cls.partner_a, invoice_date="2026-03-05", amounts=[100.0], post=True)
        cls.init_invoice("out_invoice", partner=cls.partner_a, invoice_date="2026-04-06", amounts=[20.0], post=True)
        cls.init_invoice("out_invoice", partner=cls.partner_b, invoice_date="2026-04-07", amounts=[30.0], post=True)
        F = cls.env["ir.model.fields"]
        cls.partner_field = F._get("account.move.line", "partner_id")
        cls.date_field = F._get("account.move.line", "date")
        cls.report = cls.env["mis.report"].create({
            "name": "Details test",
            "kpi_ids": [
                (0, 0, {"name": "rev", "description": "Revenue", "sequence": 1,
                        "expression": "-balp[%s]" % income.code,
                        "details_field_id": cls.partner_field.id}),
                (0, 0, {"name": "rev2", "description": "Revenue twice", "sequence": 2,
                        "expression": "rev * 2", "details_field_id": cls.partner_field.id}),
            ],
        })
        cls.instance = cls.env["mis.report.instance"].create({
            "name": "Details test", "report_id": cls.report.id, "company_id": cls.company.id,
            "period_ids": [(0, 0, {"name": "Q", "mode": "fix", "source": "actuals",
                                   "manual_date_from": "2026-03-01", "manual_date_to": "2026-04-30"})],
        })

    def _rows(self):
        matrix = self.instance._compute_matrix()
        col = next(matrix.iter_cols())
        subcol = list(col.iter_subcols())[0]
        return {(r.kpi.name, r.label): subcol.get_cell_for_row(r) for r in matrix.iter_rows()}

    def test_unfolds_by_partner_and_adds_up(self):
        rows = self._rows()
        self.assertAlmostEqual(rows[("rev", "Revenue")].val, 150.0)
        self.assertAlmostEqual(rows[("rev", self.partner_a.display_name)].val, 120.0)
        self.assertAlmostEqual(rows[("rev", self.partner_b.display_name)].val, 30.0)
        # A KPI built from other KPIs is not unfolded.
        self.assertEqual([k for k in rows if k[0] == "rev2"], [("rev2", "Revenue twice")])

    def test_unfolds_by_month(self):
        self.report.kpi_ids.filtered(lambda k: k.name == "rev").details_field_id = self.date_field
        rows = self._rows()
        self.assertAlmostEqual(rows[("rev", "2026-03")].val, 100.0)
        self.assertAlmostEqual(rows[("rev", "2026-04")].val, 50.0)

    def test_drilldown_follows_the_detail(self):
        cell = self._rows()[("rev", self.partner_b.display_name)]
        action = self.instance.drilldown(cell.drilldown_arg)
        lines = self.env["account.move.line"].search(action["domain"])
        self.assertEqual(lines.partner_id, self.partner_b)

    def test_details_or_accounts(self):
        with self.assertRaises(ValidationError):
            self.report.kpi_ids[0].auto_expand_accounts = True
