# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
#
# Only ONE paid Czech obstacle carries a per-CALENDAR-YEAR budget — the
# 6 pracovních dnů for transporting a disabled child (NV 590/2006) — so it is
# the only one that gets an accrual plan. Every other statutory limit in the CZ
# taxonomy is PER CASE or PER EVENT: 9/16 kalendářních dnů per krátkodobé
# ošetřovné case (§ 39), 90 dnů per dlouhodobé case (§ 41a), doprovod max 1 den
# per trip. A yearly accrual on any of those would cap the SECOND case at zero,
# so they are allocation-per-case and this test pins that they stay plan-less.

from datetime import date

from freezegun import freeze_time

from odoo.exceptions import ValidationError
from odoo.tests import TransactionCase, tagged

MOD = "l10n_cz_hr_payroll_oca"

# 2 Mar 2026 is a Monday; 2–9 March spans exactly 6 working days.
QUOTA_FROM = date(2026, 3, 2)
QUOTA_TO = date(2026, 3, 9)
ONE_DAY_TOO_MANY = date(2026, 3, 10)

# Statutory limits that are NOT annual and must therefore never accrue.
PER_CASE_TYPES = (
    "leave_type_cz_ocr_shortterm",
    "leave_type_cz_ocr_longterm",
    "leave_type_cz_obstacle_doprovod",
)


@tagged("post_install", "-at_install")
@freeze_time(date(2026, 3, 1))
class TestCzObstacleQuota(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        mgr = cls.env.ref("hr_holidays.group_hr_holidays_manager")
        field = "group_ids" if "group_ids" in cls.env.user._fields else "groups_id"
        cls.env.user[field] |= mgr
        cls.employee = cls.env["hr.employee"].create({"name": "CZ Obstacle Test"})
        cls.transport = cls.env.ref(
            MOD + ".leave_type_cz_obstacle_transport_disabled")
        cls.plan = cls.env.ref(
            MOD + ".accrual_plan_cz_obstacle_transport_disabled_6d")
        cls.generic = cls.env.ref(MOD + ".leave_type_cz_obstacle")

    def _allocate(self):
        alloc = self.env["hr.leave.allocation"].create(
            {
                "name": self.plan.name,
                "holiday_status_id": self.transport.id,
                "employee_id": self.employee.id,
                "allocation_type": "accrual",
                "accrual_plan_id": self.plan.id,
                "date_from": date(2026, 1, 1),
                "number_of_days": 0,
            }
        )
        alloc.action_approve()
        alloc._process_accrual_plans(date(2026, 3, 1))
        return alloc

    # ------------------------------------------------------------------

    def test_annual_quota_accrues_six_days(self):
        """The one genuinely annual paid obstacle grants its 6 days up front."""
        self.assertEqual(self.plan.time_off_type_id, self.transport)
        self.assertTrue(self.transport.requires_allocation)
        level = self.plan.level_ids
        self.assertEqual(len(level), 1)
        self.assertEqual(level.added_value_type, "day")
        self.assertEqual(level.frequency, "yearly")
        self.assertEqual(level.maximum_leave_yearly, 6)
        self.assertEqual(self._allocate().number_of_days, 6)

    def test_annual_quota_is_enforced_at_booking(self):
        """6 days go through; the 7th is refused."""
        self._allocate()
        leave = self.env["hr.leave"].create(
            {
                "holiday_status_id": self.transport.id,
                "employee_id": self.employee.id,
                "request_date_from": QUOTA_FROM,
                "request_date_to": QUOTA_TO,
            }
        )
        self.assertEqual(leave.number_of_days, 6)

        with self.assertRaises(ValidationError):
            self.env["hr.leave"].create(
                {
                    "holiday_status_id": self.transport.id,
                    "employee_id": self.employee.id,
                    "request_date_from": ONE_DAY_TOO_MANY,
                    "request_date_to": ONE_DAY_TOO_MANY,
                }
            )

    def test_per_case_limits_never_accrue(self):
        """OČR (9/16 and 90 dnů) and doprovod (1 den) are per CASE / per EVENT.
        An annual accrual would cap a second case in the same year at zero, so
        these must stay plan-less and be allocated per case."""
        Plan = self.env["hr.leave.accrual.plan"]
        for xmlid in PER_CASE_TYPES:
            leave_type = self.env.ref(MOD + "." + xmlid)
            self.assertTrue(
                leave_type.requires_allocation,
                "a per-case cap is expressed as one allocation per case",
            )
            self.assertFalse(
                Plan.search([("time_off_type_id", "=", leave_type.id)]),
                f"{xmlid} must not carry an accrual plan — its limit is not annual",
            )

    def test_generic_obstacle_needs_no_allocation(self):
        """The 'nezbytně nutná doba' reasons carry no number at all, so the
        generic type must stay bookable with no allocation."""
        self.assertFalse(self.generic.requires_allocation)

    def test_all_reasons_carry_the_obstacle_payroll_code(self):
        """The split stays invisible to payroll."""
        self.assertEqual(self.transport.l10n_cz_payroll_code, "CZOBSTACLE")
        self.assertEqual(
            self.env.ref(MOD + ".leave_type_cz_obstacle_doprovod")
            .l10n_cz_payroll_code,
            "CZOBSTACLE",
        )

    def test_quota_is_use_it_or_lose_it(self):
        """can_be_carryover=False keeps the expiry reminder away from it
        (see l10n_cssk_leave_expiry_reminder)."""
        self.assertFalse(self.plan.can_be_carryover)
        self.assertEqual(self.plan.level_ids.action_with_unused_accruals, "lost")
        self.assertFalse(self.plan.level_ids.accrual_validity)
