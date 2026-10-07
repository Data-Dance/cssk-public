from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    vrp2_fiscalize_on_payment = fields.Boolean(
        string="Fiscalize invoice payments in VRP2",
        help="When enabled, the standard Register Payment wizard offers a "
        "'Fiscalize in VRP2' option that issues a VRP2 fiscal receipt for the "
        "customer-invoice payment it creates (payment + receipt in one "
        "transaction; a VRP2 error rolls both back).",
    )
