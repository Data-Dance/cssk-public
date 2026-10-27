# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# § 218 zákoníku práce: unused dovolená carries into the following year and
# NEVER lapses. The employer must schedule it by the end of that following year
# (odst. 3), the employee may schedule it from 1 July (odst. 4), and leave still
# unused when the employment ends is compensated (§ 222 odst. 2). Nothing in the
# Code forfeits it. The plans therefore carry over with no accrual_validity; an
# earlier version expired the carried hours after 364 days, which wiped a lawful
# claim from the balance every 31 December. This test drives the accrual engine
# across several year-end carryovers and proves nothing is ever taken away.

from datetime import date

from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCzHolidayCarryover(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref(
            "hr_holidays.group_hr_holidays_manager")
        cls.company = cls.env["res.company"].create({
            "name": "CZ Carryover Co",
            "country_id": cls.env.ref("base.cz").id,
        })
        cls.env = cls.env(context=dict(
            cls.env.context, allowed_company_ids=cls.company.ids))
        cls.calendar = cls.env["resource.calendar"].create({
            "name": "CZ 40h/week", "company_id": cls.company.id,
        })
        # Generic dovolená leave type the statutory 4-week plan is allocated on.
        cls.leave_type = cls.env["hr.leave.type"].create({
            "name": "Dovolená (test)",
            "time_type": "leave",
            "requires_allocation": True,
            "allocation_validation_type": "no_validation",
            "leave_validation_type": "no_validation",
            "request_unit": "day",
            "company_id": cls.company.id,
        })
        cls.plan = cls.env.ref(
            "l10n_cz_hr_payroll_base.accrual_plan_cz_holiday_4w")

    def test_holiday_carryover_never_forfeited(self):
        """Year 1 = 2024; then several carryovers (fixed dates)."""
        with freeze_time("2024-01-01"):
            employee = self.env["hr.employee"].with_company(self.company).create({
                "name": "Dovolená Emp",
                "company_id": self.company.id,
                "resource_calendar_id": self.calendar.id,
                "date_version": date(2024, 1, 1),
                "contract_date_start": date(2024, 1, 1),
                "wage": 40000,
            })
            allocation = self.env["hr.leave.allocation"].create({
                "name": "Dovolená accrual",
                "allocation_type": "accrual",
                "accrual_plan_id": self.plan.id,
                "employee_id": employee.id,
                "holiday_status_id": self.leave_type.id,
                "number_of_days": 0,
                "date_from": date(2024, 1, 1),
            })
            allocation.action_approve()

        self.assertFalse(
            self.plan.level_ids.mapped("accrual_validity")[0],
            "§ 218 has no forfeiture: carried-over dovolená must not expire.")

        # --- Year 1 (2024): a full worked year accrues the 4-week entitlement
        #     (160 h = 20 days at 8 h/day). ---
        with freeze_time("2024-12-31"):
            allocation._process_accrual_plans(date_to=date(2024, 12, 31))
        self.assertAlmostEqual(
            allocation.number_of_days, 20.0, delta=0.1,
            msg="A full worked year accrues the statutory 4 weeks (20 days).")

        # Take 5 working days (Mon-Fri) -> 15 days remain unused in year 1.
        with freeze_time("2024-12-31"):
            leave = self.env["hr.leave"].with_company(self.company).create({
                "name": "Dovolená čerpání",
                "employee_id": employee.id,
                "holiday_status_id": self.leave_type.id,
                "request_date_from": date(2024, 3, 4),
                "request_date_to": date(2024, 3, 8),
            })
            if leave.state == "draft":
                leave.action_confirm()
            if leave.state == "confirm":
                leave.action_approve()
        self.assertAlmostEqual(allocation.leaves_taken, 5.0, delta=0.01)
        balance = allocation.number_of_days - allocation.leaves_taken  # ~15

        # --- Carryovers 1 Jan 2025 .. 1 Jan 2029: the unused balance rolls over
        #     every year and is never cut. Each worked year adds ~20 days; with
        #     no leave taken the balance grows by that much every year. ---
        for year in range(2025, 2030):
            with freeze_time(date(year, 1, 1).isoformat()):
                allocation._process_accrual_plans(date_to=date(year, 1, 1))
            self.assertFalse(
                allocation.carried_over_days_expiration_date,
                "No expiry date is set on carried-over dovolená (%s)." % year)
            after_carryover = allocation.number_of_days - allocation.leaves_taken
            self.assertGreaterEqual(
                after_carryover, balance - 0.1,
                "The 1 Jan carryover removes nothing (%s)." % year)
            # Across the whole following year, including 31 December, where the
            # old 364-day validity used to cut the carried days.
            with freeze_time(date(year + 1, 1, 1).isoformat()):
                allocation._process_accrual_plans(date_to=date(year, 12, 31))
            year_end = allocation.number_of_days - allocation.leaves_taken
            self.assertAlmostEqual(
                year_end, after_carryover + 20.0, delta=1.0,
                msg="A worked year adds its entitlement and nothing carried is "
                "forfeited at year end (%s)." % year)
            balance = year_end

        # Six worked years (2024..2029) less the 5 days taken.
        self.assertAlmostEqual(balance, 6 * 20.0 - 5.0, delta=3.0)
