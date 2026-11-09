# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    l10n_cz_partial_unemployment_pct = fields.Float(
        related="company_id.l10n_cz_partial_unemployment_pct",
        readonly=False,
    )
    # account's country_code is not available: this module depends on hr only.
    l10n_cz_company_country_code = fields.Char(
        "Company Country (Czech payroll)",
        related="company_id.country_id.code",
    )
