# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from datetime import date

from odoo.tests import TransactionCase, tagged

from ..models.calendar_public_holiday import days_of_rest, easter_sunday


@tagged("post_install", "-at_install")
class TestPublicHolidays(TransactionCase):
    def test_easter(self):
        self.assertEqual(easter_sunday(2024), date(2024, 3, 31))
        self.assertEqual(easter_sunday(2025), date(2025, 4, 20))
        self.assertEqual(easter_sunday(2026), date(2026, 4, 5))
        self.assertEqual(easter_sunday(2027), date(2027, 3, 28))

    def test_sk_2026_working_day_exceptions(self):
        days = {d: n for d, n, _ in days_of_rest("SK", 2026)}
        self.assertNotIn(date(2026, 5, 8), days)
        self.assertNotIn(date(2026, 9, 15), days)
        self.assertNotIn(date(2026, 11, 17), days)
        self.assertIn(date(2026, 4, 3), days)  # Veľký piatok
        self.assertIn(date(2026, 4, 6), days)  # Veľkonočný pondelok
        self.assertEqual(len(days), 11)

    def test_sk_2027_restored(self):
        days = {d for d, _, _ in days_of_rest("SK", 2027)}
        self.assertIn(date(2027, 5, 8), days)
        self.assertIn(date(2027, 9, 15), days)
        self.assertNotIn(date(2027, 11, 17), days)
        self.assertNotIn(date(2027, 9, 1), days)
        self.assertEqual(len(days), 13)

    def test_sk_2025_17_november_is_a_working_day(self):
        days = {d for d, _, _ in days_of_rest("SK", 2025)}
        self.assertNotIn(date(2025, 11, 17), days)
        self.assertIn(date(2025, 9, 15), days)
        self.assertEqual(len(days), 13)

    def test_sk_before_the_changes(self):
        days = {d for d, _, _ in days_of_rest("SK", 2023)}
        self.assertIn(date(2023, 9, 1), days)
        self.assertIn(date(2023, 11, 17), days)
        self.assertEqual(len(days), 15)

    def test_cz_2026(self):
        days = {d: n for d, n, _ in days_of_rest("CZ", 2026)}
        self.assertEqual(len(days), 13)
        self.assertIn(date(2026, 4, 3), days)
        self.assertIn(date(2026, 4, 6), days)
        self.assertIn(date(2026, 7, 6), days)
        self.assertNotIn(date(2026, 1, 6), days)
        # Good Friday only since 2016
        self.assertEqual(len(days_of_rest("CZ", 2015)), 12)

    def test_generate_is_idempotent_and_keeps_edits(self):
        Holiday = self.env["calendar.public.holiday"]
        sk = self.env.ref("base.sk")
        Holiday.search([("year", "=", 2031), ("country_id", "=", sk.id)]).unlink()
        first = Holiday.cssk_generate(years=(2031,), country_codes=("SK",))
        self.assertEqual(len(first), 1)
        self.assertEqual(len(first.line_ids), 13)
        line = first.line_ids.filtered(lambda l: l.date == date(2031, 1, 6))
        line.name = "Traja králi (upravené)"
        line_to_drop = first.line_ids.filtered(lambda l: l.date == date(2031, 5, 1))
        line_to_drop.unlink()
        again = Holiday.cssk_generate(years=(2031,), country_codes=("SK",))
        self.assertEqual(again, first)
        self.assertEqual(len(again.line_ids), 13)
        self.assertEqual(line.name, "Traja králi (upravené)")
        self.assertTrue(again.line_ids.filtered(lambda l: l.date == date(2031, 5, 1)))

    def test_a_regional_line_does_not_hide_the_nationwide_day(self):
        Holiday = self.env["calendar.public.holiday"]
        sk = self.env.ref("base.sk")
        Holiday.search([("year", "=", 2032), ("country_id", "=", sk.id)]).unlink()
        state = self.env["res.country.state"].create(
            {"name": "Test kraj", "code": "TK", "country_id": sk.id}
        )
        holiday = Holiday.create({"year": 2032, "country_id": sk.id})
        self.env["calendar.public.holiday.line"].create({
            "public_holiday_id": holiday.id,
            "date": date(2032, 1, 6),
            "name": "Regional",
            "state_ids": [(6, 0, state.ids)],
        })
        Holiday.cssk_generate(years=(2032,), country_codes=("SK",))
        nationwide = holiday.line_ids.filtered(
            lambda l: l.date == date(2032, 1, 6) and not l.state_ids
        )
        self.assertEqual(len(nationwide), 1)

    def test_install_loaded_both_countries(self):
        year = date.today().year
        for code in ("SK", "CZ"):
            country = self.env["res.country"].search([("code", "=", code)])
            for y in (year, year + 1):
                rec = self.env["calendar.public.holiday"].search(
                    [("year", "=", y), ("country_id", "=", country.id)]
                )
                self.assertEqual(len(rec), 1, f"{code} {y}")
                self.assertEqual(len(rec.line_ids), len(days_of_rest(code, y)))

    def test_cron_adds_next_year(self):
        year = date.today().year
        Holiday = self.env["calendar.public.holiday"]
        Holiday.search([("year", "=", year + 1)]).unlink()
        Holiday.cssk_generate_next_year()
        self.assertEqual(len(Holiday.search([("year", "=", year + 1)])), 2)
