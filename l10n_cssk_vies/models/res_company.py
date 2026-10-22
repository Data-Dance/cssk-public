# Copyright 2026 Data Dance s.r.o.
# Data Dance Proprietary License v1.0 — see the LICENSE file.

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    vies_use_direct = fields.Boolean(
        string="Use direct EU VIES (no IAP)",
        help="Validate EU VAT numbers by calling the European Commission VIES "
        "service directly instead of routing through Odoo IAP. Stores the "
        "official consultation number returned by VIES as proof of check.",
    )
