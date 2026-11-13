# -*- coding: utf-8 -*-
from odoo import fields, models


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    l10n_cz_eet2_contact_payment = fields.Boolean(
        string="EET 2.0 Contact Payment", default=True,
        help="Payments made in person / on premises (cash, card, QR) are "
            "recorded by EET 2.0. Disable for remote payments that are out of "
            "scope (no physical contact).")
