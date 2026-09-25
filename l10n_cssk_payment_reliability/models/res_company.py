# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cssk_reliability_autocheck = fields.Boolean(
        string="Auto-check supplier reliability on bill posting",
        default=True,
        help="When a vendor bill is posted, automatically check the supplier's "
        "tax reliability and registered bank accounts and warn if there is a "
        "risk. Never blocks posting or payment.",
    )
