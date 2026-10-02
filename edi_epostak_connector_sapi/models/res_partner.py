"""Peppol reachability preflight on the partner form.

The commonest ePošťák support case is not a transport failure but a
counterparty whose EAS/endpoint is wrong or who is not registered on the
network at all. Left to the send path that surfaces as a 422 on a posted
invoice; here it is one click while editing the partner.
"""

import logging

from odoo import _, models
from odoo.exceptions import UserError

from .epostak_connector import EpostakApiError

_logger = logging.getLogger(__name__)

# The BIS Billing 3.0 document types a deployment on this stack actually
# sends. Slovakia mandates plain BIS3 with no national CIUS, so these are the
# identifiers a Slovak receiver must advertise.
BIS3_DOCUMENT_TYPES = [
    "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2::Invoice"
    "##urn:cen.eu:en16931:2017#compliant#"
    "urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1",
    "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2::CreditNote"
    "##urn:cen.eu:en16931:2017#compliant#"
    "urn:fdc:peppol.eu:2017:poacc:billing:3.0::2.1",
]


class ResPartner(models.Model):
    _inherit = "res.partner"

    def action_epostak_check_peppol(self):
        """Look this partner up in the Peppol directory via ePošťák."""
        self.ensure_one()
        connector = self.env["epostak.connector"]
        partner = self.commercial_partner_id
        participant = connector._epostak_participant(
            partner.peppol_eas, partner.peppol_endpoint
        )
        if not participant:
            raise UserError(
                _(
                    "%s has no Peppol address. Set both the Peppol e-address "
                    "(EAS) and the Peppol Endpoint before checking.",
                    partner.display_name,
                )
            )

        try:
            result = connector._check_capabilities(participant, BIS3_DOCUMENT_TYPES)
        except EpostakApiError as e:
            # EpostakApiError is a plain Exception, so letting it escape a
            # button hands the user an RPC traceback instead of a dialog. The
            # provider's own message is usually the actionable part, so keep it.
            raise UserError(
                _(
                    "Could not check %(partner)s against the Peppol directory:"
                    "\n\n%(error)s",
                    partner=partner.display_name,
                    error=e,
                )
            ) from e
        found = bool(result.get("found"))
        accepts = bool(result.get("accepts"))
        ready = result.get("networkReady")

        if found and accepts:
            kind, title = "success", _("Reachable on Peppol")
            message = _(
                "%(participant)s is registered and accepts Peppol BIS "
                "Billing 3.0 invoices and credit notes.",
                participant=participant,
            )
        elif found:
            kind, title = "warning", _("Registered, but not for BIS3 billing")
            message = _(
                "%(participant)s exists on the network but does not advertise "
                "the Peppol BIS Billing 3.0 invoice and credit note types. "
                "Sending will be refused.",
                participant=participant,
            )
        else:
            kind, title = "danger", _("Not found on Peppol")
            message = _(
                "%(participant)s is not registered in the Peppol directory. "
                "Check the EAS scheme and the endpoint value.",
                participant=participant,
            )
        if ready is False:
            message += " " + _("(The provider reports the participant as not "
                               "network-ready.)")

        return {
            "type": "ir.actions.client",
            "tag": "display_notification",
            "params": {
                "type": kind,
                "sticky": kind != "success",
                "title": title,
                "message": message,
            },
        }
