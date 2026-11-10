# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date, datetime

from odoo.tests import BaseCase, tagged

from .. import travel_rules as rules


@tagged("post_install", "-at_install")
class TestTravelRules(BaseCase):
    def test_bands_at_their_boundaries(self):
        band = lambda h: rules.meal_rate(h, 9.30, 13.80, 20.60)  # noqa: E731
        self.assertEqual(band(4.99), 0.0)
        self.assertEqual(band(5.0), 9.30)
        self.assertEqual(band(12.0), 9.30)
        self.assertEqual(band(12.01), 13.80)
        self.assertEqual(band(18.0), 13.80)
        self.assertEqual(band(18.01), 20.60)

    def test_winter_trip_splits_at_local_midnight(self):
        """22:30 UTC on 14 Jan is 23:30 in Bratislava: one hour before midnight."""
        hours = rules.hours_by_local_day(
            datetime(2026, 1, 14, 22, 30), datetime(2026, 1, 15, 4, 30)
        )
        self.assertEqual(hours, {date(2026, 1, 14): 0.5, date(2026, 1, 15): 5.5})

    def test_summer_offset(self):
        hours = rules.hours_by_local_day(
            datetime(2026, 7, 14, 21, 30), datetime(2026, 7, 15, 3, 30)
        )
        self.assertEqual(hours, {date(2026, 7, 14): 0.5, date(2026, 7, 15): 5.5})

    def test_free_meals_reduce_by_the_top_rate(self):
        self.assertEqual(rules.meal_allowance(20.60, 20.60, lunch=True), 12.36)
        self.assertEqual(rules.meal_allowance(9.30, 20.60, lunch=True), 1.06)
        self.assertEqual(rules.meal_allowance(9.30, 20.60, breakfast=True, lunch=True), 0.0)

    def test_every_started_kilometre_counts(self):
        self.assertEqual(rules.kilometre_allowance(100.2, 0.313), 31.61)
        self.assertEqual(rules.kilometre_allowance(100.0, 0.313, trailer=True), 36.0)
        self.assertEqual(rules.fuel_allowance(100.2, 6.6, 1.5), 10.0)
