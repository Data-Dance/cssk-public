"""POS order hooks for QR Platba (SK) payments."""

import logging

from odoo import _, models
from odoo.exceptions import UserError

from odoo.addons.account_qr_code_payme_sk.models.res_bank import generate as payme_generate

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    def _get_nop_pos_config(self):
        """Return the pos.config with NOP configured, or raise."""
        self.ensure_one()
        cfg = self.config_id
        if not cfg.nop_environment:
            raise UserError(
                _("POS '%s' is not configured for NOP KVERKOM (no environment set).")
                % cfg.display_name
            )
        return cfg

    def create_qr_platba_transaction(self, amount):
        """Mint a NOP tx, create a payment.transaction, return payload for POS popup."""
        self.ensure_one()
        if self.state in ("paid", "done", "cancel"):
            raise UserError(_("Order %s is not payable.") % self.display_name)

        payment_method = self.online_payment_method_id
        if not payment_method or not payment_method.is_qr_platba_sk:
            raise UserError(_("This POS is not configured for QR Platba."))

        cfg = self._get_nop_pos_config()
        currency = self.currency_id
        if currency.name != "EUR":
            raise UserError(_("QR Platba only supports EUR."))

        timeout_seconds = max(30, payment_method.qr_platba_timeout_seconds or 300)
        nop_tx = self.env["nop.transaction"].sudo()._create_for_pos_config(
            pos_config=cfg,
            amount=amount,
            comment=f"POS {self.pos_reference or self.name}",
            source_model="pos.order",
            source_id=self.id,
            currency=currency,
            expires_in_seconds=timeout_seconds,
        )

        qr_url = payme_generate(
            amount=amount,
            iban=cfg.nop_iban_id.sanitized_acc_number,
            beneficiary_name=cfg.nop_merchant_name or cfg.nop_iban_id.acc_holder_name or "",
            currency=currency.name,
            originator_ref=nop_tx.transaction_id,
            note=nop_tx.transaction_id,
        )
        nop_tx.qr_code_url = qr_url

        payment_tx = self._create_qr_platba_payment_transaction(
            payment_method=payment_method,
            amount=amount,
            nop_tx=nop_tx,
        )
        nop_tx.payment_transaction_id = payment_tx.id

        return {
            "transaction_id": nop_tx.transaction_id,
            "nop_transaction_id": nop_tx.id,
            "payment_transaction_id": payment_tx.id,
            "qr_url": qr_url,
            "expires_at": nop_tx.expires_at and nop_tx.expires_at.isoformat(),
            "timeout_seconds": timeout_seconds,
        }

    def _create_qr_platba_payment_transaction(self, payment_method, amount, nop_tx):
        self.ensure_one()
        provider = self.env["payment.provider"].sudo().search(
            [("code", "=", "qr_platba_sk"), ("company_id", "=", self.company_id.id)],
            limit=1,
        )
        if not provider:
            provider = self.env["payment.provider"].sudo().search(
                [("code", "=", "qr_platba_sk")], limit=1
            )
        if not provider:
            raise UserError(_("No QR Platba payment provider is configured."))

        payment_method_payment = provider.payment_method_ids[:1]
        if not payment_method_payment:
            raise UserError(
                _("Provider %s has no payment method assigned.") % provider.display_name
            )

        partner = self.partner_id or self.company_id.partner_id
        tx = self.env["payment.transaction"].sudo().create({
            "provider_id": provider.id,
            "payment_method_id": payment_method_payment.id,
            "reference": f"{self.pos_reference or self.name}-{nop_tx.transaction_id}",
            "amount": amount,
            "currency_id": self.currency_id.id,
            "partner_id": partner.id,
            "pos_order_id": self.id,
            "state": "pending",
        })
        return tx

    def cancel_qr_platba_transaction(self, nop_transaction_id):
        """Cashier explicitly cancels: "the customer did not pay"."""
        self.ensure_one()
        nop_tx = self.env["nop.transaction"].browse(int(nop_transaction_id)).exists()
        if not nop_tx:
            return True
        nop_tx.action_cancel()
        if nop_tx.payment_transaction_id and nop_tx.payment_transaction_id.state == "pending":
            nop_tx.payment_transaction_id.sudo()._set_canceled()
        return True

    def close_qr_platba_unconfirmed(self, nop_transaction_id):
        """Cashier closes the sale without NOP confirmation.

        Returns receipt data for the "doklad o nepotvrdení zrealizovanej platby".
        """
        self.ensure_one()
        nop_tx = self.env["nop.transaction"].browse(int(nop_transaction_id)).exists()
        if not nop_tx:
            raise UserError(_("NOP transaction %s not found.") % nop_transaction_id)

        cfg = nop_tx.pos_config_id
        cfg.sudo()._nop_poll_if_due(min_interval_seconds=0)
        nop_tx.invalidate_recordset(["state"])

        if nop_tx.state in ("received", "confirmed"):
            return {"already_confirmed": True, "state": nop_tx.state}

        nop_tx.sudo().action_close_unconfirmed()
        if nop_tx.payment_transaction_id and nop_tx.payment_transaction_id.state == "pending":
            nop_tx.payment_transaction_id.sudo()._set_canceled(
                state_message=_("Closed without NOP confirmation; customer to pay with another method.")
            )

        company = self.company_id.sudo()
        return {
            "already_confirmed": False,
            "state": nop_tx.state,
            "nop_transaction_id": nop_tx.id,
            "receipt": {
                "transaction_id": nop_tx.transaction_id,
                "created_at": nop_tx.create_date and nop_tx.create_date.isoformat(),
                "closed_at": nop_tx.closed_unconfirmed_at and nop_tx.closed_unconfirmed_at.isoformat(),
                "amount": nop_tx.expected_amount,
                "currency": nop_tx.currency_id.name,
                "iban": nop_tx.expected_iban,
                "merchant_name": cfg.nop_merchant_name or company.name,
                "merchant_ico": company.company_registry or "",
                "merchant_dic": cfg.nop_vatsk or "",
                "merchant_vat": company.vat or "",
                "pokladnica_id_ext": cfg.nop_pokladnica_id_ext or "",
                "environment": cfg.nop_environment or "",
                "cashier_name": self.env.user.name,
                "public_history_url": nop_tx.public_history_url or "",
            },
        }

    def get_and_set_online_payments_data(self, next_online_payment_amount=False):
        """Drain NOP opportunistically on every POS poll."""
        self.ensure_one()
        cfg = self.config_id
        if cfg.nop_environment:
            try:
                cfg.sudo()._nop_poll_if_due(min_interval_seconds=2)
            except Exception:
                _logger.exception("QR Platba drain failed for %s", cfg.display_name)
        return super().get_and_set_online_payments_data(next_online_payment_amount)
