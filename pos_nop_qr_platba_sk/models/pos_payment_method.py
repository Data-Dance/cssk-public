from odoo import _, api, fields, models
from odoo.exceptions import ValidationError


class PosPaymentMethod(models.Model):
    _inherit = "pos.payment.method"

    is_qr_platba_sk = fields.Boolean(
        compute="_compute_is_qr_platba_sk",
        store=True,
    )
    qr_platba_timeout_seconds = fields.Integer(
        string="QR Platba — cashier timeout (s)",
        default=300,
        help=(
            "Seconds before the POS popup switches its status text to the "
            "red 'still no confirmation' prompt. The popup does not auto-close "
            "— the cashier must still pick an outcome explicitly."
        ),
    )

    @api.depends("is_online_payment", "online_payment_provider_ids.code")
    def _compute_is_qr_platba_sk(self):
        for pm in self:
            pm.is_qr_platba_sk = pm.is_online_payment and any(
                p.code == "qr_platba_sk" for p in pm.online_payment_provider_ids
            )

    @api.constrains("is_qr_platba_sk", "qr_platba_timeout_seconds")
    def _check_qr_platba_timeout_seconds(self):
        for pm in self:
            if pm.is_qr_platba_sk and pm.qr_platba_timeout_seconds < 30:
                raise ValidationError(
                    _("QR Platba timeout must be at least 30 seconds (got %d).")
                    % pm.qr_platba_timeout_seconds
                )

    @api.model
    def _load_pos_data_fields(self, config):
        fields_list = super()._load_pos_data_fields(config)
        fields_list += [
            "is_qr_platba_sk",
            "qr_platba_timeout_seconds",
        ]
        return fields_list

    def _is_write_forbidden(self, fields):
        return super()._is_write_forbidden(fields - {"qr_platba_timeout_seconds"})
