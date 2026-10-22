"""Outbound Peppol BIS 3.0 generation + send action on account.move — provider
neutral.

A posted customer invoice/refund for a Peppol-enabled customer is exported to
BIS3 UBL by Odoo's own ``account.edi.xml.ubl_bis3`` builder, wrapped in an
``edi.message`` (``doc_family='peppol'``) and dispatched through whichever
transport provider is installed. The transport is delegated to two hooks a
provider module implements: ``_peppol_provider`` (the provider key stamped on
the message) and ``_peppol_send`` (enqueue via that provider's connector).
"""

import logging
import uuid
from xml.sax.saxutils import escape as xml_escape

from markupsafe import Markup, escape

from odoo import _, api, fields, models
from odoo.exceptions import UserError

from .edi_message import (
    CAC_NS,
    CBC_NS,
    CUSTOMIZATION_INVOICE_RESPONSE,
    UBL_APPRESPONSE_NS,
)

_logger = logging.getLogger(__name__)

PROFILE_INVOICE_RESPONSE = "urn:fdc:peppol.eu:poacc:bis:invoice_response:3"

# Escape entities covering BOTH text and attribute contexts: xml.sax.saxutils
# escapes & < > but NOT quotes, so attribute values (schemeID / listID) also
# need the quote characters escaped.
_XML_ESCAPE_ENTITIES = {'"': "&quot;", "'": "&apos;"}


def _xe(value):
    """XML-escape a value for text OR attribute context (& < > and quotes).
    ``None`` becomes an empty string."""
    return xml_escape(value or "", _XML_ESCAPE_ENTITIES)

# Peppol Invoice Response status codes (UNCL4343 T111 subset), aligned with
# Odoo core's account.peppol.response for cross-implementation interop.
PEPPOL_RESPONSE_CODES = [
    ("AB", "Acknowledged"),
    ("IP", "In process"),
    ("UQ", "Under query"),
    ("CA", "Conditionally accepted"),
    ("AP", "Accepted"),
    ("RE", "Rejected"),
    ("PD", "Paid"),
]


class AccountMove(models.Model):
    _inherit = "account.move"

    peppol_message_ids = fields.One2many(
        "edi.message",
        "peppol_move_id",
        string="Peppol EDI Messages",
    )
    peppol_active = fields.Boolean(
        compute="_compute_peppol_active",
        help="True when this posted customer invoice/refund can be sent as a "
        "Peppol BIS3 document (a transport provider is installed and both "
        "parties have a Peppol address).",
    )
    peppol_status = fields.Char(
        compute="_compute_peppol_status",
        string="Peppol Status",
        help="State of the most recent outbound Peppol message for this "
        "document.",
    )
    peppol_response = fields.Char(
        string="Peppol Delivery Response",
        copy=False,
        readonly=True,
        help="Latest Peppol Message Level Response (MLR) received for this "
        "document — the delivery/acceptance code and description returned by "
        "the network (e.g. 'AB — Acknowledged').",
    )
    peppol_ir_status = fields.Selection(
        PEPPOL_RESPONSE_CODES,
        string="Peppol Invoice Response",
        copy=False,
        readonly=True,
        help="Latest business-level Peppol Invoice Response received from the "
        "buyer for a customer invoice we sent (accepted / rejected / under "
        "query / …).",
    )
    peppol_ir_reason = fields.Char(
        string="Peppol Response Reason",
        copy=False,
        readonly=True,
        help="Clarification the buyer gave with the Invoice Response — the "
        "reason for a rejection/query/conditional acceptance.",
    )
    peppol_ir_sent_status = fields.Selection(
        PEPPOL_RESPONSE_CODES,
        string="Peppol Response Sent",
        copy=False,
        readonly=True,
        help="The last business-level Peppol Invoice Response WE sent to the "
        "supplier for this received vendor bill (accepted / rejected / "
        "disputed).",
    )
    peppol_ir_can_respond = fields.Boolean(
        compute="_compute_peppol_ir_can_respond",
        help="True when this vendor bill arrived via Peppol and we can send a "
        "business Invoice Response (accept/reject/dispute) back to the "
        "supplier.",
    )

    @api.depends(
        "move_type",
        "peppol_message_ids.direction",
        "peppol_message_ids.message_type",
        "partner_id.commercial_partner_id.peppol_eas",
        "partner_id.commercial_partner_id.peppol_endpoint",
        "company_id.partner_id.peppol_eas",
        "company_id.partner_id.peppol_endpoint",
    )
    def _compute_peppol_ir_can_respond(self):
        for move in self:
            move.peppol_ir_can_respond = move._peppol_ir_can_respond()

    # ------------------------------------------------------------------
    # Transport provider hooks (implemented by the provider module)
    # ------------------------------------------------------------------

    def _peppol_provider(self):
        """Return the transport provider key to stamp on outbound Peppol
        ``edi.message`` records. The neutral base returns ``False`` (no
        transport installed); a provider module (``edi_editel_peppol`` /
        ``edi_grit_peppol``) overrides to return e.g. ``'editel'``."""
        return False

    def _peppol_send(self, msg):
        """Dispatch an outbound Peppol ``edi.message`` via the active
        provider's connector. The neutral base raises; a provider module
        overrides (e.g. ``msg._enqueue_send(self.env['editel.connector'])``)."""
        self.ensure_one()
        raise UserError(
            _(
                "No Peppol transport provider is installed to send %s. Install "
                "a provider module such as edi_editel_peppol.",
                self.display_name,
            )
        )

    # ------------------------------------------------------------------
    # Eligibility
    # ------------------------------------------------------------------

    @staticmethod
    def _peppol_partner_addressable(partner):
        p = partner.commercial_partner_id
        return bool(p.peppol_eas and p.peppol_endpoint)

    def _peppol_is_eligible(self):
        """True if this move is a posted customer document, a transport
        provider is installed, and both the company and the customer carry a
        Peppol address (EAS + endpoint)."""
        self.ensure_one()
        if self.move_type not in ("out_invoice", "out_refund"):
            return False
        if self.state != "posted":
            return False
        if not self._peppol_provider():
            return False
        if not self._peppol_partner_addressable(self.partner_id):
            return False
        if not self._peppol_partner_addressable(self.company_id.partner_id):
            return False
        return True

    @api.depends(
        "move_type",
        "state",
        "partner_id.commercial_partner_id.peppol_eas",
        "partner_id.commercial_partner_id.peppol_endpoint",
        "company_id.partner_id.peppol_eas",
        "company_id.partner_id.peppol_endpoint",
    )
    def _compute_peppol_active(self):
        for move in self:
            move.peppol_active = move._peppol_is_eligible()

    @api.depends("peppol_message_ids.state", "peppol_message_ids.direction")
    def _compute_peppol_status(self):
        # Read the linked EDI messages as sudo: simply *viewing* a customer
        # invoice must not require edi.message access (EDI User/Manager). A
        # normal accounting user sees the derived Peppol status badge; the
        # "Send via Peppol" action stays gated to the EDI groups on the button.
        for move in self:
            outbound = move.sudo().peppol_message_ids.filtered(
                lambda m: m.direction == "out"
            ).sorted("create_date")
            move.peppol_status = (
                dict(self.env["edi.message"]._fields["state"].selection).get(
                    outbound[-1].state
                )
                if outbound
                else False
            )

    # ------------------------------------------------------------------
    # UBL generation
    # ------------------------------------------------------------------

    def _peppol_builder(self):
        """Return the UBL builder to export this move with.

        Not hard-wired to ``account.edi.xml.ubl_bis3``: several jurisdictions
        ship a BIS3 subclass that the plain builder would silently drop. The
        Slovak one (``account.edi.xml.ubl_sk`` from ``l10n_sk_ubl_bis3``) maps
        the *variabilný symbol* onto ``cbc:PaymentID`` (BT-83), which is what
        the receiving bank reconciles on — exporting via the generic builder
        would put the invoice on the network without it.

        Resolution goes through the partner's configured format, but is
        constrained to formats core marks ``on_peppol``: a partner set to e.g.
        Factur-X must not have that document handed to a Peppol transport.
        """
        self.ensure_one()
        partner = self.partner_id.commercial_partner_id
        edi_format = partner._get_peppol_edi_format()
        if edi_format not in partner._get_peppol_formats():
            edi_format = partner._get_suggested_peppol_edi_format()
        builder = partner._get_edi_builder(edi_format)
        # Test for None, NOT truthiness: a builder is an AbstractModel, whose
        # recordset is empty and therefore FALSY. An `or` fallback here looks
        # right and silently discards every national builder — which is
        # exactly how the Slovak BT-83 mapping went missing in the first
        # place. Core returns None (not an empty recordset) for a format it
        # does not know, so None is the real "no builder" signal.
        if builder is None:
            builder = self.env["account.edi.xml.ubl_bis3"]
        return builder

    def _peppol_generate_ubl(self):
        """Return (xml_bytes, filename) for this move's BIS3 UBL. Raises
        UserError with the collected EN16931/Peppol constraint messages when
        the builder reports any."""
        self.ensure_one()
        builder = self._peppol_builder()
        xml_bytes, errors = builder._export_invoice(self)
        if errors:
            raise UserError(
                _(
                    "Cannot generate the Peppol BIS3 document for %(name)s:\n"
                    "%(errors)s",
                    name=self.name,
                    errors="\n".join("- %s" % e for e in errors),
                )
            )
        filename = builder._export_invoice_filename(self)
        return xml_bytes, filename

    # ------------------------------------------------------------------
    # Emit
    # ------------------------------------------------------------------

    def _peppol_emit(self, queue_send=True, raise_on_error=True):
        """Generate the BIS3 UBL and create the outbound edi.message in
        state='ready'. When ``queue_send``, also dispatch it via the provider
        transport hook; otherwise leave it for manual send.

        Generation failures propagate when ``raise_on_error`` (default);
        auto-trigger callers pass False to log + continue across a batch.
        """
        self.ensure_one()
        # Re-send reuses the single outbound message for this move (the Peppol
        # message_id is the stable UBL cbc:ID, so a fresh create() would hit
        # the (message_id, direction) uniqueness constraint). Guard against
        # clobbering an in-flight send (double-click / concurrent auto-post):
        # if the existing message is already queued or sent, don't touch it.
        msg = self.peppol_message_ids.filtered(
            lambda m: m.direction == "out"
        )[:1]
        if msg and msg.state in ("queued", "sent"):
            if raise_on_error:
                raise UserError(
                    _(
                        "A Peppol document for %(name)s is already being sent "
                        "(status: %(state)s). Manage it from the linked EDI "
                        "message before re-sending.",
                        name=self.name,
                        state=msg.state,
                    )
                )
            return msg

        try:
            xml_bytes, filename = self._peppol_generate_ubl()
        except Exception:
            if raise_on_error:
                raise
            _logger.exception(
                "Error generating Peppol BIS3 for invoice %s", self.name
            )
            return False

        doc_kind = "CreditNote" if self.move_type == "out_refund" else "Invoice"
        xml_str = (
            xml_bytes.decode("utf-8")
            if isinstance(xml_bytes, bytes)
            else xml_bytes
        )
        if msg:
            msg.write(
                {
                    "name": filename,
                    "state": "ready",
                    "error_message": False,
                    "blocking_level": False,
                }
            )
        else:
            msg = self.env["edi.message"].create(
                {
                    "name": filename,
                    "direction": "out",
                    "provider": self._peppol_provider(),
                    "doc_family": "peppol",
                    "state": "ready",
                    "external_id": self.name,
                    "peppol_move_id": self.id,
                    "company_id": self.company_id.id,
                }
            )
        # Store the raw UBL — NO biztalk envelope (Peppol routing is inside
        # the document). message_type/message_id/etc. are computed from it.
        msg._store_xml(xml_str, filename=filename)
        if queue_send:
            self._peppol_send(msg)

        link = Markup(
            '<a href="#" data-oe-model="edi.message" data-oe-id="%d">%s</a>'
        ) % (msg.id, escape(msg.name))
        self.message_post(
            body=Markup(
                _("%(kind)s sent via Peppol: %(link)s (%(state)s).")
            )
            % {
                "kind": doc_kind,
                "link": link,
                "state": _("queued") if queue_send else _("awaiting manual send"),
            },
        )
        return msg

    # ------------------------------------------------------------------
    # Auto-send resolution + hooks
    # ------------------------------------------------------------------

    def _peppol_auto_send(self):
        """Global opt-in flag (Settings > EDI). Off by default so the manual
        button is the default flow; a deployment can flip it on to send every
        eligible customer document automatically on post."""
        param = (
            self.env["ir.config_parameter"]
            .sudo()
            .get_param("peppol.auto_send", "False")
        )
        return param.lower() not in ("0", "false", "")

    def action_post(self):
        res = super().action_post()
        for move in self.filtered(lambda m: m._peppol_is_eligible()):
            if move._peppol_auto_send():
                move._peppol_emit(queue_send=True, raise_on_error=False)
        return res

    def action_peppol_send(self):
        """Manual button: emit + queue a Peppol BIS3 document for a posted
        customer invoice/refund."""
        for move in self:
            if not move._peppol_is_eligible():
                raise UserError(
                    _(
                        "%s is not eligible for Peppol sending: it must be a "
                        "posted customer invoice/credit note, a Peppol "
                        "transport provider must be installed, and both your "
                        "company and the customer must have a Peppol address "
                        "(EAS + endpoint) configured.",
                        move.display_name,
                    )
                )
            move._peppol_emit(queue_send=True)

    # ------------------------------------------------------------------
    # Outbound business Invoice Response (buyer accepts/rejects/disputes a
    # received vendor bill)
    # ------------------------------------------------------------------

    def _peppol_source_invoice_message(self):
        """The inbound Peppol Invoice/CreditNote ``edi.message`` this vendor
        bill was created from (carries the supplier's endpoint + invoice id)."""
        self.ensure_one()
        return self.peppol_message_ids.filtered(
            lambda m: m.direction == "in"
            and m.message_type in ("Invoice", "CreditNote")
        )[:1]

    def _peppol_ir_can_respond(self):
        """True if this is a vendor bill received via Peppol for which we can
        send an Invoice Response back to the supplier."""
        self.ensure_one()
        if self.move_type not in ("in_invoice", "in_refund"):
            return False
        if not self._peppol_provider():
            return False
        if not self._peppol_source_invoice_message():
            return False
        if not self._peppol_partner_addressable(self.partner_id):
            return False
        if not self._peppol_partner_addressable(self.company_id.partner_id):
            return False
        return True

    def _peppol_build_invoice_response(self, code, reason_clarifications=None,
                                       note=None):
        """Build the UBL ApplicationResponse (Peppol Invoice Response,
        invoice_response:3) for this vendor bill. Returns (xml_str, response_id).

        We are the buyer: SenderParty = our company, ReceiverParty = the
        supplier; DocumentReference/ID = the supplier's invoice number.
        """
        self.ensure_one()
        company = self.company_id
        buyer = company.partner_id.commercial_partner_id
        seller = self.partner_id.commercial_partner_id
        src = self._peppol_source_invoice_message()

        invoice_id = (
            (src.message_id if src else False)
            or self.ref
            or self.payment_reference
            or self.name
            or ""
        )
        supplier_endpoint = (
            (src.sender_gln if src else False) or seller.peppol_endpoint or ""
        )
        supplier_eas = seller.peppol_eas or "0245"
        buyer_endpoint = buyer.peppol_endpoint or ""
        buyer_eas = buyer.peppol_eas or "0245"
        doc_type_code = "381" if self.move_type == "in_refund" else "380"
        response_id = str(uuid.uuid4())
        issue_date = fields.Date.to_string(fields.Date.context_today(self))

        status_blocks = ""
        for cl in (reason_clarifications or self.env["edi.peppol.clarification"]):
            status_blocks += (
                "<cac:Status>"
                '<cbc:StatusReasonCode listID="%s">%s</cbc:StatusReasonCode>'
                "<cbc:StatusReason>%s</cbc:StatusReason>"
                "</cac:Status>"
            ) % (
                _xe(cl.list_identifier or "OPStatusReason"),
                _xe(cl.code),
                _xe(cl.name),
            )
        if note:
            status_blocks += (
                "<cac:Status><cbc:StatusReason>%s</cbc:StatusReason></cac:Status>"
                % _xe(note)
            )

        xml = (
            '<?xml version="1.0" encoding="UTF-8"?>'
            '<ApplicationResponse xmlns="%(ns)s" xmlns:cac="%(cac)s" '
            'xmlns:cbc="%(cbc)s">'
            "<cbc:CustomizationID>%(cust)s</cbc:CustomizationID>"
            "<cbc:ProfileID>%(prof)s</cbc:ProfileID>"
            "<cbc:ID>%(rid)s</cbc:ID>"
            "<cbc:IssueDate>%(date)s</cbc:IssueDate>"
            "<cac:SenderParty>"
            '<cbc:EndpointID schemeID="%(beas)s">%(bend)s</cbc:EndpointID>'
            "</cac:SenderParty>"
            "<cac:ReceiverParty>"
            '<cbc:EndpointID schemeID="%(seas)s">%(send)s</cbc:EndpointID>'
            "</cac:ReceiverParty>"
            "<cac:DocumentResponse>"
            "<cac:Response><cbc:ResponseCode>%(code)s</cbc:ResponseCode>"
            "%(status)s</cac:Response>"
            "<cac:DocumentReference><cbc:ID>%(inv)s</cbc:ID>"
            "<cbc:DocumentTypeCode>%(dtc)s</cbc:DocumentTypeCode>"
            "</cac:DocumentReference>"
            "</cac:DocumentResponse>"
            "</ApplicationResponse>"
        ) % {
            "ns": UBL_APPRESPONSE_NS,
            "cac": CAC_NS,
            "cbc": CBC_NS,
            "cust": CUSTOMIZATION_INVOICE_RESPONSE,
            "prof": PROFILE_INVOICE_RESPONSE,
            "rid": response_id,
            "date": issue_date,
            "beas": _xe(buyer_eas),
            "bend": _xe(buyer_endpoint),
            "seas": _xe(supplier_eas),
            "send": _xe(supplier_endpoint),
            "code": _xe(code),
            "status": status_blocks,
            "inv": _xe(invoice_id),
            "dtc": doc_type_code,
        }
        return xml, response_id

    def _peppol_emit_invoice_response(self, code, reason_clarifications=None,
                                      note=None, queue_send=True):
        """Generate a Peppol Invoice Response for this vendor bill and dispatch
        it back to the supplier via the transport provider."""
        self.ensure_one()
        if not self._peppol_ir_can_respond():
            raise UserError(
                _(
                    "%s cannot be responded to via Peppol: it must be a vendor "
                    "bill received over Peppol, with both parties Peppol-"
                    "addressable and a transport provider installed.",
                    self.display_name,
                )
            )
        # Peppol requires a clarification when rejecting / querying /
        # conditionally accepting — enforce it here too (not only in the
        # wizard) so direct API calls can't emit a schematron-invalid response.
        if code in ("RE", "UQ", "CA") and not (reason_clarifications or note):
            raise UserError(
                _(
                    "A reason (coded clarification or free text) is required "
                    "when the Invoice Response is Rejected, Under query or "
                    "Conditionally accepted."
                )
            )
        xml, response_id = self._peppol_build_invoice_response(
            code, reason_clarifications, note
        )
        filename = "invoice_response_%s.xml" % response_id
        msg = self.env["edi.message"].create(
            {
                "name": filename,
                "direction": "out",
                "provider": self._peppol_provider(),
                "doc_family": "peppol",
                "state": "ready",
                "external_id": self.ref or self.name,
                "peppol_move_id": self.id,
                "company_id": self.company_id.id,
            }
        )
        msg._store_xml(xml, filename=filename)
        if queue_send:
            self._peppol_send(msg)

        self.peppol_ir_sent_status = code
        label = dict(self._fields["peppol_ir_sent_status"].selection).get(
            code, code
        )
        link = Markup(
            '<a href="#" data-oe-model="edi.message" data-oe-id="%d">%s</a>'
        ) % (msg.id, escape(msg.name))
        self.message_post(
            body=Markup(
                _(
                    "Peppol Invoice Response sent: <strong>%(label)s</strong> "
                    "(%(code)s) — %(link)s."
                )
            )
            % {"label": label or "", "code": code, "link": link},
        )
        return msg

    def action_peppol_invoice_response(self):
        """Open the wizard to send a Peppol Invoice Response for this vendor
        bill."""
        self.ensure_one()
        return {
            "type": "ir.actions.act_window",
            "name": _("Peppol Invoice Response"),
            "res_model": "edi.peppol.invoice.response.wizard",
            "view_mode": "form",
            "target": "new",
            "context": {"default_move_id": self.id},
        }
