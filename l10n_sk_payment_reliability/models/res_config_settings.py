# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    fa_api_key = fields.Char(
        string="FS open-data API key",
        config_parameter="fa_api_key",
        help="API key for the Slovak Financial Administration open-data service "
        "(opendata.financnasprava.sk), used to look up registered bank accounts "
        "and the tax-reliability index.",
    )
