# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    recycling_fee_presentation = fields.Selection(
        [
            ("included", "Included in the price"),
            ("on_top", "Separate line on top of the price"),
        ],
        default="included",
        required=True,
        help="Included: the fee is part of the unit price and each line says "
        "'z toho recyklační příspěvek …' — the presentation of MŽP's model "
        "invoices (unit price 'vč. příspěvku na recyklaci'). "
        "On top: prices exclude the fee and it is invoiced as its own line; "
        "the product line then states the fee as a separate item. Both "
        "satisfy CZ § 73 odst. 1 and SK § 34 ods. 1 písm. d), which require the "
        "fee to be stated separately, not how.",
    )
