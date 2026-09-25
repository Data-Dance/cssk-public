"""Unit tests for the book-vs-tax report scaffolding in the core module.

The *concrete* ``account.asset.book.tax.report`` SQL view lives in the bridges
(they own ``asset_id`` and the edition's book-depreciation tables); the core
only ships the abstract mixin. These tests pin down the shared contract; the
end-to-end row assertions live in the bridge test suites.
"""
from odoo.tests import TransactionCase

from odoo.addons.account_asset_tax.models.account_asset_book_tax_report import (
    REPORT_QUERY_TEMPLATE,
)


class TestBookTaxReportMixin(TransactionCase):

    def test_mixin_is_abstract_and_requires_bridge(self):
        Mixin = self.env["account.asset.book.tax.report.mixin"]
        self.assertTrue(Mixin._abstract)
        with self.assertRaises(NotImplementedError):
            Mixin._book_sql()
        # init() on the abstract mixin must be a no-op (no SQL view attempt)
        self.assertIsNone(Mixin.init())

    def test_query_template_shape(self):
        book_sql = "SELECT 1 AS asset_id, 2026 AS fiscal_year, 0.0 AS book_amount, 0.0 AS book_amount_posted, 0.0 AS book_residual"
        query = REPORT_QUERY_TEMPLATE % {"book_sql": book_sql}
        self.assertIn(book_sql, query)
        # book and tax are merged per (asset, fiscal year), keeping
        # single-sided years
        self.assertIn("FULL OUTER JOIN book b", query)
        self.assertIn("ON b.asset_id = t.asset_id AND b.fiscal_year = t.fiscal_year", query)
        # difference = book − tax, null-safe on both sides
        self.assertIn(
            "COALESCE(b.book_amount, 0.0) - COALESCE(t.tax_amount, 0.0) AS difference",
            query,
        )
        # every mixin column the bridges' views rely on is projected
        for column in (
            "asset_id", "company_id", "tax_class_id", "fiscal_year",
            "tax_amount", "tax_residual", "tax_posted",
            "book_amount", "book_amount_posted", "book_residual", "difference",
        ):
            self.assertIn(f"AS {column}", query)
