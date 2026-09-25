"""Register the MultiCash payment methods with the OCA payment-order framework."""
from odoo import api, models


_MULTICASH_CODES = (
    'multicash_cfd', 'multicash_cfu', 'multicash_cfa', 'multicash_mt101',
)


class AccountPaymentMethod(models.Model):
    _inherit = 'account.payment.method'

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        for code in _MULTICASH_CODES:
            res[code] = {'mode': 'multi', 'domain': [('type', '=', 'bank')]}
        return res
