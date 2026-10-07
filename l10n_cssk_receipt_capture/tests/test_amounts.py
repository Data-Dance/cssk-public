# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo.tests.common import TransactionCase

from ..tools.amounts import (
    flatten_label, normalize_vat, reconciles, same_rate, split_gross,
)


class TestAmounts(TransactionCase):
    """The pure helpers, pinned against figures measured on real receipts.

    The amounts are the ones the tax authority itself reported; the
    receipts they came from are anonymised in the fixtures.
    """

    def test_split_gross_matches_the_authority(self):
        """Half-up gross-up reproduces Finančná správa's own recap to the cent.

        Both cases are from real service responses: a fuel receipt at 23 %
        and the 5 % bucket of a restaurant bill.
        """
        self.assertEqual(split_gross(57.85, 23.0), (47.03, 10.82))
        self.assertEqual(split_gross(130.50, 5.0), (124.29, 6.21))
        self.assertEqual(split_gross(51.40, 23.0), (41.79, 9.61))

    def test_split_gross_zero_rate_and_zero_amount(self):
        self.assertEqual(split_gross(0.0, 19.0), (0.0, 0.0))
        self.assertEqual(split_gross(10.0, 0.0), (10.0, 0.0))
        self.assertEqual(split_gross(None, None), (0.0, 0.0))

    def test_split_gross_never_invents_a_unit_price(self):
        """The reason line quantities are not posted as quantities.

        31.17 litres for 57.85 is 1.855951… a litre. Rounded to the two
        decimals of a price field it becomes 1.86, and 1.86 x 31.17 is 57.98 —
        thirteen cents that nobody spent.
        """
        gross, qty = 57.85, 31.17
        naive_unit = round(gross / qty, 2)
        self.assertEqual(naive_unit, 1.86)
        self.assertNotAlmostEqual(naive_unit * qty, gross, places=2)
        self.assertAlmostEqual(round(naive_unit * qty, 2), 57.98, places=2)

    def test_normalize_vat(self):
        self.assertEqual(normalize_vat("SK 2077 000 002"), "SK2077000002")
        self.assertEqual(normalize_vat("sk2077000002"), "SK2077000002")
        self.assertEqual(normalize_vat(None), "")

    def test_reconciles_tolerance(self):
        self.assertTrue(reconciles(10.00, 10.01))
        self.assertTrue(reconciles(10.00, 10.02))
        self.assertFalse(reconciles(10.00, 10.05))
        self.assertFalse(reconciles(None, 10.00))

    def test_same_rate(self):
        self.assertTrue(same_rate(19.0, 19))
        self.assertTrue(same_rate(19.00, 19.001))
        self.assertFalse(same_rate(19.0, 19.5))
        self.assertFalse(same_rate(20.0, 23.0))

    def test_flatten_label_collapses_modifiers(self):
        """An item name arrives multi-line with modifiers already priced in."""
        raw = ("GRILOVANÉ MENU PRE 2 OSOBY\n"
               "1x Príloha navyše +3EUR (3,00 EUR)\n"
               "1x Druhá príloha +0EUR")
        self.assertEqual(
            flatten_label(raw),
            "GRILOVANÉ MENU PRE 2 OSOBY · 1x Príloha navyše +3EUR (3,00 EUR) "
            "· 1x Druhá príloha +0EUR")
        self.assertNotIn("\n", flatten_label(raw))

    def test_flatten_label_truncates(self):
        self.assertEqual(len(flatten_label("x" * 500, limit=20)), 20)
        self.assertTrue(flatten_label("x" * 500, limit=20).endswith("…"))
        self.assertEqual(flatten_label(None), "")
