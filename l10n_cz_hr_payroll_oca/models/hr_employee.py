# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
# In 19.0 the Czech payroll attributes live on the employee's working version
# (hr.version). hr.employee delegates to that version via ``_inherits`` on
# ``version_id``, so we surface the fields here as ``inherited`` related fields
# (writable, group-guarded) for convenience/reporting.

from odoo import fields, models

CZ_PAYROLL_GROUP = "payroll.group_payroll_user"


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_cz_tax_declaration = fields.Boolean(
        related="version_id.l10n_cz_tax_declaration",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_claim_ztpp = fields.Boolean(
        related="version_id.l10n_cz_claim_ztpp",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_disability = fields.Selection(
        related="version_id.l10n_cz_disability",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t1 = fields.Integer(
        related="version_id.l10n_cz_children_t1",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t2 = fields.Integer(
        related="version_id.l10n_cz_children_t2",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t3 = fields.Integer(
        related="version_id.l10n_cz_children_t3",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_ztpp = fields.Integer(
        related="version_id.l10n_cz_children_ztpp",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_is_state_insured = fields.Boolean(
        related="version_id.l10n_cz_is_state_insured",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_agreement_type = fields.Selection(
        related="version_id.l10n_cz_agreement_type",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_dpp_notified = fields.Boolean(
        related="version_id.l10n_cz_dpp_notified",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_meal_allowance = fields.Monetary(
        related="version_id.l10n_cz_meal_allowance",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_garnishment_dependents = fields.Integer(
        related="version_id.l10n_cz_garnishment_dependents",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_avg_hourly_earnings = fields.Monetary(
        related="version_id.l10n_cz_avg_hourly_earnings",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
    l10n_cz_social_discount_category = fields.Selection(
        related="version_id.l10n_cz_social_discount_category",
        readonly=False, inherited=True, groups=CZ_PAYROLL_GROUP)
