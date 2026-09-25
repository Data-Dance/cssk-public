"""Synthetic payment.provider ``qr_platba_sk``.

The provider exists so that NOP-confirmed payments can flow through the
standard ``pos_online_payment`` machinery (``payment.transaction`` →
``_process_pos_online_payment`` → ``pos.payment`` + ``account.payment`` →
``ONLINE_PAYMENTS_NOTIFICATION`` bus message). There is no redirect form,
no third-party webhook: the MQTT / REST poll in :mod:`nop_kverkom_base` is
what drives state transitions.
"""

from odoo import fields, models


class PaymentProvider(models.Model):
    _inherit = "payment.provider"

    code = fields.Selection(
        selection_add=[("qr_platba_sk", "QR Platba (SK)")],
        ondelete={"qr_platba_sk": "set default"},
    )

    def _get_default_payment_method_codes(self):
        self.ensure_one()
        if self.code == "qr_platba_sk":
            return ["qr_platba_sk"]
        return super()._get_default_payment_method_codes()

    def _get_supported_currencies(self):
        # QR Platba is SEPA Instant EUR-only.
        supported = super()._get_supported_currencies()
        if self.code == "qr_platba_sk":
            return supported.filtered(lambda c: c.name == "EUR")
        return supported
