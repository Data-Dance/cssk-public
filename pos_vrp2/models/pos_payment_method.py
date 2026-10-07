from odoo import api, fields, models

# The payment types the VRP2 web app offers (optionsTypPlatidla, app.js).
# KVERKOM (QR payment) is sent as OTHER by the app itself; EXPENSE is not a
# tender but the refund line of a negative receipt, so neither is listed.
VRP2_PAYMENT_TYPES = [
    ("CASH", "Hotovosť"),
    ("CARD", "Platobná karta"),
    ("VOUCHER", "Poukážky"),
    ("GASTRO", "Stravné poukážky"),
    ("OTHER", "Iné"),
]


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    vrp2_payment_type = fields.Selection(
        VRP2_PAYMENT_TYPES,
        string="VRP2 Payment Type",
        compute="_compute_vrp2_payment_type",
        store=True,
        readonly=False,
        help="How payments by this method are reported on the VRP2 receipt. "
        "Defaults from the journal: cash → Hotovosť, bank → Platobná karta. "
        "Empty means the method is not a cash-register tender (a customer "
        "account), and an order paid by it cannot be fiscalized.",
    )

    @api.depends("journal_id.type")
    def _compute_vrp2_payment_type(self):
        for method in self:
            journal_type = method.journal_id.type
            if journal_type == "cash":
                method.vrp2_payment_type = "CASH"
            elif journal_type == "bank":
                method.vrp2_payment_type = "CARD"
            else:
                method.vrp2_payment_type = False
