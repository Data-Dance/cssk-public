"""Book-vs-tax depreciation analysis view — OCA (Community) bridge tests.

OCA book depreciation = the asset's depreciation table (``account.asset.line``
of type ``depreciate``); the report must line it up per fiscal year against
the non-posted tax board.
"""
from datetime import date

from odoo import Command
from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestBookTaxReportOCA(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company

        def acc(code, name, atype):
            return cls.env["account.account"].create({
                "code": code, "name": name, "account_type": atype,
                "company_ids": [Command.link(cls.company.id)],
            })

        cls.acc_asset = acc("T024001", "Report fixed asset", "asset_non_current")
        cls.acc_dep = acc("T088001", "Report accumulated depreciation", "asset_non_current")
        cls.acc_exp = acc("T655001", "Report depreciation expense", "expense")
        cls.journal = cls.env["account.journal"].create({
            "name": "Report Asset Journal", "code": "TARJ", "type": "general",
            "company_id": cls.company.id,
        })
        cls.profile = cls.env["account.asset.profile"].create({
            "name": "Report profile",
            "journal_id": cls.journal.id,
            "account_asset_id": cls.acc_asset.id,
            "account_depreciation_id": cls.acc_dep.id,
            "account_expense_depreciation_id": cls.acc_exp.id,
            "method_time": "year",
            "method_number": 5,
            "method_period": "year",
        })
        cls.cls_group = cls.env["account.asset.tax.class"].create({
            "code": "T-SK2R",
            "name": "Test SK group 2 (report)",
            "country_code": "SK",
            "group_number": 2,
            "useful_life_years": 6,
            "allow_linear": True,
            "allow_accelerated": True,
            "accel_coeff_first": 6,
            "accel_coeff_next": 7,
            "accel_coeff_increased": 6,
        })

    def _new_asset(self):
        asset = self.env["account.asset"].create({
            "name": "Report machine",
            "profile_id": self.profile.id,
            "purchase_value": 60000,
            "date_start": date(2026, 1, 1),
        })
        asset.write({
            "tax_depreciation_enabled": True,
            "tax_class_id": self.cls_group.id,
            "tax_method": "linear",
            "tax_entry_value": 60000,
            "tax_in_service_date_override": date(2026, 1, 1),
        })
        return asset

    def _rows(self, asset):
        self.env.flush_all()
        # SQL-view rows keep their synthetic row_number ids across data
        # changes, so the ORM cache would serve stale values on a re-read.
        self.env.invalidate_all()
        return self.env["account.asset.book.tax.report"].search(
            [("asset_id", "=", asset.id)], order="fiscal_year")

    def test_report_rows_book_vs_tax(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()   # 6 tax years of 10000
        asset.compute_depreciation_board()       # 5 book years of 12000
        asset.validate()

        dep_lines = asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate")
        book_by_year = {}
        for line in dep_lines:
            book_by_year.setdefault(line.line_date.year, 0.0)
            book_by_year[line.line_date.year] += line.amount

        rows = self._rows(asset)
        # FULL OUTER JOIN: union of book years (2026-2030) and tax years (2026-2031)
        self.assertEqual(rows.mapped("fiscal_year"), list(range(2026, 2032)))

        r2026 = rows[0]
        self.assertAlmostEqual(r2026.book_amount, 12000, 2)   # 60000 / 5
        self.assertAlmostEqual(r2026.tax_amount, 10000, 2)    # 60000 / 6
        self.assertAlmostEqual(r2026.difference, 2000, 2)     # book − tax
        self.assertAlmostEqual(r2026.book_residual, 48000, 2)
        self.assertAlmostEqual(r2026.tax_residual, 50000, 2)
        self.assertFalse(r2026.tax_posted)

        # tax-only tail year (book life over): book 0, difference = −tax
        r2031 = rows[-1]
        self.assertAlmostEqual(r2031.book_amount, 0.0, 2)
        self.assertAlmostEqual(r2031.tax_amount, 10000, 2)
        self.assertAlmostEqual(r2031.difference, -10000, 2)

        # every row mirrors the ORM book figure
        for row in rows:
            self.assertAlmostEqual(row.book_amount, book_by_year.get(row.fiscal_year, 0.0), 2)

        # pivot-critical dimensions come from the asset
        self.assertEqual(r2026.company_id, asset.company_id)
        self.assertEqual(r2026.tax_class_id, self.cls_group)
        self.assertEqual(r2026.currency_id, asset.company_id.currency_id)

    def test_book_amount_posted_column(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset.compute_depreciation_board()
        asset.validate()
        rows = self._rows(asset)
        # no journal entries created yet
        self.assertAlmostEqual(sum(rows.mapped("book_amount_posted")), 0.0, 2)

        line_2026 = asset.depreciation_line_ids.filtered(
            lambda l: l.type == "depreciate" and l.line_date.year == 2026)
        line_2026.create_move()
        rows = self._rows(asset)
        r2026 = rows.filtered(lambda r: r.fiscal_year == 2026)
        self.assertAlmostEqual(r2026.book_amount_posted, 12000, 2)
        self.assertAlmostEqual(r2026.book_amount, 12000, 2)
        # other years still have no journal entry
        self.assertAlmostEqual(
            sum((rows - r2026).mapped("book_amount_posted")), 0.0, 2)

    def test_tax_posted_flag_and_grouping(self):
        asset = self._new_asset()
        asset.compute_tax_depreciation_board()
        asset.compute_depreciation_board()
        asset.validate()
        self.env["account.asset.tax.close.year"].create({
            "company_id": asset.company_id.id, "fiscal_year": 2026,
        }).action_close()

        rows = self._rows(asset)
        self.assertTrue(rows.filtered(lambda r: r.fiscal_year == 2026).tax_posted)
        self.assertFalse(rows.filtered(lambda r: r.fiscal_year == 2027).tax_posted)

        # the pivot aggregates (sum over years per asset) must be readable
        groups = self.env["account.asset.book.tax.report"]._read_group(
            [("asset_id", "=", asset.id)],
            groupby=["asset_id"],
            aggregates=["book_amount:sum", "tax_amount:sum", "difference:sum"],
        )
        self.assertEqual(len(groups), 1)
        _asset, book_sum, tax_sum, diff_sum = groups[0]
        self.assertAlmostEqual(book_sum, 60000, 2)
        self.assertAlmostEqual(tax_sum, 60000, 2)
        self.assertAlmostEqual(diff_sum, 0.0, 2)
