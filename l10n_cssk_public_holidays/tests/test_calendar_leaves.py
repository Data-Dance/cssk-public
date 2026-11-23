# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The holiday lines as public holidays of the working calendars."""

from datetime import date, datetime

import pytz

from odoo.tests import TransactionCase, tagged

from ..models.calendar_public_holiday import LEAVE_COUNTRIES_PARAM


@tagged("post_install", "-at_install")
class TestHolidayCalendarLeaves(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Holiday = cls.env["calendar.public.holiday"]
        cls.Line = cls.env["calendar.public.holiday.line"]
        cls.Leave = cls.env["resource.calendar.leaves"]
        cls.sk = cls.env.ref("base.sk")
        cls.cz = cls.env.ref("base.cz")
        cls.sk_company = cls.env["res.company"].create(
            {"name": "SK holidays", "country_id": cls.sk.id}
        )
        cls.cz_company = cls.env["res.company"].create(
            {"name": "CZ holidays", "country_id": cls.cz.id}
        )
        cls.other_company = cls.env["res.company"].create(
            {"name": "US holidays", "country_id": cls.env.ref("base.us").id}
        )
        cls.Holiday.search([("year", "in", (2020, 2031))]).unlink()
        # The tests start from the default list of countries.
        cls.env["ir.config_parameter"].search(
            [("key", "=", LEAVE_COUNTRIES_PARAM)]
        ).unlink()

    def _line_leaves(self, line, company=None):
        company = company or self.sk_company
        return line._cssk_calendar_leaves().filtered(
            lambda leave: leave.company_id == company
        )

    def _leaves(self, company, year=2031):
        return self.Leave.search(
            [
                ("company_id", "=", company.id),
                ("resource_id", "=", False),
                ("date_from", ">=", datetime(year - 1, 12, 31)),
                ("date_to", "<=", datetime(year, 12, 31, 23, 59, 59)),
            ]
        )

    def _generate(self, year=2031, countries=("SK", "CZ")):
        """Generate a year and run the sweep the scheduled action runs."""
        holidays = self.Holiday.cssk_generate(years=(year,), country_codes=countries)
        self.Holiday.cssk_sync_calendar_leaves()
        return holidays

    def _hand_made(self, company, day):
        # The company of a public holiday without a calendar is the active one.
        return self.Leave.with_company(company).create(
            {
                "name": "Entered by hand",
                "company_id": company.id,
                "date_from": datetime(day.year, day.month, day.day, 0, 0, 0),
                "date_to": datetime(day.year, day.month, day.day, 20, 0, 0),
            }
        )

    def test_slovak_company_gets_one_public_holiday_per_line(self):
        holiday = self._generate().filtered(lambda rec: rec.country_id == self.sk)
        leaves = self._leaves(self.sk_company)
        self.assertEqual(len(leaves), 13)
        self.assertEqual(leaves.l10n_cssk_public_holiday_line_id, holiday.line_ids)
        self.assertEqual(leaves.company_id, self.sk_company)
        self.assertFalse(leaves.calendar_id)
        self.assertFalse(leaves.resource_id)
        self.assertEqual(set(leaves.mapped("time_type")), {"leave"})
        # The calendar day in Slovakia: 1 May 2031 is on summer time.
        labour_day = leaves.filtered(
            lambda leave: leave.l10n_cssk_public_holiday_line_id.date == date(2031, 5, 1)
        )
        self.assertEqual(labour_day.date_from, datetime(2031, 4, 30, 22, 0, 0))
        self.assertEqual(labour_day.date_to, datetime(2031, 5, 1, 21, 59, 59))
        self.assertEqual(labour_day.name, "Sviatok práce")
        new_year = leaves.filtered(
            lambda leave: leave.l10n_cssk_public_holiday_line_id.date == date(2031, 1, 1)
        )
        self.assertEqual(new_year.date_from, datetime(2030, 12, 31, 23, 0, 0))

    def test_other_countries_are_left_alone_by_default(self):
        self._generate()
        self.assertFalse(self._leaves(self.cz_company))
        self.assertFalse(self._leaves(self.other_company))

    def test_czech_companies_join_through_the_parameter(self):
        self.env["ir.config_parameter"].set_param(LEAVE_COUNTRIES_PARAM, "SK, CZ")
        self._generate()
        czech = self._leaves(self.cz_company)
        self.assertEqual(len(czech), 13)
        self.assertEqual(
            set(czech.l10n_cssk_public_holiday_line_id.public_holiday_id.country_id.ids),
            {self.cz.id},
        )
        self.assertEqual(len(self._leaves(self.sk_company)), 13)
        self.assertFalse(self._leaves(self.other_company))

    def test_switching_a_country_off_removes_its_coming_holidays(self):
        self._generate()
        # An empty value would remove the parameter and bring the default back.
        self.env["ir.config_parameter"].set_param(LEAVE_COUNTRIES_PARAM, "none")
        self.Holiday.cssk_sync_calendar_leaves()
        self.assertFalse(self._leaves(self.sk_company))

    def test_generating_again_adds_nothing(self):
        self._generate()
        before = self._leaves(self.sk_company)
        self._generate()
        self.Holiday.cssk_sync_calendar_leaves()
        self.assertEqual(self._leaves(self.sk_company), before)

    def test_the_holiday_is_no_working_time(self):
        self._generate()
        calendar = self.env["resource.calendar"].create(
            {
                "name": "SK 40h/week",
                "company_id": self.sk_company.id,
                "tz": "Europe/Bratislava",
            }
        )
        tz = pytz.timezone("Europe/Bratislava")
        # Thursday 1 May and Friday 2 May 2031
        start = tz.localize(datetime(2031, 5, 1, 0, 0, 0))
        stop = tz.localize(datetime(2031, 5, 2, 23, 59, 59))
        self.assertEqual(calendar.get_work_hours_count(start, stop, compute_leaves=False), 16.0)
        self.assertEqual(calendar.get_work_hours_count(start, stop, compute_leaves=True), 8.0)

    def test_a_line_renamed_moved_or_removed_takes_its_leave_along(self):
        holiday = self._generate(countries=("SK",))
        line = holiday.line_ids.filtered(lambda rec: rec.date == date(2031, 8, 29))
        second = self.env["res.company"].create(
            {"name": "SK second", "country_id": self.sk.id}
        )
        self.Holiday.cssk_sync_calendar_leaves()
        leave = self._line_leaves(line)
        self.assertEqual(len(leave), 1)
        line.name = "Výročie SNP"
        self.assertEqual(leave.name, "Výročie SNP")
        line.date = date(2031, 8, 28)
        for company in (self.sk_company, second):
            leave = self._line_leaves(line, company)
            self.assertEqual(len(leave), 1, company.name)
            self.assertEqual(leave.date_from, datetime(2031, 8, 27, 22, 0, 0))
            self.assertEqual(leave.date_to, datetime(2031, 8, 28, 21, 59, 59))
            self.assertEqual(leave.name, "Výročie SNP")
        line.unlink()
        self.assertFalse(leave.exists())
        self.assertEqual(len(self._leaves(self.sk_company)), 12)
        self.assertEqual(len(self._leaves(second)), 12)

    def test_a_regional_line_has_no_leave(self):
        holiday = self._generate(countries=("SK",))
        state = self.env["res.country.state"].create(
            {"name": "Test kraj", "code": "TK", "country_id": self.sk.id}
        )
        line = self.Line.create(
            {
                "public_holiday_id": holiday.id,
                "date": date(2031, 3, 3),
                "name": "Regional",
                "state_ids": [(6, 0, state.ids)],
            }
        )
        self.assertFalse(line._cssk_calendar_leaves())
        nationwide = holiday.line_ids.filtered(lambda rec: rec.date == date(2031, 7, 5))
        self.assertTrue(self._line_leaves(nationwide))
        nationwide.state_ids = state
        self.assertFalse(nationwide._cssk_calendar_leaves())

    def test_removing_the_year_removes_its_leaves(self):
        holiday = self._generate(countries=("SK",))
        self.assertTrue(self._leaves(self.sk_company))
        holiday.unlink()
        self.assertFalse(self._leaves(self.sk_company))

    def test_a_public_holiday_entered_by_hand_is_kept_and_not_doubled(self):
        by_hand = self._hand_made(self.sk_company, date(2031, 5, 1))
        holiday = self._generate(countries=("SK",))
        self.assertEqual(by_hand.company_id, self.sk_company)
        line = holiday.line_ids.filtered(lambda rec: rec.date == date(2031, 5, 1))
        self.assertFalse(self._line_leaves(line))
        self.assertEqual(len(self._leaves(self.sk_company)), 13)
        # A line moved onto a day entered by hand gives its leave up.
        other = holiday.line_ids.filtered(lambda rec: rec.date == date(2031, 7, 5))
        self.assertTrue(self._line_leaves(other))
        self._hand_made(self.sk_company, date(2031, 7, 4))
        other.date = date(2031, 7, 4)
        self.assertFalse(self._line_leaves(other))

    def test_a_past_year_is_not_put_into_the_calendars_on_its_own(self):
        holiday = self._generate(year=2020, countries=("SK",))
        self.assertEqual(len(holiday.line_ids), 15)
        self.assertFalse(self._leaves(self.sk_company, 2020))
        self.Holiday.cssk_sync_calendar_leaves()
        self.assertFalse(self._leaves(self.sk_company, 2020))
        # On request, from the day given.
        self.Holiday.cssk_sync_calendar_leaves(date_from=date(2020, 7, 1))
        days = self._leaves(self.sk_company, 2020).mapped(
            "l10n_cssk_public_holiday_line_id.date"
        )
        self.assertEqual(min(days), date(2020, 7, 5))
        self.assertEqual(len(days), 9)

    def test_a_line_added_by_hand_reaches_the_calendars_whatever_its_date(self):
        holiday = self._generate(year=2020, countries=("SK",))
        line = self.Line.create(
            {"public_holiday_id": holiday.id, "date": date(2020, 3, 3), "name": "Extra"}
        )
        self.assertEqual(len(self._line_leaves(line)), 1)

    def test_generating_alone_leaves_the_calendars_to_the_scheduled_action(self):
        self.Holiday.cssk_generate(years=(2031,), country_codes=("SK",))
        self.assertFalse(self._leaves(self.sk_company))
        self.Holiday.cssk_generate_next_year()
        self.assertEqual(len(self._leaves(self.sk_company)), 13)

    def test_install_and_upgrade_ask_the_scheduled_action_to_run(self):
        cron = self.env.ref("l10n_cssk_public_holidays.ir_cron_cssk_public_holidays")
        Trigger = self.env["ir.cron.trigger"]
        before = Trigger.search_count([("cron_id", "=", cron.id)])
        self.assertTrue(self.Holiday.cssk_run_scheduled_action_soon())
        self.assertEqual(Trigger.search_count([("cron_id", "=", cron.id)]), before + 1)

    def test_the_leave_belongs_to_the_company_not_to_the_active_one(self):
        self._generate(countries=("SK",))
        leaves = self._leaves(self.sk_company)
        self.assertNotEqual(self.env.company, self.sk_company)
        self.assertEqual(leaves.company_id, self.sk_company)

    def test_a_new_company_is_reached_by_the_scheduled_action(self):
        self._generate(countries=("SK",))
        newcomer = self.env["res.company"].create(
            {"name": "SK newcomer", "country_id": self.sk.id}
        )
        self.assertFalse(self._leaves(newcomer))
        self.Holiday.cssk_generate_next_year()
        self.assertEqual(len(self._leaves(newcomer)), 13)

    def test_a_company_that_leaves_the_country_loses_its_coming_holidays(self):
        self._generate(countries=("SK",))
        stays = self.env["res.company"].create(
            {"name": "SK stays", "country_id": self.sk.id}
        )
        self.Holiday.cssk_sync_calendar_leaves()
        self.assertEqual(len(self._leaves(stays)), 13)
        self.sk_company.country_id = self.env.ref("base.us")
        self.Holiday.cssk_sync_calendar_leaves()
        self.assertFalse(self._leaves(self.sk_company))
        self.assertEqual(len(self._leaves(stays)), 13)

    def test_time_off_does_not_count_the_holiday(self):
        if "hr.leave" not in self.env:
            self.skipTest("Time Off is not installed")
        self._generate(countries=("SK",))
        calendar = self.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": self.sk_company.id}
        )
        self.env.user.company_ids |= self.sk_company
        employee = self.env["hr.employee"].create(
            {
                "name": "Holiday maker",
                "company_id": self.sk_company.id,
                "resource_calendar_id": calendar.id,
            }
        )
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "Unlimited",
                "requires_allocation": False,
                "company_id": self.sk_company.id,
            }
        )
        # Monday 28 April to Monday 5 May 2031, 1 May on a Thursday.
        leave = (
            self.env["hr.leave"]
            .with_company(self.sk_company)
            .create(
                {
                    "name": "Across the holiday",
                    "employee_id": employee.id,
                    "holiday_status_id": leave_type.id,
                    "request_date_from": date(2031, 4, 28),
                    "request_date_to": date(2031, 5, 5),
                }
            )
        )
        self.assertEqual(leave.number_of_days, 5.0)
