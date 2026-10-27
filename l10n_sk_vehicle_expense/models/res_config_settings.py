# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_sk_fuel_income_ratio = fields.Float(
        related="company_id.l10n_sk_fuel_income_ratio", readonly=False
    )
    # Domain repeated: Odoo drops a string domain on a related field.
    l10n_sk_vehicle_nondeductible_account_id = fields.Many2one(
        related="company_id.l10n_sk_vehicle_nondeductible_account_id", readonly=False,
        domain="[('company_ids', 'in', company_id)]",
    )
    l10n_sk_vehicle_is_sk_company = fields.Boolean(
        related="company_id.l10n_sk_vehicle_is_sk_company"
    )
