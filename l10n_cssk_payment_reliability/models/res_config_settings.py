# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cssk_reliability_autocheck = fields.Boolean(
        related="company_id.cssk_reliability_autocheck", readonly=False
    )
