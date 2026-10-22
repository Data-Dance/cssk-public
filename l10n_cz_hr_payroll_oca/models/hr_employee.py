# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# hr.employee exposes a single `contract_id` (current contract), so the Czech
# payroll attributes stored on the contract are surfaced here as related fields
# for convenience/reporting.

from odoo import fields, models

CZ_PAYROLL_GROUP = "payroll.group_payroll_user"


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
    l10n_cz_dpp_notified = fields.Boolean(
        related="contract_id.l10n_cz_dpp_notified",
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
