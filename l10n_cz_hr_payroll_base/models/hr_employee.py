# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech payroll fields of the working version, surfaced on the employee.

``hr.employee`` delegates to its working version through ``_inherits`` on
``version_id``, so these are ``inherited`` related fields: writable, and stored
on the version. The engine modules re-declare them with their payroll group,
as on ``hr.version``.
"""

from datetime import datetime, time, timedelta

from odoo import fields, models

from .hr_version import CZ_PAYROLL_GROUP

#: § 192 odst. 1 ZP: the employer pays náhrada mzdy for the first 14 calendar
#: days of a dočasná pracovní neschopnost; from day 15 the employee draws
#: nemocenské from ČSSZ instead.
CZ_SICK_EMPLOYER_DAYS = 14


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_cz_tax_declaration = fields.Boolean(
        readonly=False, related="version_id.l10n_cz_tax_declaration",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_claim_ztpp = fields.Boolean(
        readonly=False, related="version_id.l10n_cz_claim_ztpp",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_disability = fields.Selection(
        readonly=False, related="version_id.l10n_cz_disability",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t1 = fields.Integer(
        readonly=False, related="version_id.l10n_cz_children_t1",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t2 = fields.Integer(
        readonly=False, related="version_id.l10n_cz_children_t2",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t3 = fields.Integer(
        readonly=False, related="version_id.l10n_cz_children_t3",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_ztpp = fields.Integer(
        readonly=False, related="version_id.l10n_cz_children_ztpp",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_is_state_insured = fields.Boolean(
        readonly=False, related="version_id.l10n_cz_is_state_insured",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_agreement_type = fields.Selection(
        readonly=False, related="version_id.l10n_cz_agreement_type",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_meal_allowance = fields.Monetary(
        readonly=False, related="version_id.l10n_cz_meal_allowance",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_garnishment_dependents = fields.Integer(
        readonly=False, related="version_id.l10n_cz_garnishment_dependents",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_avg_hourly_earnings = fields.Monetary(
        readonly=False, related="version_id.l10n_cz_avg_hourly_earnings",
        inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_social_discount_category = fields.Selection(
        readonly=False, related="version_id.l10n_cz_social_discount_category",
        inherited=True, groups=CZ_PAYROLL_GROUP)

    def _l10n_cz_sick_hours_after_employer_period(
        self, date_from, date_to, calendar, is_sick_type
    ):
        """Sick-leave hours in *date_from*..*date_to* past the 14th DPN day.

        § 192 odst. 1 zákoníku práce limits the employer's náhrada mzdy to
        "prvních 14 kalendářních dnů trvání dočasné pracovní neschopnosti".
        A DPN often spans two payslips, and is often recorded as several
        consecutive time-off requests (the doctor extends it), so the 14 days
        are counted from the first day of the uninterrupted chain, not from the
        start of each request or of the payslip period.

        *is_sick_type* is the engine's predicate on ``hr.leave.type``: the two
        payroll engines tag the sickness leave type differently.

        Returns the hours to take OFF the sick hours the payslip would
        otherwise compensate. Hours the engine cannot trace to a time-off
        request (a manual work entry, the SICK_HOURS input) are never cut.
        """
        self.ensure_one()
        if not calendar:
            return 0.0
        leaves = self.env["hr.leave"].sudo().search(
            [
                ("employee_id", "=", self.id),
                ("state", "=", "validate"),
                ("request_date_from", "<=", date_to),
            ],
            order="request_date_from, id",
        ).filtered(lambda leave: is_sick_type(leave.holiday_status_id))
        last_paid_day = {}
        chain_start = chain_end = None
        for leave in leaves:
            start = leave.request_date_from
            end = leave.request_date_to or start
            if chain_end is None or start > chain_end + timedelta(days=1):
                chain_start = start
            chain_end = max(chain_end or end, end)
            last_paid_day[leave.id] = chain_start + timedelta(
                days=CZ_SICK_EMPLOYER_DAYS - 1)
        if not last_paid_day:
            return 0.0
        excess = 0.0
        for day, hours, cal_leave in self.list_leaves(
            datetime.combine(date_from, time.min),
            datetime.combine(date_to, time.max),
            calendar=calendar,
        ):
            leave_id = cal_leave.holiday_id.id
            if leave_id in last_paid_day and day > last_paid_day[leave_id]:
                excess += hours
        return excess
