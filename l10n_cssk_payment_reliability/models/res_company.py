# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    cssk_reliability_autocheck = fields.Boolean(
        string="Auto-check supplier reliability",
        default=True,
        help="Check the supplier's tax reliability, VAT-deregistration listing "
        "and registered bank accounts when a vendor bill or an outbound "
        "supplier payment is posted, and daily for bills still unpaid; warn "
        "if there is a risk. Never blocks posting or payment.",
    )
