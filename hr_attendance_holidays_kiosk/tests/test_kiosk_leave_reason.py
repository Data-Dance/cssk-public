# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import json

from odoo import fields
from odoo.tests import TransactionCase, HttpCase, tagged


class KioskReasonCommon(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.env.company
        cls.company.write({
            'attendance_kiosk_key': 'kiosk-test-token',
            'attendance_kiosk_use_pin': False,
        })
        cls.admin = cls.env.ref('base.user_admin')
        cls.employee = cls.env['hr.employee'].create({
            'name': "Kiosk Tester",
            'company_id': cls.company.id,
            'barcode': 'KIOSKEE1',
        })
        cls.reason = cls.env['hr.leave.type'].create({
            'name': "Doctor (Test)",
            'kiosk_visible': True,
            'kiosk_sequence': 5,
            'requires_allocation': False,
            'request_unit': 'hour',
            'leave_validation_type': 'hr',
            'responsible_ids': [(6, 0, cls.admin.ids)],
        })
        cls.hidden_type = cls.env['hr.leave.type'].create({
            'name': "Not In Kiosk (Test)",
            'kiosk_visible': False,
            'requires_allocation': False,
            'request_unit': 'hour',
            'leave_validation_type': 'hr',
        })


class TestKioskLeaveReasonModel(KioskReasonCommon):

    def test_departure_leave_is_draft_for_hr(self):
        """A kiosk reason creates a confirm-state leave of the chosen type."""
        self.employee._attendance_action_change()           # check in
        attendance = self.employee._attendance_action_change()  # check out
        self.assertTrue(attendance.check_out)

        leave = self.employee._kiosk_create_departure_leave(self.reason, attendance)
        self.assertTrue(leave, "A draft leave should have been created")
        self.assertEqual(leave.holiday_status_id, self.reason)
        self.assertEqual(leave.employee_id, self.employee)
        self.assertEqual(leave.state, 'confirm',
                         "Leave must stay 'To Approve' so HR finalizes it")

    def test_departure_leave_window_is_positive(self):
        """The generated hour-based leave must never be zero-length, even when
        the check-out happens outside the scheduled working day."""
        # Mid-morning check-out: the "rest of working day" is a real window.
        day = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 06:00:00',
            'check_out': '2026-05-20 08:00:00',
        })
        leave = self.employee._kiosk_create_departure_leave(self.reason, day)
        self.assertTrue(leave)
        self.assertGreater(leave.request_hour_to, leave.request_hour_from,
                           "Daytime check-out should span until the day end")

        # Late-evening check-out: falls back to a 1h block, still positive.
        night = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 19:00:00',
            'check_out': '2026-05-20 20:35:00',
        })
        leave_night = self.employee._kiosk_create_departure_leave(self.reason, night)
        self.assertTrue(leave_night)
        self.assertGreater(leave_night.request_hour_to, leave_night.request_hour_from,
                           "After-hours check-out must not create a zero-length leave")

    def test_same_day_return_trims_draft_leave(self):
        """Returning the same day shortens the still-draft leave to the gap."""
        out = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 04:00:00',
            'check_out': '2026-05-20 06:00:00',
        })
        leave = self.employee._kiosk_create_departure_leave(self.reason, out)
        out.checkout_leave_id = leave.id
        self.assertEqual(leave.state, 'confirm')
        end_before = leave.request_hour_to
        self.assertGreater(end_before, leave.request_hour_from)

        # The employee returns ~30 minutes later, same day.
        self.employee._kiosk_close_departure_leave(
            fields.Datetime.to_datetime('2026-05-20 06:30:00'))
        self.assertLess(leave.request_hour_to, end_before,
                        "Draft leave end should be trimmed to the return time")
        self.assertGreater(leave.request_hour_to, leave.request_hour_from)
        self.assertEqual(leave.state, 'confirm', "Trim must keep it a draft")

    def test_return_does_not_touch_approved_leave(self):
        """An already-approved leave is not modified on same-day return."""
        out = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 04:00:00',
            'check_out': '2026-05-20 06:00:00',
        })
        leave = self.employee._kiosk_create_departure_leave(self.reason, out)
        out.checkout_leave_id = leave.id
        leave.action_approve()
        end_after_approve = leave.request_hour_to
        self.employee._kiosk_close_departure_leave(
            fields.Datetime.to_datetime('2026-05-20 06:30:00'))
        self.assertEqual(leave.request_hour_to, end_after_approve,
                         "Approved leave must be left untouched")

    def test_tag_auto_checkout_reason_on_prior_attendance(self):
        """Logging a reason after an automatic check-out tags that segment."""
        auto = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 04:00:00',
            'check_out': '2026-05-20 06:00:00',
            'out_mode': 'auto_check_out',
        })
        tagged = self.employee._kiosk_tag_auto_checkout(self.reason)
        self.assertEqual(tagged, auto)
        self.assertEqual(auto.checkout_reason_id, self.reason)
        self.assertTrue(auto.checkout_leave_id)
        self.assertEqual(auto.checkout_leave_id.state, 'confirm')

    def test_tag_auto_checkout_ignores_already_tagged(self):
        """An auto-checked-out segment already tagged is not re-tagged."""
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 04:00:00',
            'check_out': '2026-05-20 06:00:00',
            'out_mode': 'auto_check_out',
            'checkout_reason_id': self.reason.id,
        })
        self.assertFalse(self.employee._kiosk_tag_auto_checkout(self.hidden_type))

    def test_tag_auto_checkout_only_reaches_the_previous_attendance(self):
        """An older automatic check-out followed by an ordinary one is not
        tagged by a reason sent later."""
        older = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-19 04:00:00',
            'check_out': '2026-05-19 06:00:00',
            'out_mode': 'auto_check_out',
        })
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 04:00:00',
            'check_out': '2026-05-20 06:00:00',
        })
        self.assertFalse(self.employee._kiosk_tag_auto_checkout(self.reason))
        self.assertFalse(older.checkout_reason_id)

    def test_allocation_required_leave_is_skipped_not_raised(self):
        """A reason needing an allocation the employee lacks must not raise;
        it returns an empty recordset so the check-out is never blocked."""
        needs_alloc = self.env['hr.leave.type'].create({
            'name': "Needs Allocation (Test)",
            'kiosk_visible': True,
            'requires_allocation': True,
            'request_unit': 'hour',
            'leave_validation_type': 'hr',
        })
        self.employee._attendance_action_change()
        attendance = self.employee._attendance_action_change()
        leave = self.employee._kiosk_create_departure_leave(needs_alloc, attendance)
        self.assertFalse(leave, "Leave creation should be silently skipped")


@tagged('post_install', '-at_install')
class TestKioskLeaveReasonHttp(KioskReasonCommon, HttpCase):

    def _call(self, route, params):
        response = self.url_open(
            route,
            data=json.dumps({'jsonrpc': '2.0', 'method': 'call', 'params': params}),
            headers={'Content-Type': 'application/json'},
        )
        response.raise_for_status()
        return response.json().get('result')

    def test_full_checkout_with_reason_flow(self):
        token = self.company.attendance_kiosk_key

        # 1. Badge scan checks the employee IN (no reason screen on check-in).
        res = self._call('/hr_attendance/kiosk_action', {'token': token, 'barcode': 'KIOSKEE1'})
        self.assertEqual(res.get('employee_name'), "Kiosk Tester")
        self.env.invalidate_all()
        self.assertEqual(self.employee.attendance_state, 'checked_in')

        # 2. Identify (no action) -> will check out, kiosk reason offered.
        info = self._call('/hr_attendance/kiosk_identify', {'token': token, 'barcode': 'KIOSKEE1'})
        self.assertTrue(info.get('valid'))
        self.assertTrue(info.get('will_check_out'))
        reason_ids = [r['id'] for r in info.get('reasons', [])]
        self.assertIn(self.reason.id, reason_ids)
        self.assertNotIn(self.hidden_type.id, reason_ids,
                         "Non-kiosk types must not be offered")

        # 3. Action with the reason -> check out + tag + draft leave.
        res = self._call('/hr_attendance/kiosk_action',
                         {'token': token, 'barcode': 'KIOSKEE1', 'reason_id': self.reason.id})
        self.assertEqual(res.get('employee_name'), "Kiosk Tester")
        self.env.invalidate_all()
        self.assertEqual(self.employee.attendance_state, 'checked_out')

        attendance = self.employee.last_attendance_id
        self.assertEqual(attendance.checkout_reason_id, self.reason)
        self.assertTrue(attendance.checkout_leave_id)
        self.assertEqual(attendance.checkout_leave_id.holiday_status_id, self.reason)
        self.assertEqual(attendance.checkout_leave_id.state, 'confirm')

    def test_checkin_offers_no_reason(self):
        token = self.company.attendance_kiosk_key
        # Employee is checked out -> identify should not offer reasons.
        info = self._call('/hr_attendance/kiosk_identify', {'token': token, 'barcode': 'KIOSKEE1'})
        self.assertTrue(info.get('valid'))
        self.assertFalse(info.get('will_check_out'))
        self.assertFalse(info.get('auto_checkout_pending'))
        self.assertEqual(info.get('reasons'), [])

    def test_wrong_pin_answers_like_unknown_employee(self):
        token = self.company.attendance_kiosk_key
        self.company.attendance_kiosk_use_pin = True
        self.employee.pin = '1234'
        wrong = self._call('/hr_attendance/kiosk_identify',
                           {'token': token, 'employee_id': self.employee.id, 'pin_code': '0000'})
        unknown = self._call('/hr_attendance/kiosk_identify',
                             {'token': token, 'employee_id': 999999, 'pin_code': '0000'})
        self.assertEqual(wrong, {})
        self.assertEqual(wrong, unknown)
        right = self._call('/hr_attendance/kiosk_identify',
                           {'token': token, 'employee_id': self.employee.id, 'pin_code': '1234'})
        self.assertTrue(right.get('valid'))

    def test_identify_flags_pending_auto_checkout(self):
        token = self.company.attendance_kiosk_key
        self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 04:00:00',
            'check_out': '2026-05-20 06:00:00',
            'out_mode': 'auto_check_out',
        })
        self.env.invalidate_all()
        info = self._call('/hr_attendance/kiosk_identify', {'token': token, 'barcode': 'KIOSKEE1'})
        self.assertFalse(info.get('will_check_out'))
        self.assertTrue(info.get('auto_checkout_pending'), "Auto check-out should be flagged")
        self.assertIn(self.reason.id, [r['id'] for r in info.get('reasons', [])])

    def test_logging_reason_on_return_after_auto_checkout(self):
        token = self.company.attendance_kiosk_key
        auto = self.env['hr.attendance'].create({
            'employee_id': self.employee.id,
            'check_in': '2026-05-20 04:00:00',
            'check_out': '2026-05-20 06:00:00',
            'out_mode': 'auto_check_out',
        })
        # Return scan + a reason -> the prior auto-closed segment is tagged,
        # and the employee is checked in again.
        res = self._call('/hr_attendance/kiosk_action',
                         {'token': token, 'barcode': 'KIOSKEE1', 'reason_id': self.reason.id})
        self.assertEqual(res.get('employee_name'), "Kiosk Tester")
        self.env.invalidate_all()
        self.assertEqual(self.employee.attendance_state, 'checked_in')
        self.assertEqual(auto.checkout_reason_id, self.reason)
        self.assertTrue(auto.checkout_leave_id)
        self.assertEqual(auto.checkout_leave_id.state, 'confirm')
