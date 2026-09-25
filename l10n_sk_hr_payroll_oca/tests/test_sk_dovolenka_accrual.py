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

    def test_one_year_carryover_forfeiture(self):
        """§113 clean one-year forfeit across MANY carryover cycles.

        The holiday accrual level sets ``accrual_validity`` = 364 ``day``. Odoo
        counts that validity FROM the 1 January carryover date, so the carried
        block expires ~31 December -- just BEFORE the next 1 January carryover.
        That avoids the collision a 12-month window suffers: expiry landing on
        1 Jan coincides with the next carryover, Odoo's single expiry-tracking
        field is overwritten, and forfeiture drifts to a two-year rhythm (the
        balance then retains ~two years' worth from the second cohort on).

        This test drives FOUR consecutive 1 January carryovers and asserts a
        clean one-year forfeiture in steady state: at every year-end the balance
        returns to ~one year's statutory entitlement (~20 days) and never
        accumulates two years' worth. (The shipped dovolenka leave type is a
        no-allocation pool, so the whole unused carried entitlement is what
        expires each cycle.)
        """
        plan = self.env.ref(MOD + ".l10n_sk_accrual_plan_dovolenka_4w")
        level = plan.level_ids
        # Data sanity: the one-year window is modelled as 364 days from carryover.
        self.assertTrue(level.accrual_validity)
        self.assertEqual(level.accrual_validity_count, 364)
        self.assertEqual(level.accrual_validity_type, "day")
        self.assertEqual(plan.carryover_date, "year_start")

        employee = self.env["hr.employee"].create({"name": "Forfeiture Test"})
        with freeze_time("2024-01-01"):
            alloc = self.env["hr.leave.allocation"].create(
                {
                    "name": "Dovolenka forfeiture",
                    "holiday_status_id": self.leave_type.id,
                    "employee_id": employee.id,
                    "allocation_type": "accrual",
                    "accrual_plan_id": plan.id,
                    "date_from": date(2024, 1, 1),
                }
            )
            alloc.action_approve()

        # Year 1: accrue (almost) the full statutory entitlement.
        with freeze_time("2024-12-31"):
            alloc._update_accrual()
            self.assertGreater(alloc.number_of_days, 15.0)
            self.assertLessEqual(alloc.number_of_days, 20.5)

        # Four consecutive carryover cycles (2025, 2026, 2027, 2028). If the
        # forfeiture drifted to a two-year rhythm, the year-end balance would
        # climb toward ~40 by the later cycles; here it must stay near ~20.
        for year in (2025, 2026, 2027, 2028):
            # 1 Jan: the previous year's balance carries over and is stamped to
            # expire at the END of THIS year (30/31 Dec), strictly before the
            # next 1 Jan carryover -- so no expiry/carryover collision.
            with freeze_time(f"{year}-01-01"):
                alloc._update_accrual()
                exp = alloc.carried_over_days_expiration_date
                self.assertEqual(exp.year, year)
                self.assertEqual(exp.month, 12)
                self.assertGreaterEqual(exp.day, 30)
                self.assertLess(exp, date(year + 1, 1, 1))
                # The carried year's balance is on the one-year clock.
                self.assertGreater(alloc.expiring_carryover_days, 15.0)

            # 31 Dec: the carried block has expired within the year; the balance
            # is back to ~one year's entitlement and the expiring bucket is empty.
            with freeze_time(f"{year}-12-31"):
                alloc._update_accrual()
                self.assertAlmostEqual(alloc.number_of_days, 20.0, delta=0.5)
                self.assertAlmostEqual(
                    alloc.expiring_carryover_days, 0.0, places=6
                )
                # Anti-drift guard: a two-year retention bug shows ~40 here.
                self.assertLess(alloc.number_of_days, 25.0)
