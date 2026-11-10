# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import http
from odoo.http import request

from odoo.addons.hr_attendance.controllers.main import HrAttendance


class HrAttendanceHolidaysKiosk(HrAttendance):
    """Adds an identify-then-confirm flow so the kiosk can ask for a reason
    for leaving before recording a check-out."""

    @http.route()
    def open_kiosk_mode(self, token, from_trial_mode=False):
        # The "Try Kiosk" button links to ``...?from_trial_mode=True``, so the
        # value reaches the controller as the string "True". The OWL prop
        # ``fromTrialMode`` is a Boolean and is validated in dev/debug mode,
        # which would otherwise prevent the kiosk from mounting. Coerce it.
        if isinstance(from_trial_mode, str):
            from_trial_mode = from_trial_mode.strip().lower() in ('1', 'true', 'yes', 't')
        return super().open_kiosk_mode(token, from_trial_mode=from_trial_mode)

    @staticmethod
    def _kiosk_resolve_employee(company, employee_id=False, barcode=False, pin_code=False):
        """Resolve a kiosk employee and validate identity.

        Returns a ``(employee, pin_ok)`` tuple. ``employee`` is an empty
        recordset when no matching employee exists for the company. A badge
        scan authenticates by itself; the PIN is only enforced for manual
        selection (``employee_id``) when the company requires it.
        """
        Employee = request.env['hr.employee'].sudo()
        if employee_id:
            employee = Employee.browse(int(employee_id)).exists()
        elif barcode:
            employee = Employee.search(
                [('barcode', '=', barcode), ('company_id', '=', company.id)], limit=1)
        else:
            employee = Employee
        if not employee or employee.company_id != company:
            return Employee, False
        pin_ok = True
        if employee_id and company.attendance_kiosk_use_pin:
            pin_ok = employee.pin == pin_code
        return employee, pin_ok

    @staticmethod
    def _kiosk_leave_reasons(company):
        leave_types = request.env['hr.leave.type'].sudo().search(
            ['&', ('kiosk_visible', '=', True),
             '|', ('company_id', '=', company.id), ('company_id', '=', False)],
            order='kiosk_sequence, name',
        )
        return [{'id': lt.id, 'name': lt.name, 'color': lt.color} for lt in leave_types]

    @http.route('/hr_attendance/kiosk_identify', type="jsonrpc", auth="public")
    def kiosk_identify(self, token, employee_id=False, barcode=False, pin_code=False):
        """Identify an employee WITHOUT recording any check-in/out.

        Returns the employee info plus ``will_check_out`` and the list of
        kiosk ``reasons`` (only when the next action is a check-out)."""
        company = self._get_company(token)
        if not company:
            return {}
        employee, pin_ok = self._kiosk_resolve_employee(company, employee_id, barcode, pin_code)
        # A wrong PIN answers exactly like an unknown employee, so this
        # side-effect-free route does not tell a token holder which employee
        # ids exist. The kiosk shows "Wrong Pin" for both.
        if not employee or not pin_ok:
            return {}
        info = self._get_employee_info_response(employee)
        info['valid'] = True
        will_check_out = employee.attendance_state == 'checked_in'
        info['will_check_out'] = will_check_out

        # The employee is about to check out -> offer the reason screen.
        # Or they are returning and their previous segment was closed by the
        # "Automatic Check Out" cron without a reason -> offer to log it now.
        last_att = employee.last_attendance_id
        auto_pending = bool(
            not will_check_out and last_att and last_att.check_out
            and last_att.out_mode == 'auto_check_out'
            and not last_att.checkout_reason_id
        )
        info['auto_checkout_pending'] = auto_pending
        if auto_pending:
            info['auto_checkout_datetime'] = last_att.check_out
        info['reasons'] = self._kiosk_leave_reasons(company) if (will_check_out or auto_pending) else []
        return info

    @http.route('/hr_attendance/kiosk_action', type="jsonrpc", auth="public")
    def kiosk_action(self, token, employee_id=False, barcode=False, pin_code=False,
                     reason_id=False, latitude=False, longitude=False):
        """Record the check-in/out. On a check-out with a selected reason, tag
        the attendance and create a draft time off for HR."""
        company = self._get_company(token)
        if not company:
            return {}
        employee, pin_ok = self._kiosk_resolve_employee(company, employee_id, barcode, pin_code)
        if not employee or not pin_ok:
            return {}
        geo = self._get_geoip_response(
            'kiosk', latitude=latitude, longitude=longitude,
            device_tracking_enabled=company.attendance_device_tracking)
        attendance = employee._attendance_action_change(geo)
        if attendance.check_out:
            # Check-OUT: tag the attendance and create the draft departure leave.
            if reason_id:
                reason = request.env['hr.leave.type'].sudo().browse(int(reason_id)).exists()
                if reason and reason.kiosk_visible and (not reason.company_id or reason.company_id == company):
                    attendance.checkout_reason_id = reason.id
                    attendance.checkout_leave_id = employee._kiosk_create_departure_leave(reason, attendance)
        else:
            # Check-IN: if the employee is returning the same day, shorten the
            # still-draft departure leave to the actual time away.
            employee._kiosk_close_departure_leave(attendance.check_in)
            # A reason on a check-in means the employee is logging the reason for
            # a previous departure that the Automatic Check Out cron closed.
            if reason_id:
                reason = request.env['hr.leave.type'].sudo().browse(int(reason_id)).exists()
                if reason and reason.kiosk_visible and (not reason.company_id or reason.company_id == company):
                    employee._kiosk_tag_auto_checkout(reason)
        return self._get_employee_info_response(employee)
