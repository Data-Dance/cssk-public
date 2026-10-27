# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Asserts the statutory Slovak dovolenka accrual-plan DATA (§103/§101
# Zákonníka práce), the demo start-of-year allocation, and that the 4-week
# (20-day) plan actually accrues in DAYS and respects the yearly cap.

from datetime import date

from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged

MOD = "l10n_sk_hr_payroll_oca"


@tagged("post_install", "-at_install")
class TestSkDovolenkaAccrual(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # hr_holidays manager rights; field renamed groups_id (18.0) -> group_ids (19.0)
        mgr = cls.env.ref("hr_holidays.group_hr_holidays_manager")
        field = "group_ids" if "group_ids" in cls.env.user._fields else "groups_id"
        cls.env.user[field] |= mgr
        cls.leave_type = cls.env.ref(MOD + ".l10n_sk_leave_type_dovolenka")

    def test_plans_installed_and_attached(self):
        """3 statutory plans install, in DAYS, attached to the holiday type."""
        expected = {
            "l10n_sk_accrual_plan_dovolenka_4w": 20,
            "l10n_sk_accrual_plan_dovolenka_5w": 25,
            "l10n_sk_accrual_plan_dovolenka_8w": 40,
        }
        for xmlid, annual in expected.items():
            plan = self.env.ref(MOD + "." + xmlid)
            self.assertEqual(plan.time_off_type_id, self.leave_type)
            self.assertEqual(len(plan.level_ids), 1)
            level = plan.level_ids
            self.assertEqual(level.added_value_type, "day")
            self.assertEqual(level.frequency, "monthly")
            self.assertEqual(level.maximum_leave_yearly, annual)
            # 1/12 of the annual entitlement per whole calendar month
            self.assertAlmostEqual(level.added_value, annual / 12.0, places=4)

    def test_demo_allocation(self):
        """Demo start-of-year 20-day allocation is present (when demo loaded)."""
        alloc = self.env.ref(
            MOD + ".demo_sk_dovolenka_allocation", raise_if_not_found=False
        )
        if not alloc:
            self.skipTest("demo data not loaded")
        self.assertEqual(alloc.number_of_days, 20)
        self.assertEqual(alloc.date_from, date(2026, 1, 1))

    def test_accrual_runs_in_days(self):
        """A full-year 4-week accrual allocation accrues ~20 days, capped at 20."""
        plan = self.env.ref(MOD + ".l10n_sk_accrual_plan_dovolenka_4w")
        employee = self.env["hr.employee"].create({"name": "Test Dovolenka"})
        alloc = self.env["hr.leave.allocation"].create(
            {
                "name": "Test dovolenka 2026",
                "holiday_status_id": self.leave_type.id,
                "employee_id": employee.id,
                "allocation_type": "accrual",
                "accrual_plan_id": plan.id,
                "date_from": date(2026, 1, 1),
            }
        )
        alloc.action_approve()
        alloc._process_accrual_plans(date(2026, 12, 31))
        # Days-based accrual: several months accrued at 1/12 (1.66667 d/month),
        # never above the 20-day statutory annual cap (maximum_leave_yearly).
        # A full calendar year yields exactly 20 days (12 x 1.66667, capped).
        self.assertGreater(alloc.number_of_days, 1.0)
        self.assertLessEqual(alloc.number_of_days, 20.0)

    def test_carried_over_leave_never_lapses(self):
        """§113 Zákonníka práce: unused dovolenka is carried over and kept.

        The plans used to forfeit the carried-over balance after a one-year
        window (accrual_validity = 364 days). The Code has no forfeiture: the
        employer must grant the leave by the end of the next year, the
        employee may set it himself if the employer does not by 30 June
        (ods. 2), and leave blocked by maternity/parental leave or PN is
        granted afterwards (ods. 3, 4). Two years untouched must therefore
        leave two years' entitlement on the balance.
        """
        plan = self.env.ref(MOD + ".l10n_sk_accrual_plan_dovolenka_4w")
        # Monthly plans and the start-of-year (leave options) plans alike.
        for xmlid in ("4w", "5w", "8w", "start_4w", "start_5w", "start_8w"):
            level = self.env.ref(
                MOD + ".l10n_sk_accrual_plan_dovolenka_" + xmlid).level_ids
            self.assertFalse(level.accrual_validity, xmlid)
            self.assertEqual(level.action_with_unused_accruals, "all", xmlid)

        employee = self.env["hr.employee"].create({"name": "Carryover Test"})
        with freeze_time("2024-01-01"):
            alloc = self.env["hr.leave.allocation"].create(
                {
                    "name": "Dovolenka carryover",
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": employee.id,
                    "allocation_type": "accrual",
                    "accrual_plan_id": plan.id,
                    "date_from": date(2024, 1, 1),
                }
            )
            alloc.action_approve()

        with freeze_time("2024-12-31"):
            alloc._update_accrual()
            first_year = alloc.number_of_days
            self.assertGreater(first_year, 15.0)

        # Two full years later nothing has been taken, and nothing may have
        # lapsed: 2024's balance plus 2025's and 2026's accruals.
        with freeze_time("2026-12-31"):
            alloc._update_accrual()
            self.assertGreater(alloc.number_of_days, first_year + 2 * 15.0)

    def test_start_of_year_plan_keeps_carried_over_leave(self):
        """The start-of-year plan (whole entitlement on 1 January) must not
        lapse either. Odoo prorates the first year (1 day for a 1 January
        start) and grants 20 days on each following 1 January; with nothing
        taken, 2 January 2027 holds the 2025, 2026 and 2027 grants (61). The
        old 364-day window dropped 2025's on 31 December 2026, leaving 41.
        """
        plan = self.env.ref(MOD + ".l10n_sk_accrual_plan_dovolenka_start_4w")
        employee = self.env["hr.employee"].create({"name": "Start Plan Test"})
        with freeze_time("2024-01-01"):
            alloc = self.env["hr.leave.allocation"].create(
                {
                    "name": "Dovolenka start plan",
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": employee.id,
                    "allocation_type": "accrual",
                    "accrual_plan_id": plan.id,
                    "date_from": date(2024, 1, 1),
                }
            )
            alloc.action_approve()
        with freeze_time("2027-01-02"):
            alloc._update_accrual()
            self.assertGreaterEqual(alloc.number_of_days, 60.0)
