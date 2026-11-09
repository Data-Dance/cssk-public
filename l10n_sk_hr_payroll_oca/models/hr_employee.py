# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# On 19.0 the payroll attributes live on the employee's current version
# (``hr.version``).  They are surfaced here as delegated (``inherited``) related
# fields so they can be read/edited straight from the employee form.

from datetime import date

from odoo import _, fields, models
from odoo.exceptions import UserError


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    def _l10n_sk_january_tax_version(self, year, company, as_of):
        """Read the dated declaration, including a genuine midyear hire.

        The first version at hiring records the declared January status when
        this employer had no January version. Later awards remain later facts.
        Never backdate employment or use a version later than the calculation.
        """
        self.ensure_one()
        january = date(year, 1, 1)
        version = self._get_version(january)
        if (not version or version.date_version > january
                or (version.contract_date_end and version.contract_date_end < january)):
            # No employment here on 1 January: a hire, or a rehire after an
            # employment that ended earlier. The first version of the
            # employment starting this year carries the declared status.
            first = self.env['hr.version'].search([
                ('employee_id', '=', self.id),
                ('date_version', '>=', january),
                ('date_version', '<=', as_of),
            ], order='date_version, id', limit=1)
            if (not first or not first.contract_date_start
                    or first.contract_date_start <= january):
                raise UserError(_("Record the employee's pension tax fact on a version effective at 1 January before claiming monthly allowance."))
            version = first
        if version.company_id != company:
            raise UserError(_("Review the employee's 1 January pension version in the payroll company."))
        return version

    l10n_sk_tax_declaration_signed = fields.Boolean(
        related="version_id.l10n_sk_tax_declaration_signed",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_children_under_15 = fields.Integer(
        related="version_id.l10n_sk_children_under_15",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_children_15_18 = fields.Integer(
        related="version_id.l10n_sk_children_15_18",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_ztp = fields.Boolean(
        related="version_id.l10n_sk_ztp",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_health_oop_claim = fields.Boolean(
        related="version_id.l10n_sk_health_oop_claim",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_health_exempt = fields.Boolean(
        related="version_id.l10n_sk_health_exempt",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_guarantee_exempt = fields.Boolean(
        related="version_id.l10n_sk_guarantee_exempt",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_hourly_wage = fields.Monetary(
        related="version_id.l10n_sk_hourly_wage",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_agreement_type = fields.Selection(
        related="version_id.l10n_sk_agreement_type",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_pension_type = fields.Selection(
        related="version_id.l10n_sk_pension_type",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_agreement_oop = fields.Boolean(
        related="version_id.l10n_sk_agreement_oop",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_garnishment_dependents = fields.Integer(
        related="version_id.l10n_sk_garnishment_dependents",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_meal_allowance_type = fields.Selection(
        related="version_id.l10n_sk_meal_allowance_type",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_meal_days = fields.Integer(
        related="version_id.l10n_sk_meal_days",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_meal_voucher_employee = fields.Monetary(
        related="version_id.l10n_sk_meal_voucher_employee",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_meal_voucher_employer = fields.Monetary(
        related="version_id.l10n_sk_meal_voucher_employer",
        inherited=True,
        readonly=False,
        groups="payroll.group_payroll_user",
    )
