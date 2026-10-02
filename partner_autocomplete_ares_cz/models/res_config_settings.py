# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    """Configuration of default values for Partner Autocomplete Provider."""

    _inherit = "res.config.settings"

    config_ares_cz_mapping_ico = fields.Many2one(
        "ir.model.fields",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.ico",
    )
    config_ares_cz_mapping_nace = fields.Many2one(
        "ir.model.fields",
        string="Prevailing activity (CZ-NACE 2025)",
        ondelete="set null",
        domain="[('model_id.model', '=', 'res.partner')]",
        config_parameter="ares_cz.mapping.nace",
        help="Partner field receiving the prevailing activity from the "
        "statistical register (RES). Costs one more ARES request per lookup; "
        "empty: not fetched.",
    )
