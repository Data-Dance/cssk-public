# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The Czech payroll fields of the current contract, surfaced on the employee.

18.0's ``hr.employee`` has no delegation to its contract (19.0 delegates to
``hr.version``), so these are read-only related fields on ``contract_id``, as
the engines declared them before they moved here. Edit them on the contract.
The engine modules re-declare them with their payroll group, as on
``hr.contract``.
"""

from datetime import datetime, time, timedelta

from odoo import fields, models

from .hr_contract import CZ_PAYROLL_GROUP

#: § 192 odst. 1 ZP: the employer pays náhrada mzdy for the first 14 calendar
#: days of a dočasná pracovní neschopnost; from day 15 the employee draws
#: nemocenské from ČSSZ instead.
CZ_SICK_EMPLOYER_DAYS = 14


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_cz_tax_declaration = fields.Boolean(
        related="contract_id.l10n_cz_tax_declaration",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_claim_ztpp = fields.Boolean(
        related="contract_id.l10n_cz_claim_ztpp",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_disability = fields.Selection(
        related="contract_id.l10n_cz_disability",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t1 = fields.Integer(
        related="contract_id.l10n_cz_children_t1",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t2 = fields.Integer(
        related="contract_id.l10n_cz_children_t2",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t3 = fields.Integer(
        related="contract_id.l10n_cz_children_t3",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_ztpp = fields.Integer(
        related="contract_id.l10n_cz_children_ztpp",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_is_state_insured = fields.Boolean(
        related="contract_id.l10n_cz_is_state_insured",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_agreement_type = fields.Selection(
        related="contract_id.l10n_cz_agreement_type",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_meal_allowance = fields.Monetary(
        related="contract_id.l10n_cz_meal_allowance",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_garnishment_dependents = fields.Integer(
        related="contract_id.l10n_cz_garnishment_dependents",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_avg_hourly_earnings = fields.Monetary(
        related="contract_id.l10n_cz_avg_hourly_earnings",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_social_discount_category = fields.Selection(
        related="contract_id.l10n_cz_social_discount_category",
        readonly=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_pensioner_discount = fields.Boolean(
        related="contract_id.l10n_cz_pensioner_discount",
        readonly=True, groups=CZ_PAYROLL_GROUP)

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
