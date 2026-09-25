"""Hook ``nop.transaction`` confirmations into the pos_online_payment flow."""

import logging

from odoo import models

_logger = logging.getLogger(__name__)


class NopTransaction(models.Model):
    _inherit = "nop.transaction"

    def _notify_downstream(self):
        super()._notify_downstream()
        for nop_tx in self.filtered(lambda r: r.state == "received" and r.payment_transaction_id):
            payment_tx = nop_tx.payment_transaction_id.sudo()
            _logger.info(
                "NOP finalize: nop_tx=%s payment_tx=%s provider_code=%s payment_tx.state=%s",
                nop_tx.transaction_id, payment_tx.id, payment_tx.provider_code, payment_tx.state,
            )
            if payment_tx.provider_code != "qr_platba_sk":
                continue
            if payment_tx.state in ("done", "authorized"):
                nop_tx.state = "confirmed"
                continue
            # Savepoint so a failure in _post_process (e.g. account.payment
            # creation) doesn't taint the outer transaction and roll back the
            # nop.transaction state write.
            try:
                with self.env.cr.savepoint():
                    payment_tx._mark_done_from_nop(nop_tx)
                    # _mark_done_from_nop → _set_done → _post_process →
                    # _process_pos_online_payment creates pos.payment +
                    # account.payment and fires ONLINE_PAYMENTS_NOTIFICATION.
                nop_tx.state = "confirmed"
                _logger.info("NOP finalize OK: nop_tx=%s -> confirmed", nop_tx.transaction_id)
            except Exception:
                _logger.exception(
                    "Failed to finalize payment.transaction %s for NOP tx %s",
                    payment_tx.id,
                    nop_tx.transaction_id,
                )
        return True
