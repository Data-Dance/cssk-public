# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Foreign trips under §§ 13, 14, 16 and 36 zákona 283/2002 Z. z.

Times are naive UTC; June is CEST, so local = UTC + 2.
"""
from datetime import date, datetime

from odoo.exceptions import UserError, ValidationError
from odoo.tests import BaseCase, TransactionCase, tagged

from .. import travel_rules as rules


@tagged("post_install", "-at_install")
class TestForeignRules(BaseCase):
    def test_band_shares(self):
        self.assertEqual(rules.foreign_band_share(0), 0.0)
        self.assertEqual(rules.foreign_band_share(6), 0.25)
        self.assertEqual(rules.foreign_band_share(6.01), 0.5)
        self.assertEqual(rules.foreign_band_share(12), 0.5)
        self.assertEqual(rules.foreign_band_share(12.01), 1.0)

    def test_meal_cuts_come_off_the_full_rate(self):
        # 8 hours abroad: 50 % of 45 = 22.50; lunch cuts 40 % of 45 = 18.
        self.assertEqual(rules.foreign_meal_allowance(45, 8, lunch=True), 4.5)
        # All three meals exceed the half rate: nothing, never negative.
        self.assertEqual(rules.foreign_meal_allowance(45, 8, True, True, True), 0.0)

    def test_pocket_money_ignores_meal_cuts(self):
        self.assertEqual(rules.pocket_money(45, 13, 40), 18.0)
        self.assertEqual(rules.pocket_money(45, 5, 40), 4.5)

    def test_split_counts_home_and_abroad_per_local_day(self):
        days = rules.split_foreign_trip(
            datetime(2026, 6, 8, 4), datetime(2026, 6, 9, 17),
            datetime(2026, 6, 8, 5), datetime(2026, 6, 9, 16),
            [(datetime(2026, 6, 8, 5), "AT"), (datetime(2026, 6, 9, 10), "DE")],
        )
        self.assertEqual(days[date(2026, 6, 8)], (1.0, {"AT": 17.0}))
        home, abroad = days[date(2026, 6, 9)]
        self.assertEqual(home, 1.0)
        # Germany from 12:00 local: 12 hours in Austria, 6 in Germany.
        self.assertEqual(abroad, {"AT": 12.0, "DE": 6.0})

    def test_tie_goes_to_the_better_rate(self):
        value = {"AT": 45.0, "CH": 80 * 1.05}.get
        self.assertEqual(rules.decisive_country({"AT": 6.0, "CH": 6.0}, value), "CH")
        self.assertEqual(rules.decisive_country({"AT": 7.0, "CH": 6.0}, value), "AT")


@tagged("post_install", "-at_install")
class TestForeignOrder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        eur = cls.env.ref("base.EUR")
        eur.active = True
        cls.company = cls.env["res.company"].create({"name": "SK cesty", "currency_id": eur.id})
        cls.env = cls.env(context=dict(cls.env.context, allowed_company_ids=[cls.company.id]))
        cls.employee = cls.env["hr.employee"].create({"name": "Cesta Zahraničná"})
        cls.at = cls.env.ref("base.at")
        cls.de = cls.env.ref("base.de")
        cls.cz = cls.env.ref("base.cz")

    def _order(self, stays, **vals):
        values = {
            "employee_id": self.employee.id,
            "trip_kind": "foreign",
            "date_start": datetime(2026, 6, 8, 4),   # 06:00 Bratislava
            "border_out": datetime(2026, 6, 8, 5),   # 07:00
            "border_in": datetime(2026, 6, 9, 16),   # 18:00 next day
            "date_end": datetime(2026, 6, 9, 17),    # 19:00
            "destination": "Wien",
            "purpose": "Audit",
            "stay_ids": [(0, 0, {"country_id": c.id, "date_arrival": a}) for c, a in stays],
        }
        values.update(vals)
        order = self.env["l10n.sk.travel.order"].create(values)
        order.action_compute_days()
        return order

    def test_two_days_in_austria_with_pocket_money(self):
        order = self._order([(self.at, False)], pocket_money_percent=40)
        first, second = order.day_ids
        # Each day: 1 hour at home earns no domestic meals, 17/18 hours
        # abroad earn the full 45 EUR, and 40 % pocket money adds 18.
        self.assertEqual((first.rate, first.foreign_amount, first.pocket_money), (0.0, 45.0, 18.0))
        self.assertEqual(second.amount, 63.0)
        self.assertEqual(order.meal_amount, 126.0)

    def test_free_lunch_abroad_cuts_the_foreign_rate(self):
        order = self._order([(self.at, False)])
        second = order.day_ids[1]
        self.assertTrue(second.meals_abroad)
        second.lunch = True
        self.assertEqual(second.amount, 27.0)

    def test_long_home_leg_earns_domestic_meals_too(self):
        # Leaves at 06:00, crosses at 12:00 (6 h at home: 9.30 EUR), then
        # just under 12 hours abroad until midnight: half the rate, 22.50 EUR.
        order = self._order(
            [(self.at, False)],
            date_start=datetime(2026, 6, 8, 4),
            border_out=datetime(2026, 6, 8, 10),
            border_in=datetime(2026, 6, 8, 21, 59, 59),
            date_end=datetime(2026, 6, 8, 21, 59, 59),
        )
        day = order.day_ids
        self.assertEqual(len(day), 1)
        self.assertEqual(day.rate, 9.30)
        self.assertEqual(day.foreign_amount, 22.50)
        self.assertEqual(day.amount, 31.80)

    def test_country_with_most_hours_decides(self):
        # Day 2: 10 h in Austria, 8 h in Germany (equal rates, but Austria wins).
        order = self._order([(self.at, False), (self.de, datetime(2026, 6, 9, 8))])
        self.assertEqual(order.day_ids[1].country_id, self.at)

    def test_country_visited_twice_adds_up(self):
        # Day 2 (local): Austria 00-06, Germany 06-14, Austria 14-18 = 10 h
        # in Austria against 8 in Germany, though Germany has the longest stay.
        order = self._order([
            (self.at, False),
            (self.de, datetime(2026, 6, 9, 4)),
            (self.at, datetime(2026, 6, 9, 12)),
        ])
        self.assertEqual(order.day_ids[1].country_id, self.at)

    def test_later_countries_need_an_arrival(self):
        with self.assertRaises(UserError):
            self._order([(self.at, False), (self.de, False)])

    def test_road_transport_uses_the_special_rate(self):
        order = self._order([(self.de, False)], road_transport=True)
        self.assertEqual(order.day_ids[0].foreign_base, 63.0)

    def test_special_rate_does_not_reach_back(self):
        # The § 1a rates exist from 30. 1. 2026 only.
        order = self._order(
            [(self.de, False)], road_transport=True,
            date_start=datetime(2026, 1, 12, 5), border_out=datetime(2026, 1, 12, 6),
            border_in=datetime(2026, 1, 12, 20), date_end=datetime(2026, 1, 12, 21),
        )
        self.assertEqual(order.day_ids.foreign_base, 45.0)

    def test_koruna_converts_at_the_first_of_the_month(self):
        czk = self.env.ref("base.CZK")
        czk.active = True
        with self.assertRaises(UserError):
            self._order([(self.cz, False)])
        self.env["res.currency.rate"].create({
            "currency_id": czk.id, "company_id": self.company.id,
            "name": "2026-06-01", "rate": 25.0,
        })
        self.env["res.currency.rate"].create({
            "currency_id": czk.id, "company_id": self.company.id,
            "name": "2026-06-08", "rate": 20.0,  # not the decisive one
        })
        order = self._order([(self.cz, False)])
        first = order.day_ids[0]
        self.assertEqual(first.foreign_currency_id, czk)
        self.assertEqual(first.foreign_amount, 600.0)
        self.assertEqual(first.amount, 24.0)

    def test_time_abroad_must_lie_within_the_trip(self):
        with self.assertRaises(ValidationError):
            self._order([(self.at, False)], border_out=datetime(2026, 6, 8, 3))

    def test_pocket_money_is_capped(self):
        with self.assertRaises(ValidationError):
            self._order([(self.at, False)], pocket_money_percent=45)

    def test_seeded_rates_cover_the_notice(self):
        rates = self.env["l10n.sk.travel.foreign.rate"]
        self.assertEqual(rates.search_count([("date_from", "=", "2013-01-01")]), 193)
        self.assertEqual(rates.search_count([("date_from", "=", "2026-01-30")]), 31)
        ch = rates._for(self.env.ref("base.ch"), date(2026, 6, 1))
        self.assertEqual((ch.currency_id.name, ch.rate), ("CHF", 80.0))
