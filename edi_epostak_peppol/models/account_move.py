"""ePošťák transport wiring for the provider-neutral Peppol stack.

All Peppol/UBL logic lives in ``edi_base_peppol``. This module only tells that
base *how* to ship a Peppol ``edi.message`` — through the ePošťák access point
— by implementing the two transport hooks on ``account.move``.

The hooks are single-valued, so with more than one Peppol transport installed
(ePošťák alongside Editel eXite, say) the one that wins would otherwise be
decided by module load order. The ``peppol.transport`` setting makes that an
explicit choice instead.
"""

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _peppol_transports(self):
        return super()._peppol_transports() + ["epostak"]

    def _peppol_provider(self):
        if self._peppol_chosen_transport() == "epostak":
            return "epostak"
        return super()._peppol_provider()

    def _peppol_send(self, msg):
        """Dispatch an outbound Peppol edi.message through ePošťák.

        Routed on the provider stamped on the message rather than on the
        currently-selected transport: a message prepared while ePošťák was
        active must still leave through ePošťák after the setting changes,
        and vice versa.
        """
        self.ensure_one()
        if msg.provider != "epostak":
            return super()._peppol_send(msg)
        return msg._enqueue_send(self.env["epostak.connector"])
