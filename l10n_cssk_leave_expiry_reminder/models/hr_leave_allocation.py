# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging
from datetime import timedelta

from odoo import _, api, fields, models
from odoo.tools import format_date

_logger = logging.getLogger(__name__)

# ir.config_parameter keys
PARAM_LEAD_DAYS = "l10n_cssk_leave_expiry.lead_days"
PARAM_SEND_EMAIL = "l10n_cssk_leave_expiry.send_email"

DEFAULT_LEAD_DAYS = 60


def _as_bool(value):
    """Interpret an ir.config_parameter string as a boolean."""
    return str(value).strip().lower() not in ("", "0", "false", "no", "off")


class HrLeaveAllocation(models.Model):
    _inherit = "hr.leave.allocation"

    l10n_cssk_expiry_reminder_date = fields.Date(
        string="Leave Expiry Reminded For",
        copy=False,
        help="The carried-over-days expiration date we last sent an expiry "
        "reminder about. Used to avoid reminding twice for the same cohort.",
    )

    # ------------------------------------------------------------------
    # Cron
    # ------------------------------------------------------------------
    @api.model
    def _cron_notify_expiring_carryover(self):
        """Proactively remind about carried-over leave that is about to expire.

        Scheduled daily. For every allocation whose carried-over days expire
        within the configured lead window and that has not been reminded about
        yet, schedule a reminder activity on the employee (and optionally send
        an email), then record the cohort's expiration date so we do not remind
        again for the same cohort.
        """
        icp = self.env["ir.config_parameter"].sudo()
        try:
            lead_days = int(icp.get_param(PARAM_LEAD_DAYS, DEFAULT_LEAD_DAYS))
        except (TypeError, ValueError):
            lead_days = DEFAULT_LEAD_DAYS
        send_email = _as_bool(icp.get_param(PARAM_SEND_EMAIL, "True"))

        today = fields.Date.today()
        limit = today + timedelta(days=lead_days)

        allocations = self.search(
            [
                # 'validate1' is an allocation waiting for its second
                # approval: its days are as real as a first-level one's.
                ("state", "in", ("validate", "validate1", "confirm")),
                ("carried_over_days_expiration_date", "!=", False),
                ("carried_over_days_expiration_date", ">=", today),
                ("carried_over_days_expiration_date", "<=", limit),
                ("expiring_carryover_days", ">", 0),
                # A use-it-or-lose-it statutory quota (SK §141 doctor visits /
                # accompanying a family member, OČR) is granted whole on 1
                # January and simply lapses — nothing is ever *carried over*,
                # and telling somebody to go book seven doctor visits before
                # December is nonsense. can_be_carryover=False is exactly that
                # switch: core forces action_with_unused_accruals='lost' from
                # it. Plan-less (regular) allocations stay in scope; they never
                # carry an expiration date anyway.
                "|",
                ("accrual_plan_id", "=", False),
                ("accrual_plan_id.can_be_carryover", "=", True),
            ]
        )

        activity_type = self.env.ref(
            "l10n_cssk_leave_expiry_reminder.mail_activity_type_expiring_leave",
            raise_if_not_found=False,
        )
        mail_template = self.env.ref(
            "l10n_cssk_leave_expiry_reminder.mail_template_leave_expiry",
            raise_if_not_found=False,
        )

        for allocation in allocations:
            expiry = allocation.carried_over_days_expiration_date
            # Already reminded for this exact expiration cohort.
            if allocation.l10n_cssk_expiry_reminder_date == expiry:
                continue
            # ``expiring_carryover_days`` is the GROSS figure captured on the
            # carryover date; core only nets it against days since taken once
            # the expiration date itself is reached. Net it here so we never
            # remind about days the employee has already used up.
            if allocation._l10n_cssk_net_expiring_days() <= 0:
                continue
            try:
                delivered = allocation._l10n_cssk_notify_expiry(
                    activity_type, mail_template if send_email else False
                )
            except Exception:  # never let one allocation break the cron
                _logger.exception(
                    "Leave expiry reminder failed for allocation %s",
                    allocation.id,
                )
                continue
            if not delivered:
                # Nobody to tell (no user anywhere, no work email): leave it
                # unmarked so the next run tries again once someone is set.
                _logger.info(
                    "Leave expiry reminder for allocation %s reached nobody; "
                    "it will be retried.", allocation.id)
                continue
            # Mark this cohort as reminded (dedupe).
            allocation.l10n_cssk_expiry_reminder_date = expiry

        return True

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------
    def _l10n_cssk_expiry_responsible_user(self):
        """The employee's own user (may be empty)."""
        self.ensure_one()
        return self.employee_id.user_id

    def _l10n_cssk_expiry_hr_user(self):
        """Who on the HR side is told: the time-off approver, else the
        manager's user — never the employee themselves. May be empty."""
        self.ensure_one()
        employee = self.employee_id
        user = employee.leave_manager_id or employee.parent_id.user_id
        return user if user != employee.user_id else user.browse()

    def _l10n_cssk_hours_per_day(self):
        """Hours in a working day for this allocation's employee.

        Same source ``_process_accrual_plans`` uses when converting between
        hour- and day-denominated figures, with a defensive fallback chain.
        """
        self.ensure_one()
        reference_date = self.nextcall or self.date_from or fields.Date.today()
        return (
            self.employee_id._get_hours_per_day(reference_date)
            or self.employee_id.resource_calendar_id.hours_per_day
            or self.env.company.resource_calendar_id.hours_per_day
            or 8.0
        )

    def _l10n_cssk_net_expiring_days(self):
        """Carried-over days that will actually be forfeited, in days.

        ``expiring_carryover_days`` holds the whole balance captured on the
        carryover date; core only reduces it by the days since taken once the
        expiration date itself is reached (``_process_accrual_plans`` in
        ``hr_holidays``). Until then the raw field overstates what is at risk,
        so net it here the same way core does when it decides the forfeit.

        ``leaves_taken`` is denominated in HOURS for an hour-unit leave type
        while ``expiring_carryover_days`` is always in days, so convert first.
        """
        self.ensure_one()
        leaves_taken = self.leaves_taken
        if self.holiday_status_id.request_unit not in ("day", "half_day"):
            leaves_taken /= self._l10n_cssk_hours_per_day()
        return max(0.0, self.expiring_carryover_days - leaves_taken)

    def _l10n_cssk_expiry_amount_and_unit(self):
        """Return (formatted_amount, unit_word) honouring the leave type's
        request unit (day vs hour). The net expiring amount is in days."""
        self.ensure_one()
        days = self._l10n_cssk_net_expiring_days()
        if self.holiday_status_id.request_unit == "hour":
            amount = days * self._l10n_cssk_hours_per_day()
            unit_word = _("hour(s)")
        else:
            amount = days
            unit_word = _("day(s)")
        # round() keeps the hour conversion from leaking float noise into the
        # message ("2.99999999 hour(s)").
        return ("%g" % round(amount, 2)), unit_word

    def _l10n_cssk_notify_expiry(self, activity_type, mail_template):
        """Schedule the reminder activities and (optionally) send the email
        for a single allocation. Each channel is guarded independently so a
        missing user or email simply skips that channel. Returns whether
        anything reached anybody."""
        self.ensure_one()
        employee = self.employee_id
        if not employee:
            return
        expiry = self.carried_over_days_expiration_date
        amount, unit_word = self._l10n_cssk_expiry_amount_and_unit()
        leave_name = self.holiday_status_id.display_name or _("leave")
        expiry_str = format_date(self.env, expiry)

        delivered = False
        summary = _(
            "Expiring leave: %(amount)s %(unit)s",
            amount=amount,
            unit=unit_word,
        )

        # --- Channel 1: activity for the employee ----------------------
        responsible = self._l10n_cssk_expiry_responsible_user()
        if activity_type and responsible:
            note = _(
                "You have %(amount)s %(unit)s of %(leave)s that will expire "
                "on %(date)s. Please agree with your manager when you will "
                "take this time off before then. Annual leave does not lapse "
                "under the Labour Code; this is the date the time-off plan "
                "removes it from your balance in Odoo.",
                amount=amount,
                unit=unit_word,
                leave=leave_name,
                date=expiry_str,
            )
            employee.activity_schedule(
                activity_type_id=activity_type.id,
                date_deadline=expiry,
                summary=summary,
                note=note,
                user_id=responsible.id,
            )
            delivered = True

        # --- Channel 2: activity for HR (approver / manager) -----------
        # Always, not only when the employee has no user: the employer
        # schedules leave, so HR has to know what is about to fall off the
        # balance even when the employee was told too.
        hr_user = self._l10n_cssk_expiry_hr_user()
        if activity_type and hr_user:
            hr_note = _(
                "%(employee)s has %(amount)s %(unit)s of %(leave)s that will "
                "expire on %(date)s. Please agree with them when they will "
                "take this time off before then. Annual leave does not lapse "
                "under the Labour Code; this is the date the time-off plan "
                "removes it from their balance in Odoo.",
                employee=employee.name,
                amount=amount,
                unit=unit_word,
                leave=leave_name,
                date=expiry_str,
            )
            employee.activity_schedule(
                activity_type_id=activity_type.id,
                date_deadline=expiry,
                summary=summary,
                note=hr_note,
                user_id=hr_user.id,
            )
            delivered = True

        # --- Channel 3: email to the employee --------------------------
        if mail_template and employee.work_email:
            mail_template.send_mail(self.id, force_send=False)
            delivered = True
        return delivered
