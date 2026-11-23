# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The month that is still open for payroll gets its holidays unasked.

Payroll for a month is computed early in the next one. The working
calendars are therefore kept from the first day of the previous calendar
month: on 5 September 2031 from 1 August, which holds 29 August (a Friday)
and leaves 5 July out.
"""

from contextlib import contextmanager
from datetime import date
from unittest.mock import patch

from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged

from ..hooks import post_init_hook
from ..models.calendar_public_holiday import days_of_rest


@tagged("post_install", "-at_install")
class TestHolidayOpenMonth(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Holiday = cls.env["calendar.public.holiday"]
        cls.Leave = cls.env["resource.calendar.leaves"]
        cls.sk = cls.env.ref("base.sk")
        cls.sk_company = cls.env["res.company"].create(
            {"name": "SK open month", "country_id": cls.sk.id}
        )
        cls.Holiday.search([("year", "in", (2031, 2032, 2033))]).unlink()

    def _days(self, company=None):
        """The days the company has from the holiday lines."""
        leaves = self.Leave.search(
            [
                ("company_id", "=", (company or self.sk_company).id),
                ("resource_id", "=", False),
                ("l10n_cssk_public_holiday_line_id", "!=", False),
            ]
        )
        return sorted(leaves.mapped("l10n_cssk_public_holiday_line_id.date"))

    @staticmethod
    def _slovak_days(first, *years):
        return [
            day
            for year in years
            for day, _name, _variable in days_of_rest("SK", year)
            if day >= first
        ]

    @contextmanager
    def _changes(self):
        """Collect what is created, written or removed among the calendar leaves."""
        Model = self.env.registry["resource.calendar.leaves"]
        create, write, unlink = Model.create, Model.write, Model.unlink
        seen = []

        def spy_create(records, vals_list):
            seen.append("create")
            return create(records, vals_list)

        def spy_write(records, vals):
            if records:
                seen.append("write")
            return write(records, vals)

        def spy_unlink(records):
            if records:
                seen.append("unlink")
            return unlink(records)

        with (
            patch.object(Model, "create", spy_create),
            patch.object(Model, "write", spy_write),
            patch.object(Model, "unlink", spy_unlink),
        ):
            yield seen

    def test_installed_early_in_a_month_the_month_before_is_written(self):
        cron = self.env.ref("l10n_cssk_public_holidays.ir_cron_cssk_public_holidays")
        Trigger = self.env["ir.cron.trigger"]
        before = Trigger.search_count([("cron_id", "=", cron.id)])
        with freeze_time("2031-09-05"):
            post_init_hook(self.env)
            # The hook leaves the calendars to the scheduled action.
            self.assertEqual(self._days(), [])
            self.assertEqual(
                Trigger.search_count([("cron_id", "=", cron.id)]), before + 1
            )
            self.Holiday.cssk_generate_next_year()
        days = self._days()
        self.assertEqual(days, self._slovak_days(date(2031, 8, 1), 2031, 2032))
        self.assertEqual(days[0], date(2031, 8, 29))
        self.assertNotIn(date(2031, 7, 5), days)

    def test_the_window_starts_on_the_first_day_of_the_month_before(self):
        self.Holiday.cssk_generate(years=(2031,), country_codes=("SK",))
        with freeze_time("2031-06-30"):
            # 1 May is the first day of the window, 8 May inside it.
            self.Holiday.cssk_sync_calendar_leaves()
        self.assertEqual(self._days(), self._slovak_days(date(2031, 5, 1), 2031))
        self.assertEqual(self._days()[0], date(2031, 5, 1))

    def test_in_january_the_window_reaches_into_the_year_before(self):
        with freeze_time("2032-01-05"):
            post_init_hook(self.env)
            self.Holiday.cssk_generate_next_year()
        days = self._days()
        self.assertEqual(days, self._slovak_days(date(2031, 12, 1), 2031, 2032, 2033))
        self.assertEqual(days[:3], [date(2031, 12, 24), date(2031, 12, 25), date(2031, 12, 26)])
        self.assertNotIn(date(2031, 11, 1), days)

    def test_a_second_run_changes_nothing(self):
        with freeze_time("2031-09-05"):
            with self._changes() as first:
                self.Holiday.cssk_generate_next_year()
            self.assertEqual(set(first), {"create"})
            with self._changes() as second:
                self.Holiday.cssk_generate_next_year()
                self.Holiday.cssk_sync_calendar_leaves()
            self.assertEqual(second, [])

    def test_a_company_added_later_gets_the_window_of_its_first_run(self):
        with freeze_time("2031-09-05"):
            self.Holiday.cssk_generate_next_year()
            first = self.env["res.company"].create(
                {"name": "SK added in September", "country_id": self.sk.id}
            )
            self.assertEqual(self._days(first), [])
            self.Holiday.cssk_generate_next_year()
            self.assertEqual(self._days(first), self._days())
            self.assertEqual(self._days(first)[0], date(2031, 8, 29))
        with freeze_time("2031-10-05"):
            second = self.env["res.company"].create(
                {"name": "SK added in October", "country_id": self.sk.id}
            )
            with self._changes() as seen:
                self.Holiday.cssk_generate_next_year()
            # Only the newcomer is written; its window starts on 1 September.
            self.assertEqual(set(seen), {"create"})
            self.assertEqual(self._days(second)[0], date(2031, 9, 15))
            self.assertEqual(self._days()[0], date(2031, 8, 29))

    def test_an_earlier_day_given_reaches_further_back(self):
        with freeze_time("2031-09-05"):
            self.Holiday.cssk_generate_next_year()
            self.assertNotIn(date(2031, 7, 5), self._days())
            self.Holiday.cssk_sync_calendar_leaves(date_from=date(2031, 7, 1))
        self.assertEqual(self._days()[:2], [date(2031, 7, 5), date(2031, 8, 29)])

    def test_time_off_recounts_the_open_month_once(self):
        if "hr.leave" not in self.env:
            self.skipTest("Time Off is not installed")
        self.env.user.company_ids |= self.sk_company
        calendar = self.env["resource.calendar"].create(
            {"name": "SK 40h/week", "company_id": self.sk_company.id}
        )
        employee = self.env["hr.employee"].create(
            {
                "name": "Holiday maker",
                "company_id": self.sk_company.id,
                "resource_calendar_id": calendar.id,
            }
        )
        leave_type = self.env["hr.leave.type"].create(
            {
                "name": "From an allocation",
                "requires_allocation": True,
                "leave_validation_type": "no_validation",
                "allocation_validation_type": "no_validation",
                "company_id": self.sk_company.id,
            }
        )
        with freeze_time("2031-09-05"):
            allocation = (
                self.env["hr.leave.allocation"]
                .with_company(self.sk_company)
                .create(
                    {
                        "name": "2031",
                        "employee_id": employee.id,
                        "holiday_status_id": leave_type.id,
                        "number_of_days": 20,
                        "date_from": date(2031, 1, 1),
                    }
                )
            )
            if allocation.state != "validate":
                allocation.action_approve()
            # Monday 25 to Friday 29 August 2031, the Friday a holiday.
            leave = (
                self.env["hr.leave"]
                .with_company(self.sk_company)
                .create(
                    {
                        "name": "The last week of August",
                        "employee_id": employee.id,
                        "holiday_status_id": leave_type.id,
                        "request_date_from": date(2031, 8, 25),
                        "request_date_to": date(2031, 8, 29),
                    }
                )
            )
            if leave.state != "validate":
                leave.action_approve()
            self.assertEqual(leave.number_of_days, 5.0)
            messages = len(leave.message_ids)
            self.Holiday.cssk_generate_next_year()
            self.assertEqual(leave.number_of_days, 4.0)
            self.assertEqual(leave.state, "validate")
            # Time Off tells the employee of the day given back.
            self.assertEqual(len(leave.message_ids), messages + 1)
            self.Holiday.cssk_generate_next_year()
            self.assertEqual(leave.number_of_days, 4.0)
            self.assertEqual(len(leave.message_ids), messages + 1)
