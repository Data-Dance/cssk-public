# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# hr.employee exposes a single `contract_id` (current contract), so the Slovak
# payroll attributes stored on the contract are surfaced here as related fields
# for convenience/reporting.

from odoo import fields, models


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_sk_tax_declaration_signed = fields.Boolean(
        related="contract_id.l10n_sk_tax_declaration_signed",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_children_under_15 = fields.Integer(
        related="contract_id.l10n_sk_children_under_15",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_children_15_18 = fields.Integer(
        related="contract_id.l10n_sk_children_15_18",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_ztp = fields.Boolean(
        related="contract_id.l10n_sk_ztp",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_health_oop_claim = fields.Boolean(
        related="contract_id.l10n_sk_health_oop_claim",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_agreement_type = fields.Selection(
        related="contract_id.l10n_sk_agreement_type",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_agreement_oop = fields.Boolean(
        related="contract_id.l10n_sk_agreement_oop",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_garnishment_dependents = fields.Integer(
        related="contract_id.l10n_sk_garnishment_dependents",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_meal_allowance_type = fields.Selection(
        related="contract_id.l10n_sk_meal_allowance_type",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_meal_voucher_employee = fields.Monetary(
        related="contract_id.l10n_sk_meal_voucher_employee",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
    l10n_sk_meal_voucher_employer = fields.Monetary(
        related="contract_id.l10n_sk_meal_voucher_employer",
        readonly=True,
        groups="payroll.group_payroll_user",
    )
