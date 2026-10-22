# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    vies_use_direct = fields.Boolean(
        related="company_id.vies_use_direct", readonly=False
    )
