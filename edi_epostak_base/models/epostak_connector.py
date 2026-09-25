"""ePošťák connector — provider identity, environment configuration and the
Peppol addressing metadata that every ePošťák wire protocol needs.

ePošťák (https://epostak.sk) is a Slovak Peppol Access Point. Unlike the
EDIFACT providers in this stack it carries **only** Peppol documents, so the
routing metadata it wants on the wire (participant ids, document type id,
process id) is derivable from the UBL payload itself — which is also the only
way to satisfy the API's ``SAPI-DOC-025`` rule that the ``cbc:EndpointID``
inside the document must agree with the metadata sent alongside it.

This module holds that derivation plus the mode/credential plumbing; the
concrete HTTP transport lives in ``edi_epostak_connector_sapi``.
"""

import logging
from xml.etree import ElementTree

from odoo import _, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

SANDBOX = "sandbox"
PRODUCTION = "production"

# SAPI-SK 1.0 — the UBL-in / UBL-out surface we transport over.
DEFAULT_SAPI_URLS = {
    SANDBOX: "https://dev.epostak.sk/sapi/v1",
    PRODUCTION: "https://epostak.sk/sapi/v1",
}
# Enterprise API — same credentials, used only for the lifecycle endpoints
# SAPI does not carry (outbound delivery status, participant capabilities).
DEFAULT_API_URLS = {
    SANDBOX: "https://dev.epostak.sk/api/v1",
    PRODUCTION: "https://epostak.sk/api/v1",
}

# UBL 2.1 namespaces of the three document kinds that cross a Peppol AP.
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"

# A Peppol participant identifier is sometimes written with its ICD prefix
# (``iso6523-actorid-upis::0245:2121576435``); ePošťák echoes that longer form
# back on inbound metadata but wants the bare ``scheme:value`` on send.
PARTICIPANT_PREFIX = "iso6523-actorid-upis::"

# ICD 0245 addresses a Slovak company by its DIČ, which is exactly ten digits.
# The IČO (eight digits) is a different register and is NOT routable: ePošťák
# answers an unknown participant with 400 SAPI-VAL-004 "Invalid participant
# ID", which reads like a format complaint and sends you looking for padding
# or a prefix. Catch the confusion here, where we can name it.
SK_DIC_SCHEME = "0245"
SK_DIC_LENGTH = 10

# Peppol document type identifiers are structurally
# ``<root-namespace>::<root-element>##<CustomizationID>::<UBLVersionID>``.
# BIS3 documents omit cbc:UBLVersionID, and the network assumes 2.1.
DEFAULT_UBL_VERSION = "2.1"


class EpostakConnector(models.TransientModel):
    _name = "epostak.connector"
    _inherit = ["edi.connector.mixin"]
    _description = "ePošťák Connector"

    # ------------------------------------------------------------------
    # Configuration
    # ------------------------------------------------------------------

    def _get_mode(self):
        """Return the active environment: 'sandbox' or 'production'."""
        return (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("epostak.mode", SANDBOX)
        )

    def _get_config(self, mode=None):
        """Environment-level configuration shared by every ePošťák transport.

        Credentials themselves belong to the concrete connector (they are
        API-surface specific), so this returns only what identifies the
        environment and the firm we speak for.
        """
        ICP = self.env["ir.config_parameter"].sudo()
        mode = mode or self._get_mode()
        if mode not in (SANDBOX, PRODUCTION):
            mode = SANDBOX
        return {
            "mode": mode,
            "firm_id": ICP.get_param("epostak.firm_id", ""),
        }

    def _validate_config(self, mode=None):
        """Verify the deployment can address itself on the Peppol network.

        Every ePošťák call is scoped to a participant via the
        ``X-Peppol-Participant-Id`` header, so a company without an EAS +
        endpoint cannot send *or* poll. Fail here with a readable message
        rather than on a 403 FORBIDDEN from the API.
        """
        participant = self._epostak_own_participant_id()
        if not participant:
            raise UserError(
                _(
                    "The Peppol address of company %s is not configured. Set "
                    "the Peppol e-address (EAS) and Peppol Endpoint on the "
                    "company's partner record — ePošťák scopes every request "
                    "to that participant identifier.",
                    self.env.company.display_name,
                )
            )
        complaint = self._epostak_participant_complaint(participant)
        if complaint:
            raise UserError(
                _(
                    "The Peppol address of company %(company)s is not "
                    "routable: %(complaint)s",
                    company=self.env.company.display_name,
                    complaint=complaint,
                )
            )

    @classmethod
    def _epostak_participant_complaint(cls, participant):
        """Why ``participant`` cannot be routed, or '' when it looks fine.

        Only shapes we can judge locally are checked — an id that passes here
        may still be unknown to ePošťák. Returned rather than raised so the
        same rule can annotate a partner without blocking one.
        """
        scheme, _sep, value = (participant or "").partition(":")
        if scheme != SK_DIC_SCHEME:
            return ""
        if value.isdigit() and len(value) == SK_DIC_LENGTH:
            return ""
        hint = ""
        if value.isdigit() and len(value) == 8:
            hint = _(
                " That looks like an IČO; scheme 0245 addresses the DIČ, "
                "which is a different number."
            )
        return _(
            "scheme %(scheme)s expects a %(length)s-digit Slovak DIČ, but the "
            "endpoint is %(value)r.%(hint)s",
            scheme=SK_DIC_SCHEME,
            length=SK_DIC_LENGTH,
            value=value,
            hint=hint,
        )

    # ------------------------------------------------------------------
    # Peppol participant identifiers
    # ------------------------------------------------------------------

    @staticmethod
    def _epostak_participant(scheme, value):
        """Join an EAS scheme and an endpoint value into ``scheme:value``.

        Returns '' when either half is missing — callers treat that as "not
        addressable" rather than sending a malformed identifier.
        """
        scheme = (scheme or "").strip()
        value = (value or "").strip()
        if not scheme or not value:
            return ""
        return "%s:%s" % (scheme, value)

    @classmethod
    def _epostak_normalize_participant(cls, value):
        """Strip the ``iso6523-actorid-upis::`` ICD prefix if present."""
        value = (value or "").strip()
        if value.startswith(PARTICIPANT_PREFIX):
            return value[len(PARTICIPANT_PREFIX):]
        return value

    def _epostak_own_participant_id(self, company=None):
        """Our own Peppol participant id, from the company partner."""
        company = company or self.env.company
        partner = company.partner_id.commercial_partner_id
        return self._epostak_participant(
            partner.peppol_eas, partner.peppol_endpoint
        )

    # ------------------------------------------------------------------
    # UBL introspection
    # ------------------------------------------------------------------

    @staticmethod
    def _epostak_fromstring(xml_content):
        """Parse a payload into an ElementTree root, refusing any DTD.

        Mirrors the hardening in ``edi_base_peppol``: BIS3 UBL never carries a
        DTD, so rejecting one defuses entity-expansion attacks on payloads
        that reach us from the network. Returns None on anything unparseable.
        """
        if not xml_content:
            return None
        raw = (
            xml_content.encode("utf-8")
            if isinstance(xml_content, str)
            else xml_content
        )
        head = raw[:8192].lower()
        if b"<!doctype" in head or b"<!entity" in head:
            _logger.warning(
                "Refusing ePošťák payload containing a DTD/entity declaration"
            )
            return None
        try:
            return ElementTree.fromstring(raw)
        except ElementTree.ParseError:
            return None

    @classmethod
    def _epostak_endpoint(cls, root, *paths):
        """Return ``scheme:value`` for the first cbc:EndpointID found.

        Reads the ``schemeID`` attribute rather than the stored partner
        record: the API rejects a mismatch between the metadata participant
        and the document's own EndpointID (``SAPI-DOC-025``), so the document
        must be the single source of truth.
        """
        for path in paths:
            el = root.find(path)
            if el is None:
                continue
            value = (el.text or "").strip()
            scheme = (el.get("schemeID") or "").strip()
            if not value:
                continue
            # Tolerate an already-qualified value ("0245:2121576435").
            if not scheme and ":" in value:
                return cls._epostak_normalize_participant(value)
            joined = cls._epostak_participant(scheme, value)
            if joined:
                return joined
        return ""

    @classmethod
    def _epostak_parse_ubl(cls, xml_content):
        """Extract the ePošťák send metadata from a UBL payload.

        Returns a dict with ``document_id``, ``document_type_id``,
        ``process_id``, ``sender``, ``receiver`` and ``doc_kind`` — or an
        empty dict when the payload is not parseable UBL.

        Both UBL party shapes are handled: an Invoice/CreditNote addresses via
        ``cac:AccountingSupplierParty`` / ``cac:AccountingCustomerParty``,
        while an ApplicationResponse (MLR, Invoice Response) uses
        ``cac:SenderParty`` / ``cac:ReceiverParty``. In both cases "sender" is
        the document's *from* and "receiver" its *to*, which is what the API
        wants — including when we are the buyer answering a supplier.
        """
        root = cls._epostak_fromstring(xml_content)
        if root is None:
            return {}

        # ElementTree renders a namespaced tag as "{ns}Local".
        tag = root.tag
        if not tag.startswith("{"):
            return {}
        namespace, _sep, local_name = tag[1:].partition("}")
        if not namespace or not local_name:
            return {}

        def _text(path):
            el = root.find(path)
            return (el.text or "").strip() if el is not None else ""

        customization = _text(f"{{{CBC_NS}}}CustomizationID")
        if not customization:
            # Without a CustomizationID we cannot name a Peppol document type,
            # and the network has nothing to route on.
            return {}
        ubl_version = _text(f"{{{CBC_NS}}}UBLVersionID") or DEFAULT_UBL_VERSION

        sender = cls._epostak_endpoint(
            root,
            f"{{{CAC_NS}}}AccountingSupplierParty/{{{CAC_NS}}}Party/"
            f"{{{CBC_NS}}}EndpointID",
            f"{{{CAC_NS}}}SenderParty/{{{CBC_NS}}}EndpointID",
        )
        receiver = cls._epostak_endpoint(
            root,
            f"{{{CAC_NS}}}AccountingCustomerParty/{{{CAC_NS}}}Party/"
            f"{{{CBC_NS}}}EndpointID",
            f"{{{CAC_NS}}}ReceiverParty/{{{CBC_NS}}}EndpointID",
        )

        return {
            "doc_kind": local_name,
            "document_id": _text(f"{{{CBC_NS}}}ID"),
            "document_type_id": "%s::%s##%s::%s"
            % (namespace, local_name, customization, ubl_version),
            "process_id": _text(f"{{{CBC_NS}}}ProfileID"),
            "sender": sender,
            "receiver": receiver,
        }

    def _parse_envelope(self, raw):
        """Envelope accessor the base inbound poll uses for duplicate detection.

        ``edi_base._dedup_key_for_inbound`` asks the *connector* for a
        message id, and ``edi_base_peppol`` overrides that seam with the UBL
        ``cbc:ID`` — but only when it is installed. Answering here as well
        keeps dedup working for an ePošťák-only install instead of silently
        degrading to "no dedup" on an AttributeError.
        """
        parsed = self._epostak_parse_ubl(raw)
        return {"message_id": parsed.get("document_id", "")}

    def _epostak_document_metadata(self, msg, xml_content):
        """Build the ``metadata`` block for an outbound ePošťák submission.

        Raises UserError with a specific cause rather than letting the API
        answer 400/422 — a misaddressed document is a configuration problem
        the user has to fix on a partner record, and the HTTP error does not
        say which one.
        """
        parsed = self._epostak_parse_ubl(xml_content)
        if not parsed:
            raise UserError(
                _(
                    "%s does not carry a Peppol UBL document (no UBL root "
                    "element or no cbc:CustomizationID). ePošťák transports "
                    "Peppol documents only.",
                    msg.display_name,
                )
            )
        missing = [
            label
            for key, label in (
                ("sender", _("sender Peppol address")),
                ("receiver", _("receiver Peppol address")),
                ("process_id", _("cbc:ProfileID")),
                ("document_id", _("cbc:ID")),
            )
            if not parsed.get(key)
        ]
        if missing:
            raise UserError(
                _(
                    "The Peppol document %(name)s is missing: %(missing)s. "
                    "Check the Peppol e-address (EAS) and Endpoint on both "
                    "your company and the counterparty.",
                    name=msg.display_name,
                    missing=", ".join(missing),
                )
            )
        return parsed
