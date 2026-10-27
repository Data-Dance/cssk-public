from odoo import fields, models


class ResCompany(models.Model):
    _inherit = "res.company"

    vrp2_fiscalize_on_payment = fields.Boolean(
        string="Fiscalize invoice payments in VRP2",
        help="When enabled, the standard Register Payment wizard offers a "
        "'Fiscalize in VRP2' option that issues a VRP2 fiscal receipt for the "
        "customer-invoice payment it creates. If VRP2 refuses the first "
        "receipt nothing is registered; once a receipt has been issued, a "
        "later failure keeps the payments and is noted on the invoice to be "
        "fiscalized again.",
    )
    vrp2_cash_rounding_id = fields.Many2one(
        "account.cash.rounding",
        string="VRP2 cash rounding",
        help="Where Register Payment books the 0.05 € rounding of a cash "
        "payment it fiscalizes: its profit account when the customer paid "
        "more than the invoice, its loss account when less.",
    )
