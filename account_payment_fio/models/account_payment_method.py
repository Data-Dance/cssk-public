# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Register the Fio XML payment method with the OCA payment-order framework."""

from odoo import api, models

FIO_XML_CODE = "fio_xml"


class AccountPaymentMethod(models.Model):
    _inherit = "account.payment.method"

    @api.model
    def _get_payment_method_information(self):
        res = super()._get_payment_method_information()
        res[FIO_XML_CODE] = {"mode": "multi", "domain": [("type", "=", "bank")]}
        return res
