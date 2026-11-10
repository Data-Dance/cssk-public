# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
import logging

import pytz

from odoo import models, fields, _
from odoo.exceptions import UserError, ValidationError

_logger = logging.getLogger(__name__)


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _kiosk_create_departure_leave(self, leave_type, attendance):
        """Create a draft (state=confirm) time off for HR to finalize when an
        employee selects a reason while checking out at the kiosk.

        The leave spans from the check-out time to the end of the employee's
        working day. It is left in ``confirm`` state so that:
          * no ``resource.calendar.leaves`` entry is created yet (no conflict
            with the attendance that was just recorded), and
          * the regular approval activity is sent to the Time Off approvers.

        Any validation error (e.g. a type that requires an allocation the
        employee does not have) is swallowed so it never blocks the check-out.
        Returns the created ``hr.leave`` record, or an empty recordset.
        """
        self.ensure_one()
        if not attendance.check_out:
            return self.env['hr.leave']

        tz = pytz.timezone(self._get_tz() or 'UTC')
        local_out = pytz.utc.localize(attendance.check_out).astimezone(tz)
        vals = {
            'employee_id': self.id,
            'holiday_status_id': leave_type.id,
            'request_date_from': local_out.date(),
            'request_date_to': local_out.date(),
            'name': _("Kiosk check-out — %(reason)s", reason=leave_type.name),
        }
        if leave_type.request_unit == 'hour':
            out_float = local_out.hour + local_out.minute / 60.0
            day_end = self._kiosk_day_end_float(local_out)
            # "Rest of the working day". When the check-out happens at/after the
            # scheduled day end (or no schedule is known), fall back to a 1h
            # block so the draft is never zero-length; HR adjusts on approval.
            if not day_end or day_end <= out_float:
                end_float = min(out_float + 1.0, 24.0)
            else:
                end_float = day_end
            vals.update({
                'request_unit_hours': True,
                'request_hour_from': out_float,
                'request_hour_to': end_float,
            })

        try:
            return self.env['hr.leave'].sudo().with_context(
                leave_skip_date_check=True,
            ).create(vals)
        except (ValidationError, UserError) as err:
            _logger.warning(
                "Kiosk departure leave skipped for %s (%s): %s",
                self.name, leave_type.name, err,
            )
            return self.env['hr.leave']

    def _kiosk_close_departure_leave(self, check_in_dt):
        """Shorten the still-draft kiosk departure leave when the employee
        returns the same day.

        Called on a kiosk check-in: the most recent kiosk-created departure
        leave (linked from the previous attendance) is trimmed so its end
        matches this check-in time, i.e. the leave covers only the real time
        away instead of the whole rest of the working day. Only ``confirm``
        (draft) leaves are touched; an already-approved leave is left as-is.
        Returns the trimmed leave, or an empty recordset when nothing applies.
        """
        self.ensure_one()
        check_in_dt = fields.Datetime.to_datetime(check_in_dt)
        if not check_in_dt:
            return self.env['hr.leave']

        last_tagged = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', self.id),
            ('checkout_leave_id', '!=', False),
            ('check_out', '!=', False),
        ], order='check_out desc', limit=1)
        leave = last_tagged.checkout_leave_id
        if not leave or leave.state != 'confirm' or not leave.request_unit_hours:
            return self.env['hr.leave']

        tz = pytz.timezone(self._get_tz() or 'UTC')
        local_in = pytz.utc.localize(check_in_dt).astimezone(tz)
        if local_in.date() != leave.request_date_from:
            # Returned on a different day: leave the draft untouched.
            return self.env['hr.leave']

        in_float = local_in.hour + local_in.minute / 60.0
        if leave.request_hour_from < in_float < leave.request_hour_to:
            leave.with_context(
                leave_skip_date_check=True,
                leave_skip_state_check=True,
            ).write({'request_hour_to': in_float})
        return leave

    def _kiosk_tag_auto_checkout(self, leave_type):
        """Attach a departure reason to the most recent attendance that the
        *Automatic Check Out* cron closed and that is not yet tagged.

        Used when an employee returns to the kiosk after a forgotten check-out:
        the prior auto-closed segment is tagged and gets the usual draft leave.
        Only the attendance immediately before the current one qualifies, the
        one the kiosk asked about: an older automatic check-out followed by an
        ordinary one is never reached by a reason sent with a later check-in.
        Its duration is approximate (based on the auto check-out time, which is
        not the real departure time), so it is meant to be finalized by HR.
        Returns the tagged attendance, or an empty recordset.
        """
        self.ensure_one()
        attendance = self.env['hr.attendance'].sudo().search([
            ('employee_id', '=', self.id),
            ('check_out', '!=', False),
        ], order='check_out desc', limit=1)
        if (not attendance or attendance.out_mode != 'auto_check_out'
                or attendance.checkout_reason_id):
            return self.env['hr.attendance']
        attendance.checkout_reason_id = leave_type.id
        attendance.checkout_leave_id = self._kiosk_create_departure_leave(leave_type, attendance)
        return attendance

    def _kiosk_day_end_float(self, local_dt):
        """Return the last working hour (float) of the employee's calendar for
        the weekday of ``local_dt``, or False when it cannot be determined."""
        self.ensure_one()
        calendar = self.resource_calendar_id
        if not calendar:
            return False
        weekday = str(local_dt.weekday())
        hours = calendar.attendance_ids.filtered(
            lambda a: a.dayofweek == weekday and a.day_period != 'lunch'
        ).mapped('hour_to')
        return max(hours) if hours else False
