# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Register the BEST payment methods with the OCA payment-order framework."""
from odoo import api, models

KB_BEST_CODES = ("kb_best_domestic", "kb_best_foreign")


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        for code in KB_BEST_CODES:
            res[code] = {"mode": "multi", "domain": [("type", "=", "bank")]}
        return res
