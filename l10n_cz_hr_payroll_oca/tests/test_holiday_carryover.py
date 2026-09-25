# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# § 218 zákoníku práce (one-year carryover window for dovolená):
# unused annual leave carries into the FOLLOWING calendar year, but leave that is
# still untaken by the end of that following year is forfeited. This is modelled
# on the holiday accrual level's accrual_validity = 364 days, which Odoo counts
# from the 1 Jan carryover date: the carried days therefore expire ~31 Dec of the
# following year -- just BEFORE the next 1 Jan carryover. Using 364 days (rather
# than 12 months, which would collide with the 1 Jan carryover date and drift into
# a two-year retention) yields a clean one-year window in steady state. This test
# drives the accrual engine across six successive year-end expiry / 1 Jan carryover
# cycles and proves the forfeiture keeps exactly one year every cycle.

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
            "l10n_cz_hr_payroll_oca.accrual_plan_cz_holiday_4w")

    def test_holiday_one_year_carryover_then_forfeit(self):
        """Year 1 = 2024; then five steady-state cycles (fixed dates)."""
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
        year1_unused = allocation.number_of_days - allocation.leaves_taken  # ~15

        # --- First carryover (1 Jan 2025): the unused year-1 days roll over and
        #     are flagged to expire at the END of 2025 (31 Dec), strictly before
        #     the next 1 Jan carryover. ---
        with freeze_time("2025-01-01"):
            allocation._process_accrual_plans(date_to=date(2025, 1, 1))
        expiry = allocation.carried_over_days_expiration_date
        self.assertEqual(
            expiry, date(2025, 12, 31),
            "First cohort: carried dovolená expires 31 Dec of the following "
            "year (end of N+1), not on the 1 Jan carryover date.")
        self.assertLess(
            expiry, date(2026, 1, 1),
            "Expiry falls strictly before the next 1 Jan carryover.")
        self.assertAlmostEqual(
            allocation.expiring_carryover_days, 20.0, delta=0.1,
            msg="The year-1 entitlement is flagged as carried-over, expiring days.")
        self.assertAlmostEqual(
            allocation.number_of_days - allocation.leaves_taken, year1_unused,
            delta=0.1, msg="Nothing is forfeited yet at the first carryover.")

        # --- Steady state: five consecutive year-end expiry / 1 Jan carryover
        #     cycles (2025..2029). Each cycle must forfeit the older carried days
        #     and keep only the immediately-preceding year -- a CLEAN one-year
        #     window, never two years. ---
        balances_at_new_year = []
        for year in range(2025, 2030):
            # Mid-December, BEFORE the 31 Dec expiry: the current year plus the
            # prior carried year have accumulated (~two years' worth).
            with freeze_time(date(year, 12, 15).isoformat()):
                allocation._process_accrual_plans(date_to=date(year, 12, 15))
            balance_before_expiry = (
                allocation.number_of_days - allocation.leaves_taken)
            # Across the 31 Dec expiry and the following 1 Jan carryover.
            with freeze_time(date(year + 1, 1, 1).isoformat()):
                allocation._process_accrual_plans(date_to=date(year + 1, 1, 1))
            balance_after = allocation.number_of_days - allocation.leaves_taken
            expiry = allocation.carried_over_days_expiration_date

            self.assertGreater(
                balance_before_expiry, 30.0,
                "Before the year-end expiry, two years of leave have "
                "accumulated (cycle %s)." % year)
            self.assertAlmostEqual(
                balance_after, 20.0, delta=1.0,
                msg="After the year-end forfeiture only ONE year (~20 days) is "
                "retained -- clean one-year carryover, no 2-year drift "
                "(cycle %s)." % year)
            self.assertLess(
                balance_after, 30.0,
                "Steady state must never retain a second full year "
                "(cycle %s)." % year)
            self.assertGreater(
                balance_before_expiry - balance_after, 10.0,
                "A substantial forfeiture happens every cycle (cycle %s)." % year)
            # Carried days always expire at end of December, before the next
            # 1 Jan carryover (30/31 Dec; 30 Dec in leap years).
            self.assertEqual(
                expiry.month, 12, "Expiry is in December (cycle %s)." % year)
            self.assertGreaterEqual(
                expiry.day, 30, "Expiry is at end of December (cycle %s)." % year)
            self.assertLess(
                expiry, date(year + 2, 1, 1),
                "Expiry is strictly before the next 1 Jan carryover "
                "(cycle %s)." % year)
            balances_at_new_year.append(balance_after)

        self.assertTrue(
            all(b < 30.0 for b in balances_at_new_year),
            "Every steady-state cycle retained only one year of leave: %s"
            % balances_at_new_year)
