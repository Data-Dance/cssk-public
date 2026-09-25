"""Bridge ``nop.transaction`` to ``payment.transaction`` for POS online payments."""

import logging

from odoo import _, models
from odoo.exceptions import ValidationError

_logger = logging.getLogger(__name__)


class PaymentTransaction(models.Model):
    _inherit = "payment.transaction"

    def _get_specific_rendering_values(self, processing_values):
        if self.provider_code == "qr_platba_sk":
            # The QR code is rendered client-side by the POS popup, not by a
            # redirect form. Return a minimal dict so the generic flow doesn't
            # complain.
            return {"api_url": "", "reference": self.reference}
        return super()._get_specific_rendering_values(processing_values)

    def _apply_updates(self, payment_data):
        if self.provider_code != "qr_platba_sk":
            return super()._apply_updates(payment_data)
        state = payment_data.get("state")
        if state == "done":
            self._set_done()
        elif state == "cancel":
            self._set_canceled()
        elif state == "error":
            self._set_error(payment_data.get("message") or _("NOP payment failed."))
        else:
            self._set_pending()

    def _mark_done_from_nop(self, nop_transaction):
        """Called by :meth:`nop.transaction._notify_downstream` on a confirmed push.

        Odoo 19 decoupled ``_set_done`` from ``_post_process`` (there's a cron
        that drains unprocessed txs), so we have to invoke ``_post_process``
        ourselves to keep the POS flow synchronous — the cashier cannot wait
        for the next cron tick.
        """
        self.ensure_one()
        if self.state in ("done", "authorized"):
            return
        if self.provider_code != "qr_platba_sk":
            raise ValidationError(
                _("_mark_done_from_nop called on a non-QR-Platba transaction")
            )
        self._apply_updates({"state": "done"})
        self._post_process()
