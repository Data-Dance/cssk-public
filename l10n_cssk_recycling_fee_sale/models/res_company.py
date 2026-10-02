# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    recycling_fee_product_id = fields.Many2one(
        "product.product",
        string="Recycling Fee Product",
        domain="[('type', '=', 'service')]",
        help="Service product used for the separate fee lines when the fee is "
        "invoiced on top of the price. Its income account is where the fee is "
        "booked; its taxes are NOT used — each fee line takes the VAT of the "
        "goods it belongs to, since the fee is part of the consideration for "
        "that supply.",
    )
