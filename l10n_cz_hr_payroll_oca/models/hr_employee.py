# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The employee mirrors of the Czech fields, restricted to this engine's
payroll users. Declared in ``l10n_cz_hr_payroll_base``; see ``hr_version``."""

from odoo import fields, models

from .hr_version import CZ_PAYROLL_GROUP


class HrEmployee(models.Model):
    _inherit = "hr.employee"

    l10n_cz_tax_declaration = fields.Boolean(groups=CZ_PAYROLL_GROUP)
    l10n_cz_claim_ztpp = fields.Boolean(groups=CZ_PAYROLL_GROUP)
    l10n_cz_disability = fields.Selection(groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t1 = fields.Integer(groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t2 = fields.Integer(groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_t3 = fields.Integer(groups=CZ_PAYROLL_GROUP)
    l10n_cz_children_ztpp = fields.Integer(groups=CZ_PAYROLL_GROUP)
    l10n_cz_is_state_insured = fields.Boolean(groups=CZ_PAYROLL_GROUP)
    l10n_cz_agreement_type = fields.Selection(groups=CZ_PAYROLL_GROUP)
    l10n_cz_meal_allowance = fields.Monetary(groups=CZ_PAYROLL_GROUP)
    l10n_cz_garnishment_dependents = fields.Integer(groups=CZ_PAYROLL_GROUP)
    l10n_cz_avg_hourly_earnings = fields.Monetary(groups=CZ_PAYROLL_GROUP)
    l10n_cz_social_discount_category = fields.Selection(groups=CZ_PAYROLL_GROUP)
