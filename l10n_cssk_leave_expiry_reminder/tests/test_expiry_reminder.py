# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from datetime import date

from freezegun import freeze_time

from odoo.tests import TransactionCase, tagged

MOD = "l10n_cssk_leave_expiry_reminder"
# Fixed "today" for the whole suite; the lead window default is 60 days.
TODAY = date(2026, 11, 1)
IN_WINDOW = date(2026, 12, 20)  # 49 days out -> inside the 60-day window
OUT_WINDOW = date(2027, 3, 1)  # ~120 days out -> outside the window


@tagged("post_install", "-at_install")
@freeze_time(TODAY)
class TestLeaveExpiryReminder(TransactionCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.act_type = cls.env.ref(MOD + ".mail_activity_type_expiring_leave")
        cls.Activity = cls.env["mail.activity"]
        cls.user = cls.env["res.users"].create(
            {
                "name": "Expiry Employee",
                "login": "expiry_employee",
                "email": "expiry.employee@example.com",
            }
        )
        cls.employee = cls.env["hr.employee"].create(
            {
                "name": "Expiry Employee",
                "user_id": cls.user.id,
                "work_email": "expiry.employee@example.com",
            }
        )
        cls.leave_type = cls.env["hr.leave.type"].create(
            {
                "name": "Test Annual Leave",
                "requires_allocation": "yes",
                "request_unit": "day",
                # Leaves land straight in 'validate', which is what
                # ``leaves_taken`` counts.
                "leave_validation_type": "no_validation",
            }
        )

    def _make_allocation(self, expiry_date, expiring_days):
        alloc = self.env["hr.leave.allocation"].create(
            {
                "name": "Test allocation",
                "holiday_status_id": self.leave_type.id,
                "employee_id": self.employee.id,
                "number_of_days": 20,
                # Early enough to cover the leaves the netting tests book.
                "date_from": date(2026, 1, 1),
            }
        )
        # These fields are populated imperatively by the accrual cron in real
        # use; set them directly to simulate carried-over days.
        alloc.write(
            {
                "carried_over_days_expiration_date": expiry_date,
                "expiring_carryover_days": expiring_days,
            }
        )
        return alloc

    def _activities_for(self, employee):
        return self.Activity.search(
            [
                ("res_model", "=", "hr.employee"),
                ("res_id", "=", employee.id),
                ("activity_type_id", "=", self.act_type.id),
            ]
        )

    def test_reminder_created_once_and_deduped(self):
        alloc = self._make_allocation(IN_WINDOW, 5.0)

        self.env["hr.leave.allocation"]._cron_notify_expiring_carryover()

        acts = self._activities_for(self.employee)
        self.assertEqual(len(acts), 1, "exactly one reminder activity expected")
        self.assertEqual(acts.date_deadline, IN_WINDOW)
        self.assertEqual(acts.user_id, self.user)
        self.assertEqual(alloc.l10n_cssk_expiry_reminder_date, IN_WINDOW)

        # Running again must NOT create a duplicate.
        self.env["hr.leave.allocation"]._cron_notify_expiring_carryover()
        self.assertEqual(
            len(self._activities_for(self.employee)),
            1,
            "cron must be idempotent for the same cohort",
        )

    def test_outside_window_gets_no_reminder(self):
        alloc = self._make_allocation(OUT_WINDOW, 5.0)
        self.env["hr.leave.allocation"]._cron_notify_expiring_carryover()
        self.assertFalse(self._activities_for(self.employee))
        self.assertFalse(alloc.l10n_cssk_expiry_reminder_date)

    def test_zero_expiring_days_gets_no_reminder(self):
        alloc = self._make_allocation(IN_WINDOW, 0.0)
        self.env["hr.leave.allocation"]._cron_notify_expiring_carryover()
        self.assertFalse(self._activities_for(self.employee))
        self.assertFalse(alloc.l10n_cssk_expiry_reminder_date)

    def _make_accrual_plan(self, name, lost, **level_kw):
        plan = self.env["hr.leave.accrual.plan"].create({
            "name": name,
            "time_off_type_id": self.leave_type.id,
            "accrued_gain_time": "start",
            "carryover_date": "year_start",
        })
        self.env["hr.leave.accrual.level"].create(dict({
            "accrual_plan_id": plan.id,
            "added_value": 7,
            "added_value_type": "day",
            "frequency": "yearly",
            "cap_accrued_time": False,
            "maximum_leave": 7,
            "action_with_unused_accruals": "lost" if lost else "all",
        }, **level_kw))
        return plan

    def _take_leave(self, date_from, date_to):
        return self.env["hr.leave"].create({
            "holiday_status_id": self.leave_type.id,
            "employee_id": self.employee.id,
            "request_date_from": date_from,
            "request_date_to": date_to,
        })

    def test_amount_is_net_of_days_already_taken(self):
        """``expiring_carryover_days`` is the GROSS balance captured on the
        carryover date; days taken since must not be reminded about."""
        alloc = self._make_allocation(IN_WINDOW, 5.0)
        alloc.action_approve()
        self._take_leave(date(2026, 10, 5), date(2026, 10, 6))
        self.assertEqual(alloc._l10n_cssk_net_expiring_days(), 3.0)

        self.env["hr.leave.allocation"]._cron_notify_expiring_carryover()
        acts = self._activities_for(self.employee)
        self.assertEqual(len(acts), 1)
        self.assertIn("3 day(s)", acts.note)

    def test_statutory_quota_plan_is_never_reminded(self):
        """A §141 doctor-visit quota is granted whole and lapses; nothing is
        carried over, so it must stay out of scope."""
        quota = self._make_accrual_plan("Obstacle 7 days/year", lost=True)
        alloc = self._make_allocation(IN_WINDOW, 5.0)
        alloc.write({"allocation_type": "accrual", "accrual_plan_id": quota.id})
        self.env["hr.leave.allocation"]._cron_notify_expiring_carryover()
        self.assertFalse(self._activities_for(self.employee))

    def test_carryover_capable_plan_is_still_reminded(self):
        holiday = self._make_accrual_plan("Dovolenka", lost=False)
        alloc = self._make_allocation(IN_WINDOW, 5.0)
        alloc.write({"allocation_type": "accrual", "accrual_plan_id": holiday.id})
        self.env["hr.leave.allocation"]._cron_notify_expiring_carryover()
        self.assertEqual(len(self._activities_for(self.employee)), 1)
