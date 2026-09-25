# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Tests for the deterministic half of the pipeline.

The model is never asked to pick an Odoo record — it returns natural keys, and
the helpers here decide whether those keys hang together. That makes this the
layer where a wrong answer is caught, so it is the layer worth testing.
"""

from odoo.tests import TransactionCase, tagged

from ..tools.resolver import (
    normalize_vat,
    reconciles,
    totals_consistent,
    vat_country_prefix,
)


@tagged("post_install", "-at_install")
class TestResolverHelpers(TransactionCase):
    def test_normalize_vat_strips_formatting(self):
        self.assertEqual(normalize_vat("SK 2020 123 456"), "SK2020123456")
        self.assertEqual(normalize_vat("cz-123.456/789"), "CZ123456789")
        self.assertEqual(normalize_vat(None), "")
        self.assertEqual(normalize_vat(""), "")

    def test_vat_country_prefix(self):
        self.assertEqual(vat_country_prefix("SK2020123456"), "SK")
        self.assertEqual(vat_country_prefix("sk 2020123456"), "SK")
        # A bare number carries no country.
        self.assertEqual(vat_country_prefix("2020123456"), "")
        self.assertEqual(vat_country_prefix("A1"), "")
        self.assertEqual(vat_country_prefix(None), "")

    def test_reconciles_tolerance_and_junk(self):
        self.assertTrue(reconciles(100.00, 100.02))
        self.assertFalse(reconciles(100.00, 100.03))
        self.assertTrue(reconciles(100.00, 100.10, tolerance=0.10))
        # Never raise on rubbish from the model — just decline to reconcile.
        self.assertFalse(reconciles(None, 100.00))
        self.assertFalse(reconciles("abc", 100.00))

    def test_totals_must_be_present_and_complete(self):
        ok, reason = totals_consistent(None, None)
        self.assertFalse(ok)
        self.assertIn("missing totals", reason)

        ok, reason = totals_consistent({"net": 100.0, "vat": 23.0}, None)
        self.assertFalse(ok)
        self.assertIn("incomplete totals", reason)

    def test_net_plus_vat_must_equal_gross(self):
        ok, _reason = totals_consistent(
            {"net": 100.0, "vat": 23.0, "gross": 123.0}, None
        )
        self.assertTrue(ok)

        ok, reason = totals_consistent(
            {"net": 100.0, "vat": 23.0, "gross": 130.0}, None
        )
        self.assertFalse(ok)
        self.assertIn("!= gross", reason)

    def test_breakdown_must_sum_to_the_totals(self):
        totals = {"net": 300.0, "vat": 59.0, "gross": 359.0}
        good = [
            {"rate": 23.0, "base": 100.0, "vat_amount": 23.0},
            {"rate": 18.0, "base": 200.0, "vat_amount": 36.0},
        ]
        ok, _reason = totals_consistent(totals, good)
        self.assertTrue(ok)

        bad_base = [
            {"rate": 23.0, "base": 50.0, "vat_amount": 23.0},
            {"rate": 18.0, "base": 200.0, "vat_amount": 36.0},
        ]
        ok, reason = totals_consistent(totals, bad_base)
        self.assertFalse(ok)
        self.assertIn("base sum", reason)

        bad_vat = [
            {"rate": 23.0, "base": 100.0, "vat_amount": 5.0},
            {"rate": 18.0, "base": 200.0, "vat_amount": 36.0},
        ]
        ok, reason = totals_consistent(totals, bad_vat)
        self.assertFalse(ok)
        self.assertIn("VAT sum", reason)

    def test_zero_vat_invoice_reconciles(self):
        """Reverse charge and exports arrive with zero VAT — not an error."""
        ok, _reason = totals_consistent(
            {"net": 1000.0, "vat": 0.0, "gross": 1000.0},
            [{"rate": 0.0, "base": 1000.0, "vat_amount": 0.0}],
        )
        self.assertTrue(ok)

    def test_missing_breakdown_amounts_count_as_zero(self):
        """A breakdown line with no vat_amount must not raise."""
        ok, reason = totals_consistent(
            {"net": 100.0, "vat": 0.0, "gross": 100.0},
            [{"rate": 0.0, "base": 100.0}],
        )
        self.assertTrue(ok, reason)
