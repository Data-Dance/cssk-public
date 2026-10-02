"""Peppol BIS 3.0 document family on ``edi.message`` — provider neutral.

Peppol invoices/credit notes carry a plain UBL 2.1 payload with no biztalk
envelope; routing lives inside the UBL itself (``cbc:EndpointID`` on the
supplier and customer party blocks). The raw BIS3 XML is what we send and
receive, over *whatever* transport provider is installed (Editel eXite, GRiT
Orion, …) — this module is transport-agnostic.

It registers the ``peppol`` document family and teaches ``edi.message`` to:
  * classify an inbound payload as UBL vs biztalk (by root element);
  * parse routing/identity fields out of the UBL for display + dedup;
  * turn an inbound UBL Invoice/CreditNote into a draft vendor bill using
    Odoo's own (proxy-independent) UBL decoder;
  * record an inbound ApplicationResponse (MLR) against the sent document.

Outbound generation + the send action live in ``account_move.py``; the actual
transport dispatch is delegated to a provider hook there.
"""

import logging
from xml.etree import ElementTree

from markupsafe import Markup

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# UBL 2.1 namespaces (BIS3 Invoice + CreditNote + Peppol MLR).
UBL_INVOICE_NS = "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
UBL_CREDITNOTE_NS = "urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2"
UBL_APPRESPONSE_NS = (
    "urn:oasis:names:specification:ubl:schema:xsd:ApplicationResponse-2"
)
CBC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2"
CAC_NS = "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"

# A UBL ApplicationResponse is one of two Peppol business responses, told
# apart by CustomizationID:
#   * MLR (Message Level Response, T71) — technical: received/rejected;
#   * Invoice Response (T111) — business: accept/reject/dispute in the
#     buyer's approval-and-payment process.
CUSTOMIZATION_MLR = "urn:fdc:peppol.eu:poacc:trns:mlr:3"
CUSTOMIZATION_INVOICE_RESPONSE = "urn:fdc:peppol.eu:poacc:trns:invoice_response:3"

# Root local name → our coarse UBL kind, used only for UBL detection / dedup.
# The finer message_type ("MLR" / "InvoiceResponse") is resolved from the
# CustomizationID in ``_peppol_parse_envelope``.
_UBL_ROOTS = {
    f"{{{UBL_INVOICE_NS}}}Invoice": "Invoice",
    f"{{{UBL_CREDITNOTE_NS}}}CreditNote": "CreditNote",
    f"{{{UBL_APPRESPONSE_NS}}}ApplicationResponse": "ApplicationResponse",
}


class EdiMessage(models.Model):
    _inherit = "edi.message"

    # A single generic link to the account.move this message carries — the
    # outbound customer invoice/refund we sent, or the inbound vendor bill we
    # created. Kept separate from the edi_base_sale/purchase link fields so
    # this module stays independent of the EDIFACT sale/purchase stack.
    peppol_move_id = fields.Many2one(
        "account.move",
        string="Peppol Document",
        copy=False,
        index=True,
        help="The customer invoice/refund this Peppol message was generated "
        "from (outbound), or the vendor bill created from it (inbound).",
    )

    # ------------------------------------------------------------------
    # Document-family registration
    # ------------------------------------------------------------------

    @api.model
    def _selection_doc_family(self):
        return super()._selection_doc_family() + [("peppol", "Peppol BIS3")]

    # ------------------------------------------------------------------
    # UBL payload detection helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _peppol_fromstring(xml_content):
        """Safely parse an (untrusted) inbound payload into an ElementTree
        root, or return None.

        BIS3 UBL never carries a DTD, so we refuse any payload with a
        DOCTYPE/ENTITY declaration in its prolog — this defuses the
        entity-expansion ("billion laughs") DoS class that stdlib
        ElementTree/expat is otherwise vulnerable to on hostile inbound XML.
        A DTD must precede the root element, so scanning the head suffices.
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
                "Refusing UBL payload containing a DTD/entity declaration"
            )
            return None
        try:
            return ElementTree.fromstring(raw)
        except ElementTree.ParseError:
            return None

    @classmethod
    def _peppol_root_localname(cls, xml_content):
        """Return 'Invoice'/'CreditNote'/'ApplicationResponse' if the payload
        is a UBL BIS3 document, else None."""
        root = cls._peppol_fromstring(xml_content)
        return _UBL_ROOTS.get(root.tag) if root is not None else None

    def _is_peppol(self):
        """True if this message belongs to the Peppol family. Prefers the
        stored ``doc_family`` and falls back to sniffing the payload (covers
        records whose family wasn't stamped, e.g. legacy rows)."""
        self.ensure_one()
        if self.doc_family == "peppol":
            return True
        if self.doc_family and self.doc_family != "peppol":
            return False
        return self._peppol_root_localname(self._get_xml_content()) is not None

    def _peppol_parse_envelope(self, xml_content):
        """Extract identity/routing fields from a UBL BIS3 payload.

        Returns a dict with: doc_kind ('Invoice'/'CreditNote'/
        'ApplicationResponse'), message_id (cbc:ID), issue_date
        (cbc:IssueDate str), supplier_endpoint (document "from"),
        customer_endpoint (document "to"). For an ApplicationResponse (MLR)
        the dict also carries response_code, response_desc and referenced_id
        (the cbc:ID of the document being acknowledged). Missing pieces come
        back as ''."""
        root = self._peppol_fromstring(xml_content)
        if root is None:
            return {}
        doc_kind = _UBL_ROOTS.get(root.tag)
        if not doc_kind:
            return {}

        def _text(el):
            return (el.text or "").strip() if el is not None else ""

        cbc_id = root.find(f"{{{CBC_NS}}}ID")
        issue_date = root.find(f"{{{CBC_NS}}}IssueDate")

        if doc_kind == "ApplicationResponse":
            # Both MLR and Invoice Response share this shape: parties are
            # cac:SenderParty / cac:ReceiverParty, and the body is
            # cac:DocumentResponse (response code + referenced doc). Resolve
            # the finer kind from the CustomizationID.
            cust = _text(root.find(f"{{{CBC_NS}}}CustomizationID"))
            if CUSTOMIZATION_INVOICE_RESPONSE in cust:
                doc_kind = "InvoiceResponse"
            else:
                doc_kind = "MLR"
            supplier_ep = root.find(
                f"{{{CAC_NS}}}SenderParty/{{{CBC_NS}}}EndpointID"
            )
            customer_ep = root.find(
                f"{{{CAC_NS}}}ReceiverParty/{{{CBC_NS}}}EndpointID"
            )
            response = (
                f"{{{CAC_NS}}}DocumentResponse/{{{CAC_NS}}}Response/"
            )
            resp_code = root.find(f"{response}{{{CBC_NS}}}ResponseCode")
            resp_desc = root.find(f"{response}{{{CBC_NS}}}Description")
            status_reason_code = root.find(
                f"{response}{{{CAC_NS}}}Status/{{{CBC_NS}}}StatusReasonCode"
            )
            status_reason = root.find(
                f"{response}{{{CAC_NS}}}Status/{{{CBC_NS}}}StatusReason"
            )
            ref_id = root.find(
                f"{{{CAC_NS}}}DocumentResponse/{{{CAC_NS}}}DocumentReference/"
                f"{{{CBC_NS}}}ID"
            )
            return {
                "doc_kind": doc_kind,
                "customization": cust,
                "message_id": _text(cbc_id),
                "issue_date": _text(issue_date),
                "supplier_endpoint": _text(supplier_ep),
                "customer_endpoint": _text(customer_ep),
                "response_code": _text(resp_code),
                "response_desc": _text(resp_desc),
                "status_reason_code": _text(status_reason_code),
                "status_reason": _text(status_reason),
                "referenced_id": _text(ref_id),
            }

        supplier_ep = root.find(
            f"{{{CAC_NS}}}AccountingSupplierParty/{{{CAC_NS}}}Party/"
            f"{{{CBC_NS}}}EndpointID"
        )
        customer_ep = root.find(
            f"{{{CAC_NS}}}AccountingCustomerParty/{{{CAC_NS}}}Party/"
            f"{{{CBC_NS}}}EndpointID"
        )
        return {
            "doc_kind": doc_kind,
            "message_id": _text(cbc_id),
            "issue_date": _text(issue_date),
            "supplier_endpoint": _text(supplier_ep),
            "customer_endpoint": _text(customer_ep),
        }

    # ------------------------------------------------------------------
    # Envelope field computation (UBL variant)
    # ------------------------------------------------------------------

    def _compute_envelope_fields(self):
        # Split the recordset: biztalk records go through the base parser,
        # Peppol/UBL records are populated from the UBL structure instead
        # (the biztalk parser would return garbage on UBL).
        peppol = self.filtered(lambda r: r._is_peppol())
        super(EdiMessage, self - peppol)._compute_envelope_fields()
        for rec in peppol:
            parsed = rec._peppol_parse_envelope(rec._get_xml_content())
            if not parsed:
                rec.message_type = False
                rec.message_id = False
                rec.message_date = False
                rec.doc_type_code = False
                rec.sender_gln = False
                rec.receiver_gln = False
                continue
            rec.message_type = parsed["doc_kind"]
            rec.message_id = parsed["message_id"] or False
            # Keep doc_type_code empty for Peppol so _get_effective_type does
            # not resolve to an EDIFACT type (e.g. 380=INVOIC) and misroute
            # the message into the biztalk dispatchers.
            rec.doc_type_code = False
            # Supplier = document "from", customer = document "to".
            rec.sender_gln = parsed["supplier_endpoint"] or False
            rec.receiver_gln = parsed["customer_endpoint"] or False
            rec.message_date = self._peppol_issue_datetime(parsed["issue_date"])
            # Link the counterparty by Peppol endpoint: inbound → supplier
            # (the vendor), outbound → customer.
            endpoint = (
                parsed["supplier_endpoint"]
                if rec.direction == "in"
                else parsed["customer_endpoint"]
            )
            rec.partner_id = rec._peppol_find_partner(endpoint).id or False

    @staticmethod
    def _peppol_issue_datetime(issue_date):
        """Convert a UBL cbc:IssueDate (YYYY-MM-DD) into a Datetime at
        midnight, or False."""
        if not issue_date:
            return False
        try:
            import datetime

            d = datetime.date.fromisoformat(issue_date[:10])
            return datetime.datetime.combine(d, datetime.time())
        except ValueError:
            return False

    def _peppol_find_partner(self, endpoint):
        """Resolve a res.partner from a Peppol EndpointID value. Matches on
        the stored ``peppol_endpoint`` (schemeID-agnostic). Returns an empty
        recordset when unresolved."""
        Partner = self.env["res.partner"]
        if not endpoint:
            return Partner
        return Partner.search(
            [("peppol_endpoint", "=", endpoint)], limit=1
        )

    # ------------------------------------------------------------------
    # Inbound polling seams (overrides of edi_base defaults)
    # ------------------------------------------------------------------

    def _dedup_key_for_inbound(self, connector, xml_content):
        # UBL payloads have no biztalk envelope; dedup on the UBL cbc:ID.
        if self._peppol_root_localname(xml_content) is not None:
            parsed = self._peppol_parse_envelope(xml_content)
            return parsed.get("message_id", "")
        return super()._dedup_key_for_inbound(connector, xml_content)

    def _inbound_stub_vals(self, provider, xml_content, pkg):
        vals = super()._inbound_stub_vals(provider, xml_content, pkg)
        if self._peppol_root_localname(xml_content) is not None:
            vals["doc_family"] = "peppol"
        return vals

    def _inbound_dispatch_may_commit(self):
        # Peppol inbound builds a vendor bill through Odoo's core UBL importer,
        # which commits the cursor mid-decode
        # (account_document_import_mixin.rollbackable_transaction). The poll
        # must therefore not wrap our dispatch in a savepoint.
        self.ensure_one()
        if self.doc_family == "peppol":
            return True
        return super()._inbound_dispatch_may_commit()

    # ------------------------------------------------------------------
    # Inbound dispatch — provider-agnostic, keyed on doc_family='peppol':
    #   UBL Invoice/CreditNote  → draft vendor bill
    #   ApplicationResponse     → business response on the sent document
    # ------------------------------------------------------------------

    def _lookup_related_records(self):
        super()._lookup_related_records()
        for rec in self:
            if (
                rec.direction != "in"
                or rec.state == "done"
                or rec.doc_family != "peppol"
            ):
                continue
            try:
                if rec.message_type in ("MLR", "InvoiceResponse", "ApplicationResponse"):
                    rec._peppol_process_application_response()
                else:
                    bill = rec._peppol_create_vendor_bill()
                    if bill:
                        rec.peppol_move_id = bill.id
                rec.state = "done"
            except Exception as exc:  # noqa: BLE001 - surface on the message
                _logger.exception(
                    "Error processing inbound Peppol edi.message id=%s",
                    rec.id,
                )
                rec.state = "error"
                rec.error_message = str(exc)

    # ------------------------------------------------------------------
    # Inbound ApplicationResponse (MLR today; Invoice Response later)
    # ------------------------------------------------------------------

    def _peppol_process_application_response(self):
        """Route an inbound UBL ApplicationResponse to the MLR (technical
        delivery) or Invoice Response (business accept/reject/dispute) handler,
        by its resolved ``message_type``."""
        self.ensure_one()
        if self.message_type == "InvoiceResponse":
            self._peppol_process_invoice_response()
        else:
            self._peppol_process_mlr()

    def _peppol_referenced_out_move(self, parsed):
        """Resolve the outbound customer invoice/refund an ApplicationResponse
        refers to, by ``DocumentReference/ID`` == move name."""
        self.ensure_one()
        ref = parsed.get("referenced_id")
        Move = self.env["account.move"]
        if not ref:
            return Move
        return Move.search(
            [
                ("name", "=", ref),
                ("move_type", "in", ("out_invoice", "out_refund")),
                *Move._check_company_domain(self.company_id or self.env.company),
            ],
            limit=1,
        )

    def _peppol_process_invoice_response(self):
        """Handle an inbound Peppol **Invoice Response** (business-level
        accept/reject/dispute): match it to the outbound invoice it responds
        to, record the status + reason on that move (``peppol_ir_status`` /
        ``peppol_ir_reason`` + chatter) and link this message to it."""
        self.ensure_one()
        parsed = self._peppol_parse_envelope(self._get_xml_content())
        code = parsed.get("response_code") or ""
        reason = parsed.get("status_reason") or parsed.get("response_desc") or ""
        reason_code = parsed.get("status_reason_code") or ""
        sender = parsed.get("supplier_endpoint") or ""

        move = self._peppol_referenced_out_move(parsed)
        if not move:
            _logger.info(
                "Peppol Invoice Response id=%s references unknown document %r "
                "(code=%s)",
                self.id,
                parsed.get("referenced_id"),
                code,
            )
            return

        self.peppol_move_id = move.id
        move.peppol_ir_status = code or False
        reason_txt = (
            "%s — %s" % (reason_code, reason)
            if reason_code and reason
            else (reason or reason_code)
        )
        move.peppol_ir_reason = reason_txt or False
        label = dict(
            move._fields["peppol_ir_status"].selection
        ).get(code, code)
        move.message_post(
            body=Markup(
                _(
                    "Peppol Invoice Response received: "
                    "<strong>%(label)s</strong> (%(code)s) %(reason)s "
                    "— from %(sender)s."
                )
            )
            % {
                "label": label or "",
                "code": code,
                "reason": reason_txt or "",
                "sender": sender,
            },
        )

    def _peppol_process_mlr(self):
        """Handle an inbound Peppol MLR (ApplicationResponse): match it to the
        outbound document it acknowledges (by ``DocumentReference/ID`` = the
        move name), record the response code/description on that move (chatter
        + ``peppol_response``) and link this message to it.

        A response for a document we don't know (e.g. sent from another system)
        is not an error — we log it and leave the message linked to nothing.
        """
        self.ensure_one()
        parsed = self._peppol_parse_envelope(self._get_xml_content())
        ref = parsed.get("referenced_id")
        code = parsed.get("response_code") or ""
        desc = parsed.get("response_desc") or ""
        sender = parsed.get("supplier_endpoint") or ""

        move = self.env["account.move"]
        if ref:
            move = move.search(
                [
                    ("name", "=", ref),
                    ("move_type", "in", ("out_invoice", "out_refund")),
                    *move._check_company_domain(self.company_id or self.env.company),
                ],
                limit=1,
            )
        if not move:
            _logger.info(
                "Peppol MLR edi.message id=%s references unknown document %r "
                "(code=%s)",
                self.id,
                ref,
                code,
            )
            return

        self.peppol_move_id = move.id
        move.peppol_response = (
            "%s — %s" % (code, desc) if desc else code
        ) or False
        move.message_post(
            body=Markup(
                _(
                    "Peppol delivery response received: "
                    "<strong>%(code)s</strong> %(desc)s (from %(sender)s)."
                )
            )
            % {"code": code, "desc": desc, "sender": sender},
        )

    def _peppol_purchase_journal(self, company):
        """Return the purchase journal to book inbound Peppol bills into.

        Prefers the company's configured Peppol purchase journal, else the
        company's first purchase journal."""
        Journal = self.env["account.journal"]
        journal = company.sudo().peppol_purchase_journal_id
        if journal and journal.company_id == company:
            return journal
        return Journal.search(
            [
                *Journal._check_company_domain(company),
                ("type", "=", "purchase"),
            ],
            limit=1,
        )

    def _peppol_create_vendor_bill(self):
        """Create a *draft* vendor bill from this inbound UBL payload using
        Odoo's core UBL decoder. Credit notes become ``in_refund``
        automatically (the decoder derives the sign and, given a purchase
        journal, the in_ prefix). Left in draft for AP review — no autopost.
        """
        self.ensure_one()
        company = self.company_id or self.env.company
        journal = self._peppol_purchase_journal(company)
        if not journal:
            raise UserError(
                _(
                    "No purchase journal found for company %s to book the "
                    "inbound Peppol document.",
                    company.display_name,
                )
            )
        if not self.attachment_id:
            raise UserError(_("Inbound Peppol message has no XML attachment."))

        Move = self.env["account.move"].with_company(company)
        move = Move.create(
            {
                "move_type": "in_invoice",
                "journal_id": journal.id,
                "company_id": company.id,
            }
        )
        # extract_state / is_in_extractable_state are EE-only (OCR); guard.
        if "is_in_extractable_state" in move._fields:
            move.is_in_extractable_state = False

        file_data = Move._to_files_data(self.attachment_id)[0]
        move._extend_with_attachments([file_data], new=True)

        # Reparent the payload attachment onto the created bill so it shows
        # in the bill's attachments, mirroring account_peppol.
        self.attachment_id.write(
            {"res_model": "account.move", "res_id": move.id}
        )
        return move
