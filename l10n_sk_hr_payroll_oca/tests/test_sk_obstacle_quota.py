# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# The §141 paid-obstacle reasons that carry an ANNUAL day-cap (vyšetrenie 7,
# sprevádzanie 7, sprevádzanie ZŤP dieťaťa 10) each get their own leave type
# with requires_allocation=True, so the cap is enforced when the leave is
# booked. Asserts that they are genuinely separate balances — sharing one
# leave type would pool them into a single 24-day pot — while the generic
# paid-obstacle type stays bookable without any allocation, because the
# per-EVENT reasons (svadba, úmrtie, narodenie, darovanie krvi) have no quota.

from datetime import date

from freezegun import freeze_time

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

MOD = "l10n_sk_hr_payroll_oca"

# 2 Mar 2026 is a Monday; 2–10 March spans exactly 7 working days.
QUOTA_FROM = date(2026, 3, 2)
QUOTA_TO = date(2026, 3, 10)
ONE_DAY_TOO_MANY = date(2026, 3, 11)

CAPPED = {
    "l10n_sk_accrual_plan_obstacle_exam_7d": (
        "l10n_sk_leave_type_obstacle_exam", 7),
    "l10n_sk_accrual_plan_obstacle_accompany_7d": (
        "l10n_sk_leave_type_obstacle_accompany", 7),
    "l10n_sk_accrual_plan_obstacle_accompany_disabled_10d": (
        "l10n_sk_leave_type_obstacle_accompany_disabled", 10),
}


@tagged("post_install", "-at_install")
@freeze_time(date(2026, 3, 1))
class TestSkObstacleQuota(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mgr = cls.env.ref("hr_holidays.group_hr_holidays_manager")
        field = "group_ids" if "group_ids" in cls.env.user._fields else "groups_id"
        cls.env.user[field] |= mgr
        cls.employee = cls.env["hr.employee"].create({"name": "Obstacle Test"})
        cls.generic = cls.env.ref(MOD + ".l10n_sk_leave_type_obstacle")

    def _allocate(self, plan_xmlid):
        """Run the shipped plan for a year and return its allocation."""
        plan = self.env.ref(MOD + "." + plan_xmlid)
        alloc = self.env["hr.leave.allocation"].create(
            {
                "name": plan.name,
                "holiday_status_id": plan.time_off_type_id.id,
                "employee_id": self.employee.id,
                "allocation_type": "accrual",
                "accrual_plan_id": plan.id,
                "date_from": date(2026, 1, 1),
                "number_of_days": 0,
            }
        )
        alloc.action_approve()
        alloc._process_accrual_plans(date(2026, 3, 1))
        return alloc

    def _balance(self, leave_type):
        return leave_type.get_allocation_data(self.employee)[self.employee][0][1][
            "max_leaves"
        ]

    # ------------------------------------------------------------------

    def test_each_capped_reason_has_its_own_type(self):
        """One leave type per capped reason, each requiring an allocation."""
        seen = self.env["hr.leave.type"]
        for plan_xmlid, (type_xmlid, annual) in CAPPED.items():
            plan = self.env.ref(MOD + "." + plan_xmlid)
            leave_type = self.env.ref(MOD + "." + type_xmlid)
            self.assertEqual(plan.time_off_type_id, leave_type)
            self.assertEqual(plan.level_ids.maximum_leave_yearly, annual)
            self.assertTrue(leave_type.requires_allocation)
            self.assertNotIn(
                leave_type, seen, "capped reasons must not share a leave type"
            )
            self.assertNotEqual(leave_type, self.generic)
            seen |= leave_type
        self.assertEqual(len(seen), 3)

    def test_caps_are_not_pooled(self):
        """Two quotas held at once stay two balances, not one 14-day pot."""
        self._allocate("l10n_sk_accrual_plan_obstacle_exam_7d")
        self._allocate("l10n_sk_accrual_plan_obstacle_accompany_7d")
        for _plan, (type_xmlid, annual) in list(CAPPED.items())[:2]:
            leave_type = self.env.ref(MOD + "." + type_xmlid)
            self.assertEqual(self._balance(leave_type), annual)

    def test_cap_is_enforced_at_booking(self):
        """7 days of vyšetrenie go through; the 8th is refused."""
        self._allocate("l10n_sk_accrual_plan_obstacle_exam_7d")
        exam = self.env.ref(MOD + ".l10n_sk_leave_type_obstacle_exam")

        leave = self.env["hr.leave"].create(
            {
                "holiday_status_id": exam.id,
                "employee_id": self.employee.id,
                "request_date_from": QUOTA_FROM,
                "request_date_to": QUOTA_TO,
            }
        )
        self.assertEqual(leave.number_of_days, 7)

        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": exam.id,
                    "employee_id": self.employee.id,
                    "request_date_from": ONE_DAY_TOO_MANY,
                    "request_date_to": ONE_DAY_TOO_MANY,
                }
            )

    def test_generic_obstacle_needs_no_allocation(self):
        """A funeral day must stay bookable with no allocation at all — those
        §141 reasons are per-event, not an annual quota."""
        self.assertFalse(self.generic.requires_allocation)
        leave = self.env["hr.leave"].create(
            {
                "holiday_status_id": self.generic.id,
                "employee_id": self.employee.id,
                "request_date_from": ONE_DAY_TOO_MANY,
                "request_date_to": ONE_DAY_TOO_MANY,
            }
        )
        self.assertEqual(leave.number_of_days, 1)

    def test_all_reasons_carry_the_obstacle_payroll_code(self):
        """The split must be invisible to payroll: every obstacle type feeds
        the same OBSTACLE worked-day line."""
        self.assertEqual(self.generic.l10n_sk_payroll_code, "OBSTACLE")
        for _plan, (type_xmlid, _annual) in CAPPED.items():
            leave_type = self.env.ref(MOD + "." + type_xmlid)
            self.assertEqual(leave_type.l10n_sk_payroll_code, "OBSTACLE")

    def test_quotas_are_use_it_or_lose_it(self):
        """can_be_carryover=False is what keeps the expiry reminder away from
        a statutory quota (see l10n_cssk_leave_expiry_reminder)."""
        for plan_xmlid in CAPPED:
            plan = self.env.ref(MOD + "." + plan_xmlid)
            self.assertFalse(plan.can_be_carryover)
            self.assertEqual(plan.level_ids.action_with_unused_accruals, "lost")
            self.assertFalse(plan.level_ids.accrual_validity)
