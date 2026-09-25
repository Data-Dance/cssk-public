# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# On 19.0 the payroll attributes live on the employee's current version
# (``hr.version``).  They are surfaced here as delegated (``inherited``) related
# fields so they can be read/edited straight from the employee form.

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

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
