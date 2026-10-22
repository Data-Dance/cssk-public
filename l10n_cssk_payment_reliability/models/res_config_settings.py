# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import fields, models


class ResConfigSettings(models.TransientModel):
    _inherit = "res.config.settings"

    cssk_reliability_autocheck = fields.Boolean(
        related="company_id.cssk_reliability_autocheck", readonly=False
    )
