# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Checks on the shipped statutory data.

The minimum-wage table is transcribed from the published figures rather than
derived, so the derivation is used here as an independent check on the
transcription: a typo in one of the 18 amounts fails the § 120 ods. 4 formula.
"""

from datetime import date

from odoo.exceptions import UserError
from odoo.tests import TransactionCase

# § 120 ods. 4: the 2020 anchor and the six coefficients.
ANCHOR_2020 = 580.0
COEFFICIENTS = {"1": 1.0, "2": 1.2, "3": 1.4, "4": 1.6, "5": 1.8, "6": 2.0}
# § 134 — the statutory average monthly working hours the hourly figures use.
MONTHLY_HOURS = 174.0


class TestMinimumWageData(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["l10n.sk.minimum.wage"]

    def test_every_year_has_all_six_levels(self):
        for year in (2024, 2025, 2026):
            claims = self.model.search([("date_from", "=", date(year, 1, 1))])
            self.assertEqual(
                len(claims), 6, "%s must ship all six stupne náročnosti" % year
            )

    def test_monthly_amounts_follow_the_statutory_formula(self):
        for year in (2024, 2025, 2026):
            base = self.model._get_claim(date(year, 6, 30), "1").amount_monthly
            for level, coeff in COEFFICIENTS.items():
                expected = (base - ANCHOR_2020) + ANCHOR_2020 * coeff
                claim = self.model._get_claim(date(year, 6, 30), level)
                self.assertAlmostEqual(
                    claim.amount_monthly,
                    expected,
                    places=2,
                    msg="%s level %s" % (year, level),
                )

    def test_hourly_amounts_are_the_monthly_over_174(self):
        for year in (2024, 2025, 2026):
            for level in COEFFICIENTS:
                claim = self.model._get_claim(date(year, 6, 30), level)
                self.assertAlmostEqual(
                    claim.amount_hourly,
                    round(claim.amount_monthly / MONTHLY_HOURS, 3),
                    places=3,
                    msg="%s level %s" % (year, level),
                )

    def test_lookup_picks_the_latest_vintage_not_a_later_one(self):
        self.assertEqual(self.model._get_base_hourly(date(2025, 12, 31)), 4.690)
        self.assertEqual(self.model._get_base_hourly(date(2026, 1, 1)), 5.259)

    def test_lookup_before_the_first_vintage_raises(self):
        with self.assertRaises(UserError):
            self.model._get_claim(date(2020, 1, 1), "1")


class TestSurchargeRateData(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.model = cls.env["l10n.sk.wage.surcharge.rate"]

    def test_shipped_percentages(self):
        rate = self.model._get_rate(date(2026, 3, 31))
        self.assertEqual(rate._pct("NOC"), 40.0)
        self.assertEqual(rate._pct("NOC", risk=True), 50.0)
        self.assertEqual(rate._pct("NOC", reduced=True), 35.0)
        self.assertEqual(rate._pct("SOBOTA"), 50.0)
        self.assertEqual(rate._pct("NEDELA"), 100.0)
        self.assertEqual(rate._pct("SVIATOK"), 100.0)
        self.assertEqual(rate._pct("NADCAS"), 25.0)
        self.assertEqual(rate._pct("NADCAS", risk=True), 35.0)
        self.assertEqual(rate._pct("STAZENY"), 20.0)
        self.assertEqual(rate._pct("POHOTOVOST"), 20.0)

    def test_lookup_before_the_percentage_regime_raises(self):
        """Before 1 June 2023 the surcharges were fixed euro amounts."""
        with self.assertRaises(UserError):
            self.model._get_rate(date(2023, 5, 31))
