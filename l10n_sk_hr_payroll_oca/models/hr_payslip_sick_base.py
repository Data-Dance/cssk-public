# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""What the OCA engine supplies to the determined daily base of sick pay.

The rules of § 8 zákona 462/2003 Z. z. are in ``l10n_sk_hr_payroll_base``;
here are the engine's own GROSS while a payslip is computed, the wage a
contract would pay for a month, and how a missing base is said.
"""

from datetime import datetime, time

from odoo import fields, models
from odoo.exceptions import UserError


class HrPayslip(models.Model):
    _inherit = "hr.payslip"

    l10n_sk_sick_pay_warning = fields.Char(
        string="Sick Pay Warning",
        compute="_compute_l10n_sk_sick_pay_warning",
    )

    def _compute_l10n_sk_sick_pay_warning(self):
        for slip in self:
            computed = slip.state in ("draft", "verify") and slip.line_ids
            slip.l10n_sk_sick_pay_warning = (
                computed and slip._l10n_sk_pn_missing_base_message()
            ) or False

    def compute_sheet(self):
        return super(
            HrPayslip, self._l10n_sk_with_live_categories()
        ).compute_sheet()

    def _get_baselocaldict(self, contracts):
        localdict = super()._get_baselocaldict(contracts)
        self._l10n_sk_register_live_categories(localdict["categories"].dict)
        return localdict

    def _l10n_sk_month_wage_due(self, month_first, month_last):
        self.ensure_one()
        version = self._l10n_sk_version()
        if not version.l10n_sk_hourly_wage:
            return self._l10n_sk_monthly_cash_wage(version)
        calendar = version.resource_calendar_id
        if not calendar:
            return None
        scheduled = self.employee_id._get_work_days_data_batch(
            datetime.combine(month_first, time.min),
            datetime.combine(month_last, time.max),
            calendar=calendar,
            compute_leaves=False,
        )
        hours = scheduled.get(self.employee_id.id, {}).get("hours", 0.0)
        return hours * version.l10n_sk_hourly_wage

    def action_payslip_done(self):
        """Refuse to confirm a payslip that owes sick pay it could not compute."""
        pending = self.filtered(lambda slip: slip.state != "done")
        result = super().action_payslip_done()
        for slip in pending:
            message = slip._l10n_sk_pn_missing_base_message()
            if message:
                raise UserError(message)
        return result
