# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration of default value for Partner Autocomplete Provider."""

    _inherit = "res.config.settings"
    _description = "Provider"

    partner_autocomplete_provider = fields.Selection(
        related="company_id.partner_autocomplete_provider",
        readonly=False,
    )
