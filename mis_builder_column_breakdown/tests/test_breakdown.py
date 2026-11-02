# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestColumnBreakdown(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        income = cls.company_data["default_account_revenue"]
        cls.init_invoice("out_invoice", partner=cls.partner_a, invoice_date="2026-03-05", amounts=[100.0], post=True)
        cls.init_invoice("out_invoice", partner=cls.partner_a, invoice_date="2026-03-06", amounts=[20.0], post=True)
        cls.init_invoice("out_invoice", partner=cls.partner_b, invoice_date="2026-03-07", amounts=[30.0], post=True)
        cls.report = cls.env["mis.report"].create({
            "name": "Breakdown test",
            "kpi_ids": [(0, 0, {"name": "rev", "description": "Revenue",
                                "expression": "-balp[%s]" % income.code})],
        })
        partner_field = cls.env["ir.model.fields"]._get("account.move.line", "partner_id")
        cls.instance = cls.env["mis.report.instance"].create({
            "name": "Breakdown test", "report_id": cls.report.id, "company_id": cls.company.id,
            "period_ids": [(0, 0, {
                "name": "March", "mode": "fix", "source": "actuals",
                "manual_date_from": "2026-03-01", "manual_date_to": "2026-03-31",
                "breakdown_field_id": partner_field.id,
            })],
        })
        cls.period = cls.instance.period_ids

    def _matrix(self):
        matrix = self.instance._compute_matrix()
        row = next(r for r in matrix.iter_rows() if r.kpi.name == "rev")
        cols = {}
        for col in matrix.iter_cols():
            cell = list(col.iter_subcols())[0].get_cell_for_row(row)
            cols[col.label] = (col.key, cell)
        return cols

    def test_one_column_per_value_then_the_total(self):
        cols = self._matrix()
        self.assertEqual(list(cols), [self.partner_a.display_name, self.partner_b.display_name, "March (total)"])
        self.assertAlmostEqual(cols[self.partner_a.display_name][1].val, 120.0)
        self.assertAlmostEqual(cols[self.partner_b.display_name][1].val, 30.0)
        key, total = cols["March (total)"]
        self.assertEqual(key, self.period.id)     # the total keeps the period's key
        self.assertAlmostEqual(total.val, 150.0)

    def test_drilldown_follows_the_sub_column(self):
        _key, cell = self._matrix()[self.partner_b.display_name]
        action = self.instance.drilldown(cell.drilldown_arg)
        lines = self.env["account.move.line"].search(action["domain"])
        self.assertEqual(lines.partner_id, self.partner_b)
        self.assertAlmostEqual(-sum(lines.mapped("balance")), 30.0)

    def test_sum_column_still_finds_the_period(self):
        self.env["mis.report.instance.period"].create({
            "name": "Sum", "report_instance_id": self.instance.id, "source": "sumcol", "mode": "none",
            "source_sumcol_ids": [(0, 0, {"period_to_sum_id": self.period.id, "sign": "+"})],
        })
        self.assertAlmostEqual(self._matrix()["Sum"][1].val, 150.0)

    def test_limit_caps_the_columns(self):
        self.period.breakdown_limit = 1
        cols = self._matrix()
        self.assertEqual(len(cols), 2)          # the busiest partner + total
        self.assertIn(self.partner_a.display_name, cols)

    def test_notes_belong_to_their_own_column(self):
        self.env.user.group_ids |= self.env.ref("mis_builder.group_edit_annotation") | self.env.ref(
            "mis_builder.group_read_annotation")
        self.instance.invalidate_recordset()
        Note = self.env["mis.report.instance.annotation"]
        cols = self._matrix()
        _key, sub = cols[self.partner_a.display_name]
        _key, other = cols[self.partner_b.display_name]
        _key, total = cols["March (total)"]
        Note.set_annotation(sub.cell_id, self.instance.id, "partner A note")
        Note.set_annotation(total.cell_id, self.instance.id, "total note")
        notes = self.instance.get_notes_by_cell_id()
        self.assertEqual(notes[sub.cell_id]["text"], "partner A note")
        self.assertEqual(notes[total.cell_id]["text"], "total note")
        self.assertNotIn(other.cell_id, notes)
        # Editing finds the same note; removing removes only that one.
        Note.set_annotation(sub.cell_id, self.instance.id, "edited")
        self.assertEqual(self.instance.get_notes_by_cell_id()[sub.cell_id]["text"], "edited")
        Note.remove_annotation(sub.cell_id, self.instance.id)
        notes = self.instance.get_notes_by_cell_id()
        self.assertNotIn(sub.cell_id, notes)
        self.assertEqual(notes[total.cell_id]["text"], "total note")
