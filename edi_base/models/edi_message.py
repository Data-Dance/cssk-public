"""Concrete EDI message model shared by all providers.

Each provider module extends this model via _inherit to add its
provider-specific methods (APERAK processing, etc.) and registers
itself in PROVIDER_CONNECTOR_MAP and PROVIDER_CRON_MAP.
"""

import base64
import datetime
import logging
from xml.etree import ElementTree
from zoneinfo import ZoneInfo

from odoo import _, api, fields, models

from ..exceptions import RetryableJobError
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class EdiMessage(models.Model):
    _name = "edi.message"
    _inherit = ["mail.thread", "mail.activity.mixin"]
    _description = "EDI Message"
    _order = "create_date desc"
    _sql_constraints = [
        (
            "message_id_direction_unique",
            "UNIQUE(message_id, direction)",
            "An EDI message with this ID and direction already exists.",
        )
    ]

    # ------------------------------------------------------------------
    # Provider registry — extended by each provider module
    # ------------------------------------------------------------------

    PROVIDER_CONNECTOR_MAP = {}  # {"editel": "editel.connector", "grit": "grit.connector"}
    PROVIDER_CRON_MAP = {}       # {"editel": "edi_editel_base.cron_...", "grit": "edi_grit_base.cron_..."}

    #: How a provider's outbound messages leave ``queued``. ``"queue"`` means a
    #: job takes them, and needs ``edi_base_queue_job`` installed; ``"cron"``
    #: means :meth:`_cron_send_queued` does, and needs nothing.
    #:
    #: Declared per provider rather than inferred from what is installed,
    #: because on a database carrying both a guess would be a double send: the
    #: cron and the job would each pick up the same ``queued`` message. An
    #: unregistered provider defaults to ``"queue"``, which is what every
    #: provider did before this existed.
    PROVIDER_DISPATCH_MAP = {}   # {"epostak": "cron"}

    def _dispatch_mode(self):
        self.ensure_one()
        return self.PROVIDER_DISPATCH_MAP.get(self.provider, "queue")

    def _get_connector_name(self):
        """Return the connector model name for this message's provider."""
        self.ensure_one()
        name = self.PROVIDER_CONNECTOR_MAP.get(self.provider)
        if not name:
            _logger.warning("No connector registered for provider %s", self.provider)
        return name or "edi.connector.mixin"

    def _get_cron_xmlid(self):
        """Return the cron xmlid for this message's provider."""
        self.ensure_one()
        return self.PROVIDER_CRON_MAP.get(self.provider, "")

    # ------------------------------------------------------------------
    # Provider identification
    # ------------------------------------------------------------------

    provider = fields.Selection(
        selection="_selection_provider",
        string="Provider",
        required=True,
        index=True,
        default=lambda self: self._default_provider(),
    )
    provider_mode = fields.Char(
        string="Mode",
        copy=False,
        help="Raw test/production mode value stamped at create time. "
        "Meaning is provider-specific (e.g. 'test'/'production' for "
        "Editel, '1'/'0' for GRiT).",
    )

    @api.model
    def _selection_provider(self):
        """Return available providers. Extended by each provider module."""
        return []

    @api.model
    def _default_provider(self):
        """Override in concrete model to set provider automatically."""
        return False

    # ------------------------------------------------------------------
    # Document family — the document *standard* carried over the transport,
    # orthogonal to ``provider`` (= transport / clearing house). A single
    # provider mailbox can carry several families; e.g. Editel eXite carries
    # both EDIFACT (biztalk envelope) and Peppol BIS3 (UBL). Extended by each
    # document-family module via ``_selection_doc_family``.
    # ------------------------------------------------------------------

    doc_family = fields.Selection(
        selection="_selection_doc_family",
        string="Document Family",
        default="edifact",
        required=True,
        index=True,
        help="The document standard of this message (e.g. EDIFACT vs Peppol "
        "BIS3). Independent of the provider/transport used to carry it.",
    )

    @api.model
    def _selection_doc_family(self):
        """Return available document families. Extended by family modules."""
        return [("edifact", "EDIFACT")]

    is_test_mode = fields.Boolean(
        string="Test Mode",
        compute="_compute_is_test_mode",
        store=True,
        help="True if this message was created in test mode.",
    )

    @api.depends("provider", "provider_mode")
    def _compute_is_test_mode(self):
        for rec in self:
            if rec.provider == "editel":
                rec.is_test_mode = rec.provider_mode == "test"
            elif rec.provider == "grit":
                rec.is_test_mode = rec.provider_mode == "1"
            else:
                rec.is_test_mode = False

    # ------------------------------------------------------------------
    # Shared fields
    # ------------------------------------------------------------------

    name = fields.Char(string="Document Name")

    message_type = fields.Char(
        string="Message Type",
        compute="_compute_envelope_fields",
        store=True,
    )
    message_id = fields.Char(
        string="Message ID",
        compute="_compute_envelope_fields",
        store=True,
    )
    message_date = fields.Datetime(
        string="Message Date",
        compute="_compute_envelope_fields",
        store=True,
    )
    doc_type_code = fields.Char(
        string="Document Type Code",
        compute="_compute_envelope_fields",
        store=True,
        help="EDIFACT document type code from the message body (e.g. 220=ORDERS, "
        "231=ORDRSP, 351=DESADV, 380=INVOIC). More reliable than message_type "
        "for dispatch because some EDI providers rewrite the header message_type.",
    )
    sender_gln = fields.Char(
        string="Sender GLN",
        compute="_compute_envelope_fields",
        store=True,
    )
    receiver_gln = fields.Char(
        string="Receiver GLN",
        compute="_compute_envelope_fields",
        store=True,
    )

    direction = fields.Selection(
        [("in", "Inbound"), ("out", "Outbound")],
        string="Direction",
        required=True,
        index=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("ready", "Ready"),
            ("queued", "Queued"),
            ("sent", "Sent"),
            ("received", "Received"),
            ("error", "Error"),
            ("done", "Done"),
        ],
        string="State",
        default="draft",
        required=True,
        index=True,
    )

    message_xml = fields.Text(string="XML Content")
    attachment_id = fields.Many2one(
        "ir.attachment",
        string="XML Attachment",
        ondelete="set null",
    )
    error_message = fields.Text(string="Error Details")
    blocking_level = fields.Selection(
        [("info", "Info"), ("warning", "Warning"), ("error", "Error")],
        string="Blocking Level",
    )

    # The link from queue.job back to its edi.message is provided by the
    # ``edi_base_queue_job`` bridge module (queue.job.edi_message_id auto-
    # populated from the ``job_edi_message_id`` context passed by
    # _enqueue_send), along with the queue_job_ids One2many on this model
    # and the "Queue Jobs" / "Open EDI Message" navigation buttons.

    partner_id = fields.Many2one("res.partner", string="Partner")
    company_id = fields.Many2one(
        "res.company",
        default=lambda self: self.env.company,
        index=True,
    )

    # Provider correlation
    transmission_uuid = fields.Char(
        string="Transmission UUID",
        index=True,
        copy=False,
    )
    provider_interchange_id = fields.Char(
        string="Provider Interchange ID",
        index=True,
        copy=False,
    )
    external_id = fields.Char(
        string="External Reference",
        index=True,
        copy=False,
    )
    customer_ref = fields.Char(
        string="Customer / Vendor Reference",
        index=True,
        copy=False,
        help="The counterparty's reference number — the buyer's order "
        "number for sale-side messages, the vendor's order reference for "
        "purchase-side messages. Propagated from the originating "
        "sale_order.client_order_ref / purchase_order.partner_ref so a "
        "whole document conversation (ORDERS → ORDRSP → DESADV → INVOIC) "
        "can be searched by the same reference value.",
    )

    # ------------------------------------------------------------------
    # XML storage helpers
    # ------------------------------------------------------------------

    def _get_xml_content(self):
        """Return the XML payload as a string, preferring attachment_id.

        Defensive decoding: some senders mis-declare cp1250 (Windows-1250)
        bytes as ``encoding="UTF-8"``. Try strict UTF-8 first, then fall
        back to cp1250 so the parser can still extract structured fields
        instead of crashing on UnicodeDecodeError.
        """
        self.ensure_one()
        if self.attachment_id and self.attachment_id.datas:
            raw = base64.b64decode(self.attachment_id.datas)
            try:
                return raw.decode("utf-8")
            except UnicodeDecodeError:
                _logger.warning(
                    "edi.message %s: UTF-8 decode failed, falling back to cp1250",
                    self.id,
                )
                return raw.decode("cp1250", errors="replace")
        return self.message_xml or ""

    @staticmethod
    def _beautify_xml(xml_content):
        """Reformat XML with consistent indentation for storage / display.

        Used by ``_store_xml`` so both inbound and outbound payloads
        land in the database (and in the UI's chatter / form view) with
        readable indentation.

        Implementation notes:
          - Uses ``lxml`` with ``remove_blank_text=True`` so the parser
            discards the inconsistent inter-element whitespace from the
            QWeb template output, then ``pretty_print=True`` regenerates
            tidy two-space indentation.
          - Inter-element whitespace is the only thing changed —
            text-bearing leaf elements (e.g. ``<userdocid>302600324</userdocid>``)
            are left untouched, which is critical for XSD ``xsd:string``
            elements that default to ``whiteSpace="preserve"``. The
            beautified output still XSD-validates.
          - On any parse failure we fall back to the original bytes; the
            caller never sees an exception from this helper.
        """
        if not xml_content:
            return xml_content
        try:
            from lxml import etree
            parser = etree.XMLParser(remove_blank_text=True, huge_tree=True)
            data = (
                xml_content.encode("utf-8")
                if isinstance(xml_content, str)
                else xml_content
            )
            tree = etree.fromstring(data, parser)
            pretty = etree.tostring(
                tree,
                pretty_print=True,
                xml_declaration=True,
                encoding="UTF-8",
            )
            return pretty.decode("utf-8")
        except Exception:
            _logger.warning(
                "Failed to beautify XML for edi.message storage; "
                "storing raw payload instead.",
                exc_info=True,
            )
            return xml_content

    def _store_xml(self, xml_content, filename=None):
        """Persist XML as ir.attachment; keep message_xml for small payloads.

        Runs the payload through ``_beautify_xml`` first so the stored
        form is pretty-printed regardless of whether it came from
        outbound rendering (QWeb output has the template's literal
        whitespace) or inbound polling (provider envelopes vary).
        """
        self.ensure_one()
        if not xml_content:
            return
        xml_content = self._beautify_xml(xml_content)
        name = filename or self.name or f"edi_{self.id}.xml"
        data = (
            xml_content.encode("utf-8")
            if isinstance(xml_content, str)
            else xml_content
        )
        attachment = self.env["ir.attachment"].create(
            {
                "name": name,
                "datas": base64.b64encode(data),
                "res_model": self._name,
                "res_id": self.id,
                "mimetype": "application/xml",
            }
        )
        vals = {"attachment_id": attachment.id}
        if len(data) <= 1_000_000:
            vals["message_xml"] = data.decode("utf-8", errors="replace")
        self.write(vals)

    # ------------------------------------------------------------------
    # Envelope field computation
    # ------------------------------------------------------------------

    # doc_type → effective message type mapping (EDIFACT standard codes)
    DOC_TYPE_MAP = {
        "220": "ORDERS",
        "224": "ORDERS",   # urgent order
        "226": "ORDERS",   # commission
        "231": "ORDRSP",
        "305": "APERAK",   # application acknowledgment
        "351": "DESADV",
        "380": "INVOIC",
        "381": "INVOIC",   # credit note
        "481": "REMADV",   # remittance/payment advice
        "492": "ORDERS",   # CDC order
    }

    @api.depends("message_xml", "attachment_id")
    def _compute_envelope_fields(self):
        for rec in self:
            xml = rec._get_xml_content()
            if not xml:
                rec.message_type = False
                rec.message_id = False
                rec.message_date = False
                rec.doc_type_code = False
                rec.sender_gln = False
                rec.receiver_gln = False
                continue
            try:
                connector = self.env[rec._get_connector_name()]
                parsed = connector._parse_envelope(xml)
                rec.message_type = parsed.get("message_type") or False
                rec.message_id = parsed.get("message_id") or False
                rec.doc_type_code = parsed.get("doc_type_code") or False
                sender = parsed.get("sender_gln") or False
                receiver = parsed.get("receiver_gln") or False
                rec.sender_gln = sender
                rec.receiver_gln = receiver
                if rec.direction == "in" and sender:
                    partner = self.env["res.partner"].search(
                        [("global_location_number", "=", sender)], limit=1
                    )
                    rec.partner_id = partner.id if partner else False
                elif rec.direction == "out" and receiver:
                    partner = self.env["res.partner"].search(
                        [("global_location_number", "=", receiver)], limit=1
                    )
                    rec.partner_id = partner.id if partner else False
                raw_date = (
                    parsed.get("interchange_date")
                    or parsed.get("creation_date")
                    or ""
                )
                raw_time = (
                    parsed.get("interchange_time")
                    or parsed.get("creation_time")
                    or ""
                )
                if raw_date:
                    try:
                        d = datetime.date.fromisoformat(raw_date)
                        t = datetime.time()
                        if raw_time:
                            # Accept HH:MM, HH:MM:SS, or HH:MM:SS.fff
                            for fmt in ("%H:%M:%S", "%H:%M"):
                                try:
                                    t = datetime.datetime.strptime(
                                        raw_time, fmt
                                    ).time()
                                    break
                                except ValueError:
                                    continue
                        rec.message_date = datetime.datetime.combine(d, t)
                    except ValueError:
                        rec.message_date = False
                else:
                    rec.message_date = False
            except Exception:
                _logger.exception(
                    "Error parsing envelope for %s id=%s", self._name, rec.id
                )
                rec.message_type = False
                rec.message_id = False
                rec.doc_type_code = False
                rec.message_date = False
                rec.sender_gln = False
                rec.receiver_gln = False

    # ------------------------------------------------------------------
    # Effective message type resolution
    # ------------------------------------------------------------------

    # Message families where the body's <document_type> refers to the
    # OTHER document (the one being commented on) rather than to the
    # message itself — e.g. COMDIS carries a document_type=380 that
    # identifies the disputed invoice, not that the COMDIS "is" an
    # invoice. For these, message_type from the envelope is
    # authoritative and must not be overridden by DOC_TYPE_MAP.
    META_MESSAGE_TYPES = {"COMDIS", "APERAK"}

    def _get_effective_type(self):
        """Return the effective EDIFACT message type for dispatch.

        Primary: doc_type_code mapped through DOC_TYPE_MAP (reliable — lives
        in the message body, not rewritten by clearing houses).
        Fallback: message_type from the header (may be rewritten by the
        provider, e.g. GRiT Orion rewrites ORDRSP → ORDERS).

        Exception: for META_MESSAGE_TYPES (COMDIS, APERAK, …) the body's
        <document_type> refers to a DIFFERENT document (the disputed /
        acknowledged one), so we trust the envelope's message_type
        verbatim.
        """
        self.ensure_one()
        if self.message_type in self.META_MESSAGE_TYPES:
            return self.message_type
        if self.doc_type_code and self.doc_type_code in self.DOC_TYPE_MAP:
            return self.DOC_TYPE_MAP[self.doc_type_code]
        return self.message_type or ""

    # ------------------------------------------------------------------
    # ORM overrides
    # ------------------------------------------------------------------

    @api.model
    def _company_from_links(self, vals):
        """The company of the document a new message is created for.

        A message belongs to its document's company, not to whichever company
        the user happened to be in: the connector takes the sender's identity
        and credentials from it (``_enqueue_send``). The first linked record
        with a company decides.
        """
        for name, value in vals.items():
            field = self._fields.get(name)
            if (not value or not field or field.type != "many2one"
                    or not isinstance(value, int)
                    # A partner restricted to a company says nothing about
                    # which company a document is exchanged for.
                    or field.comodel_name in ("res.partner", "res.users", "res.company")):
                continue
            # sudo: a record rule hiding the document from the creator must not
            # silently leave the message in the creator's company.
            record = self.env[field.comodel_name].sudo().browse(value)
            if "company_id" in record._fields and record.exists() and record.company_id:
                return record.company_id
        return self.env["res.company"]

    def create(self, vals_list):
        for vals in ([vals_list] if isinstance(vals_list, dict) else vals_list):
            if not vals.get("company_id"):
                company = self._company_from_links(vals)
                if company:
                    vals["company_id"] = company.id
        records = super().create(vals_list)
        for rec in records:
            if rec.direction == "in" and rec._get_xml_content():
                rec._lookup_related_records()
        return records

    # ------------------------------------------------------------------
    # Inbound processing hook (overridden by purchase/sale modules)
    # ------------------------------------------------------------------

    def _lookup_related_records(self):
        """Dispatch inbound message to the appropriate processor.
        Default is a no-op; provider and purchase/sale modules override."""
        return

    def _backfill_partner_id_from_links(self):
        """Backfill partner_id, sale_order_id, purchase_order_id from any
        linked business record when they weren't set at parse/emit time.

        The compute on partner_id only re-fires when message_xml or
        attachment_id changes — so if a contact gets GLN-tagged AFTER the
        original receive (the common reason reprocess is needed), the
        compute won't pick it up. Provider dispatchers call this after
        linking a business record so partner_id always reflects the
        actual counterparty.

        Sale/purchase order IDs are resolved analogously from anchor
        records (picking, invoice, payment). For multi-order anchors
        (multi-SO invoices, multi-PO payments) the *primary* order wins
        — same semantics as Odoo's sale_type_id on account.move.

        Safe — no-op for fields already set or with no resolvable link.
        """
        for rec in self:
            if not rec.partner_id:
                # Probe each known link field; first one with a partner wins.
                for fname in (
                    "purchase_order_id", "vendor_bill_id", "picking_id",
                    "sale_order_id", "customer_invoice_id", "out_picking_id",
                    "payment_id",
                ):
                    if fname not in rec._fields:
                        continue
                    linked = rec[fname]
                    if linked and linked.partner_id:
                        rec.partner_id = linked.partner_id.id
                        break

            if "sale_order_id" in rec._fields and not rec.sale_order_id:
                so = self.env["sale.order"]
                if "out_picking_id" in rec._fields and rec.out_picking_id:
                    so = rec.out_picking_id.sale_id
                elif "customer_invoice_id" in rec._fields and rec.customer_invoice_id:
                    so = rec.customer_invoice_id.line_ids.sale_line_ids.order_id[:1]
                if so:
                    rec.sale_order_id = so.id

            if "purchase_order_id" in rec._fields and not rec.purchase_order_id:
                po = self.env["purchase.order"]
                if "picking_id" in rec._fields and rec.picking_id:
                    po = rec.picking_id.purchase_id
                elif "vendor_bill_id" in rec._fields and rec.vendor_bill_id:
                    po = (
                        rec.vendor_bill_id.invoice_line_ids
                        .purchase_line_id.order_id[:1]
                    )
                elif "payment_id" in rec._fields and rec.payment_id:
                    po = (
                        rec.payment_id.reconciled_bill_ids[:1]
                        .invoice_line_ids.purchase_line_id.order_id[:1]
                    )
                if po:
                    rec.purchase_order_id = po.id

    # ------------------------------------------------------------------
    # Unresolved-product policy hook (overridable by add-on modules)
    # ------------------------------------------------------------------

    def _edi_handle_unresolved_products(self, unresolved):
        """Decide what to do when an inbound document references one or
        more products our master data can't match.

        Default behaviour is **strict**: return False so the caller aborts
        the whole import and raises. This keeps the public module safe by
        default — no SO is created when any product is missing, no partner
        is silently shortchanged.

        Add-on modules (e.g. ``edi_base_sale_pending``) override this to
        persist the unresolved line data into their own model and return
        True so the caller proceeds with only the matched lines.

        :param unresolved: list[dict] — one dict per unmatched line. Keys:
            ean, article_name, article_number, article_number_buyer,
            quantity, unit_code, price, delivery_date.
        :returns: bool — True to continue with matched lines only, False
            to abort the entire import.
        """
        return False

    @staticmethod
    def _format_unresolved_products_error(unresolved):
        """Render a human-readable error_message for the strict-mode
        abort path. The caller raises UserError(this) which then lands on
        ``edi.message.error_message`` via _lookup_related_records' guard.
        """
        lines = [
            _("Cannot process inbound document: %d product(s) not found "
              "in master data.") % len(unresolved),
            "",
        ]
        for i, u in enumerate(unresolved, 1):
            lines.append(_(
                "  %(i)d. EAN=%(ean)s  qty=%(qty)s %(unit)s  price=%(price)s"
                "\n     name: %(name)s"
                "\n     supplier code: %(art)s  buyer code: %(buyer)s"
            ) % {
                "i": i,
                "ean": u.get("ean") or "-",
                "qty": u.get("quantity") or "?",
                "unit": u.get("unit_code") or "",
                "price": u.get("price") or 0.0,
                "name": u.get("article_name") or "-",
                "art": u.get("article_number") or "-",
                "buyer": u.get("article_number_buyer") or "-",
            })
        lines.append("")
        lines.append(_(
            "Create the missing product(s) in your catalog, then reprocess "
            "this EDI message."
        ))
        return "\n".join(lines)

    def _edi_unresolved_activity_user_id(self):
        """Return the user_id to assign the strict-mode To-Do activity to.

        Default is the current env user (typically the cron user). Override
        per-deployment via a custom module if you have a dedicated EDI
        responsible group.
        """
        self.ensure_one()
        return self.env.user.id

    # ------------------------------------------------------------------
    # Product resolution (shared by all providers)
    # ------------------------------------------------------------------

    def _resolve_product(self, partner, code):
        """Find a product by EDI code.

        ``article_ean`` on an inbound order is a GTIN — i.e. our own
        product's barcode/default_code — so it must resolve regardless of
        whether the sending partner is known to us. Between the barcode and
        the ``default_code`` match, a known partner's own codes
        (``product.supplierinfo.product_code``) are tried as well.

        For numeric codes (GTIN / UPC / EAN), tries both the literal form
        and a leading-zero-stripped form — partners frequently disagree on
        whether to left-pad EAN-13s, and that asymmetry breaks matching.
        """
        if not code:
            return False
        # Build the list of candidate code variants. GTIN/UPC/EAN
        # representations vary across partners — some pad to 13, some
        # strip leading zeros, some leave them. Try every standard length
        # the stripped numeric form fits into.
        candidates = {code}
        if code.isdigit():
            stripped = code.lstrip("0") or "0"
            candidates.add(stripped)
            for target_len in (8, 12, 13, 14):
                if len(stripped) <= target_len:
                    candidates.add(stripped.zfill(target_len))
        candidates = list(candidates)

        # Barcode first, then the sender's own code for the product, then
        # our internal reference — the order every partner carried while
        # ``res.partner.product_edi_code_priority`` existed (its default).
        Product = self.env["product.product"]
        product = Product.search([("barcode", "in", candidates)], limit=1)
        if product:
            return product
        if partner:
            supplierinfo = (
                self.env["product.supplierinfo"]
                .search(
                    [
                        ("product_code", "in", candidates),
                        ("partner_id", "=", partner.id),
                    ]
                )
                .sorted("date_end")
            )
            if supplierinfo:
                return (
                    supplierinfo[-1].product_id
                    or supplierinfo[-1].product_tmpl_id.product_variant_id
                )
        product = Product.search([("default_code", "in", candidates)], limit=1)
        return product or False

    # ------------------------------------------------------------------
    # XML parsing helpers (static, shared)
    # ------------------------------------------------------------------

    @staticmethod
    def _xml_text(element, path, default=None):
        el = element.find(path)
        if el is not None and el.text:
            return el.text.strip()
        return default

    @staticmethod
    def _xml_date(element, path, fmt="%Y-%m-%d"):
        text = EdiMessage._xml_text(element, path)
        if text:
            try:
                return datetime.datetime.strptime(text, fmt).date()
            except ValueError:
                pass
        return None

    # ------------------------------------------------------------------
    # Local-timezone date/time helpers
    #
    # Editel/GRiT XML carries dates and times as separate elements without
    # a timezone marker — the convention is the sender's local TZ (Slovak
    # for our network). Storing/sending naive datetimes as UTC silently
    # shifts every wire time by the local offset, which is what the
    # "ORDERS arrived for 08:00 but Odoo shows 02:00" symptom is.
    # ------------------------------------------------------------------

    @api.model
    def _edi_tz(self):
        """Configured EDI wire timezone (config param `edi.timezone`,
        default `Europe/Bratislava`)."""
        return self.env["ir.config_parameter"].sudo().get_param(
            "edi.timezone", "Europe/Bratislava",
        )

    @api.model
    def _edi_combine_local_to_utc(self, date_obj, time_str):
        """Combine a date with a 'HH:MM' or 'HH:MM:SS' time string, treat
        the result as local-wall-clock time in `_edi_tz()`, and return a
        naive UTC datetime suitable for storing in a fields.Datetime
        column. `time_str` may be falsy — defaults to midnight."""
        if not date_obj:
            return None
        hh = mm = ss = 0
        if time_str:
            parts = time_str.split(":")
            try:
                hh = int(parts[0])
                mm = int(parts[1]) if len(parts) > 1 else 0
                ss = int(parts[2]) if len(parts) > 2 else 0
            except (ValueError, IndexError):
                hh = mm = ss = 0
        local = datetime.datetime(
            date_obj.year, date_obj.month, date_obj.day, hh, mm, ss,
            tzinfo=ZoneInfo(self._edi_tz()),
        )
        return local.astimezone(datetime.timezone.utc).replace(tzinfo=None)

    @api.model
    def _edi_now_local_split(self):
        """Return (date_str 'YYYY-MM-DD', time_str 'HH:MM:SS') for
        the *current* instant rendered in `_edi_tz()`. Used by outbound
        emit helpers for <generation_date>/<generation_time> pairs."""
        now_local = datetime.datetime.now(ZoneInfo(self._edi_tz()))
        return now_local.strftime("%Y-%m-%d"), now_local.strftime("%H:%M:%S")

    @api.model
    def _edi_dt_to_local_split(self, dt, time_fmt="%H:%M:%S"):
        """Convert a stored naive-UTC datetime to local (date_str, time_str)
        for outbound use. Returns (None, None) if `dt` is falsy."""
        if not dt:
            return None, None
        utc = dt.replace(tzinfo=datetime.timezone.utc)
        local = utc.astimezone(ZoneInfo(self._edi_tz()))
        return local.strftime("%Y-%m-%d"), local.strftime(time_fmt)

    @staticmethod
    def _xml_float(element, path, default=0.0):
        text = EdiMessage._xml_text(element, path)
        if text:
            try:
                return float(text)
            except ValueError:
                pass
        return default

    # ------------------------------------------------------------------
    # Extension hooks — no-ops in base, override in localisation modules
    # ------------------------------------------------------------------

    def _hook_validate_outbound_xml(self, xml_string):
        """Called before sending outbound XML. Override to add XSD validation,
        content checks, or partner-specific transformations."""

    # ------------------------------------------------------------------
    # Cron: poll inbound messages
    # ------------------------------------------------------------------

    # ------------------------------------------------------------------
    # Inbound polling seams (overridable per document family)
    # ------------------------------------------------------------------

    def _dedup_key_for_inbound(self, connector, xml_content):
        """Return the duplicate-detection key for an inbound payload.

        Default: the biztalk ``message_id`` parsed by the connector envelope
        parser. Document-family modules override to supply their own key
        (e.g. the UBL ``cbc:ID`` for a Peppol payload, which has no biztalk
        envelope). Returning a falsy value disables dedup for that payload.
        """
        envelope_data = connector._parse_envelope(xml_content)
        return envelope_data.get("message_id", "")

    def _inbound_stub_vals(self, provider, xml_content, pkg):
        """Return the create-vals for an inbound stub message.

        Default reproduces the historical EDIFACT behaviour. Document-family
        modules override to merge extra vals (e.g. ``doc_family='peppol'``)
        based on the payload. Must not set ``message_xml`` — the caller stores
        the payload separately so the create() override does not auto-dispatch
        before phase 2.
        """
        return {
            "provider": provider,
            "name": pkg.get("name", ""),
            "direction": "in",
            "state": "received",
            "provider_interchange_id": pkg.get("raw_id") or False,
            "external_id": pkg.get("external_id") or False,
        }

    def _inbound_dispatch_may_commit(self):
        """Whether dispatching this inbound message may COMMIT the cursor
        mid-processing, so the poll must not wrap the dispatch in a savepoint.

        Default ``False``: dispatch runs inside the ambient transaction and is
        isolated under a savepoint (historical EDIFACT behaviour). Document-
        family modules whose importer commits internally override this to
        return ``True`` — e.g. Peppol UBL, where core
        ``account_document_import_mixin.rollbackable_transaction`` commits the
        decode, which would otherwise release the poll savepoint and abort the
        whole batch.
        """
        self.ensure_one()
        return False

    # ------------------------------------------------------------------
    # Durable writes from inside a queue_job
    # ------------------------------------------------------------------

    def _write_outside_job(self, vals, rollback_first=True):
        """Write ``vals`` on a fresh cursor so they survive a job rollback.

        Inside an OCA ``queue_job``, the natural "record the outcome, then
        raise" pattern silently loses the record write:

        * ``queue_job``'s ``_runjob`` calls ``env.cr.rollback()`` explicitly on
          the ``RetryableJobError`` branch, and re-raises to the http layer
          (which rolls back too) on ``FailedJobError``. The *job* row survives
          because it is written through ``job.in_temporary_env()``; ours is not.
        * ``_try_perform_job`` wraps ``perform()`` in ``_prevent_commit``, so
          committing the job cursor to save the write raises ``RuntimeError``.

        The visible symptom is a failed ``queue.job`` sitting next to a message
        still in ``queued`` with an empty ``error_message`` — the failure is
        invisible exactly where a user looks for it. Worse, anything else the
        job had written goes with it (e.g. a transmission id a retry depends on
        for idempotency).

        ``rollback_first`` rolls the job cursor back before opening the second
        cursor. That is normally required, not optional: if the job has already
        written these rows, its uncommitted locks would block the new cursor
        while the job waits on it — a deadlock. Pass False only when you know
        this transaction has not touched them.

        Never raises: bookkeeping must not mask the failure that prompted it.
        Returns True when the write was committed.
        """
        ids = self.ids
        if not ids or not vals:
            return False
        if rollback_first:
            try:
                self.env.cr.rollback()
            except Exception:
                _logger.exception("Could not roll back before an out-of-job write")
                return False
        try:
            with self.env.registry.cursor() as cr:
                # exists(): a record created in the transaction we just rolled
                # back is not visible to this cursor, and writing to it would
                # raise. Report False rather than True when there is nothing
                # left to write — the caller's outcome was NOT persisted.
                records = self.env(cr=cr)[self._name].browse(ids).exists()
                if not records:
                    _logger.warning(
                        "%s ids %s are not committed; their outcome %s could "
                        "not be persisted outside the job",
                        self._name,
                        ids,
                        list(vals),
                    )
                    return False
                records.write(vals)
        except Exception:
            _logger.exception(
                "Could not persist %s outside the job for %s ids %s",
                list(vals),
                self._name,
                ids,
            )
            return False
        return True

    def _get_messages(self, provider=None):
        """Cron entry point: poll registered provider(s) for inbound messages.

        Resolves the target providers in priority order:
          1. Explicit ``provider`` argument.
          2. Distinct providers found on ``self`` (manual trigger on records).
          3. All providers in ``PROVIDER_CONNECTOR_MAP`` (typical cron call
             with an empty ``self``).

        Each provider is polled independently so a failure on one does not
        block the others.
        """
        if provider:
            providers = [provider]
        elif self:
            providers = list({r.provider for r in self if r.provider})
        else:
            providers = list(self.PROVIDER_CONNECTOR_MAP.keys())
        for p in providers:
            self._poll_provider(p)

    def _poll_provider(self, provider):
        """Poll one provider's connector and persist the returned packages."""
        connector_name = self.PROVIDER_CONNECTOR_MAP.get(provider)
        if not connector_name:
            _logger.warning("No connector registered for provider %s", provider)
            return
        connector = self.env[connector_name]
        try:
            result = connector._poll_inbound()
        except Exception:
            _logger.exception(
                "Error polling %s for inbound messages", connector_name
            )
            return

        if isinstance(result, list):
            packages = result
            has_more = False
        else:
            packages = result.get("messages", []) if result else []
            has_more = bool(result.get("has_more")) if result else False

        for pkg in packages:
            xml_content = pkg.get("xml_content", "")
            filename = pkg.get("name", "")
            raw_id = pkg.get("raw_id")
            external_id = pkg.get("external_id")
            if not xml_content:
                continue

            # eXite has already transitioned the interchange server-side, so
            # if we drop it we lose the only copy. Persist a stub eagerly
            # (phase 1), then run processing under a second savepoint
            # (phase 2) — a failure there leaves the stub in state=error
            # with the raw XML attached for manual re-processing.

            # Pre-parse the envelope out-of-band for duplicate detection.
            # Delegated to a seam so non-EDIFACT families (e.g. Peppol UBL,
            # which has no biztalk envelope) can supply their own dedup key.
            try:
                envelope_msg_id = self._dedup_key_for_inbound(connector, xml_content)
            except Exception:
                envelope_msg_id = ""

            if envelope_msg_id and self.search(
                [
                    ("provider", "=", provider),
                    ("message_id", "=", envelope_msg_id),
                    ("direction", "=", "in"),
                ],
                limit=1,
            ):
                _logger.info(
                    "Duplicate inbound %s %s, skipping",
                    self._name,
                    envelope_msg_id,
                )
                if raw_id:
                    self._dispatch_ack(connector, raw_id)
                continue

            # Phase 1: stub creation. No message_xml in vals so the create()
            # override does NOT auto-dispatch _lookup_related_records yet —
            # we want phase 2 to handle that explicitly under its own
            # savepoint.
            msg = False
            try:
                with self.env.cr.savepoint():
                    stub_vals = self._inbound_stub_vals(
                        provider, xml_content, pkg
                    )
                    msg = self.create(stub_vals)
                    msg._store_xml(xml_content, filename=filename)
            except Exception:
                _logger.exception(
                    "Failed to persist edi_message stub for raw_id=%s; "
                    "package payload is lost",
                    raw_id,
                )
                continue

            # A provider may park a stub it cannot place (e.g. a receiver it
            # cannot route to a company): it is stored with its payload, so it
            # is acknowledged like any other, but nothing processes it.
            if msg.state == "error":
                if raw_id:
                    self._dispatch_ack(connector, raw_id)
                continue
            # Processed as the company the message belongs to, which the
            # provider may have routed away from the polling company.
            if msg.company_id:
                msg = msg.with_company(msg.company_id)

            # Phase 2: dispatch lookup/processing.
            #
            # Default path: isolate the dispatch under a savepoint so a failure
            # rolls back the partial work and leaves the stub in state=error —
            # never silently dropped.
            #
            # Commit-tolerant path: some document-family importers COMMIT the
            # cursor mid-dispatch — notably Peppol UBL, where core
            # ``account_document_import_mixin.rollbackable_transaction`` commits
            # the decode. A wrapping savepoint cannot survive that (its RELEASE
            # fails with InvalidSavepointSpecification and poisons the whole
            # poll batch). For those we persist the stub first, dispatch WITHOUT
            # a savepoint, and commit per message; on failure we roll back and
            # mark the already-persisted stub as error.
            if msg._inbound_dispatch_may_commit():
                # Persist the stub durably BEFORE the committing importer runs.
                # If even this fails, do NOT fall through to the acknowledge
                # below — leave the interchange on the provider so the next
                # poll re-fetches it (guards against ack-without-persist data
                # loss).
                try:
                    self.env.cr.commit()
                except Exception:
                    self.env.cr.rollback()
                    _logger.exception(
                        "Could not persist inbound stub for raw_id=%s; will "
                        "re-fetch on the next poll",
                        raw_id,
                    )
                    continue
                # Dispatch WITHOUT a savepoint (the importer commits
                # internally) and commit the result per message.
                try:
                    msg._lookup_related_records()
                    self.env.cr.commit()
                except Exception as e:
                    self.env.cr.rollback()
                    msg.invalidate_recordset()
                    _logger.exception(
                        "Lookup failed for edi_message id=%s raw_id=%s",
                        msg.id,
                        raw_id,
                    )
                    try:
                        msg.write(
                            {
                                "state": "error",
                                "error_message": (
                                    "Inbound processing failed: %s" % e
                                ),
                            }
                        )
                        self.env.cr.commit()
                    except Exception:
                        self.env.cr.rollback()
                        _logger.exception(
                            "Could not persist error state for edi_message "
                            "id=%s",
                            msg.id,
                        )
            else:
                try:
                    with self.env.cr.savepoint():
                        msg._lookup_related_records()
                except Exception as e:
                    _logger.exception(
                        "Lookup failed for edi_message id=%s raw_id=%s",
                        msg.id,
                        raw_id,
                    )
                    msg.write(
                        {
                            "state": "error",
                            "error_message": (
                                "Inbound processing failed: %s" % e
                            ),
                        }
                    )

            if raw_id:
                self._dispatch_ack(connector, raw_id)

        if has_more:
            cron_xmlid = self.PROVIDER_CRON_MAP.get(provider)
            if cron_xmlid:
                try:
                    self.env.ref(cron_xmlid)._trigger()
                except Exception:
                    _logger.exception(
                        "Failed to re-trigger %s poll cron", provider
                    )

    # ------------------------------------------------------------------
    # Manual actions
    # ------------------------------------------------------------------

    def action_reprocess(self):
        for rec in self.filtered(lambda r: r.direction == "in"):
            rec.write(
                {
                    "error_message": False,
                    "blocking_level": False,
                    "state": "received",
                }
            )
            if rec.company_id:
                rec = rec.with_company(rec.company_id)
            rec._lookup_related_records()

    SENDABLE_STATES = ("draft", "ready", "queued", "error")

    def _enqueue_send(self, connector=None, max_retries=5):
        """Dispatch this outbound message via queue_job and move state to
        'queued' so the UI reflects "in the queue, not yet sent."

        Replaces the scattered ``connector.with_delay()._send_message()``
        calls so every dispatch site goes through the same path. The
        ``job_edi_message_id`` context is what ``edi_base_queue_job``'s
        queue.job override picks up to stamp ``queue.job.edi_message_id``
        at create time, giving the bidirectional navigation between the
        message and its jobs. Clears any stale error fields so a retry
        starts clean.
        """
        self.ensure_one()
        if connector is None:
            connector = self.env[self._get_connector_name()]
        if self.company_id:
            # The connector reads its credentials and the sender's identity
            # from env.company; a job inherits the context it is queued with.
            connector = connector.with_company(self.company_id)
        self.write(
            {
                "state": "queued",
                "error_message": False,
                "blocking_level": False,
            }
        )
        self._post_dispatch_trace()
        return self._dispatch_send(connector, max_retries)

    def _dispatch_send(self, connector, max_retries=5):
        """Hand a ``queued`` message to whatever will actually send it.

        Nothing here. ``edi_base_queue_job`` overrides this with the
        ``with_delay`` call that used to live inline, and a provider that wants
        no job runner registers ``"cron"`` in
        :attr:`PROVIDER_DISPATCH_MAP` and is picked up by
        :meth:`_cron_send_queued` instead.

        The state write stays in :meth:`_enqueue_send` on purpose: ``queued``
        already means "dispatched, not yet sent", and it means that whichever
        of the two takes it from here. Only the handover differs.
        """
        self.ensure_one()
        return False

    def _dispatch_ack(self, connector, raw_id):
        """Acknowledge an inbound document.

        Synchronous by default, and that costs nothing: every caller is already
        inside the inbound polling cron, so there is no user waiting and no
        request to free up. ``edi_base_queue_job`` still pushes it to a job,
        which is worth keeping where a poll can return a large batch.
        """
        return connector._acknowledge_inbound(raw_id)

    @api.model
    def _cron_send_queued(self, limit=100):
        """Send what is ``queued`` for the providers that asked for a cron.

        Strictly scoped to :attr:`PROVIDER_DISPATCH_MAP`. A provider dispatched
        by job must never appear here, or a message would be sent twice — once
        by its job and once by this.

        Note the outcome is written with a plain ``write``, not
        ``_write_outside_job``. That helper exists because a job runner rolls
        the cursor back around a raising job, so the outcome has to be written
        on a cursor it cannot reach. Here nothing rolls back: the savepoint
        around the send is released, this transaction is intact, and a write on
        a separate cursor could not even see a row this transaction has not
        committed.
        """
        providers = [
            provider for provider, mode in self.PROVIDER_DISPATCH_MAP.items()
            if mode == "cron"
        ]
        if not providers:
            return
        messages = self.search([
            ("state", "=", "queued"),
            ("direction", "=", "out"),
            ("provider", "in", providers),
        ], limit=limit, order="id")
        for message in messages:
            connector = self.env[message._get_connector_name()]
            if message.company_id:
                connector = connector.with_company(message.company_id)
            try:
                # Each message in its own savepoint: one unsendable document
                # must not hold up the rest of the run, and the failure belongs
                # on that message rather than in a traceback nobody reads.
                with self.env.cr.savepoint():
                    connector._send_message(message)
            except RetryableJobError as exception:
                # The same signal a job runner acts on, honoured the same way:
                # leave it queued and let the next tick try again. Losing this
                # distinction would turn every rate limit and every timeout
                # into a document a human has to re-send by hand.
                _logger.info("EDI cron send deferred for %s: %s",
                             message.name, exception)
                message.write({
                    "error_message": str(exception),
                    "blocking_level": "warning",
                })
            except Exception as exception:  # noqa: BLE001
                _logger.exception("EDI cron send failed for %s", message.name)
                message.write({
                    "state": "error",
                    "error_message": str(exception),
                })

    def _edi_related_documents(self):
        """Business documents this message should leave a chatter trace on.

        ``edi.message`` itself owns no document links — they live on the
        satellite modules (``edi_base_sale`` adds ``sale_order_id`` /
        ``out_picking_id`` / ``customer_invoice_id``, ``edi_base_purchase``
        adds ``purchase_order_id``), so this returns nothing by default and
        each satellite ORs in what it knows about.

        Returns a list of recordsets, not a single recordset — the links
        point at different models.
        """
        self.ensure_one()
        return []

    def _post_dispatch_trace(self):
        """Post a chatter line on the linked documents when the message is
        actually handed to the queue.

        Without this the only visible chatter came from the provider's
        ``_*_emit_invoic`` at GENERATION time, so an invoice generated with
        auto-send off and dispatched later from the EDI message form showed
        no trace of the dispatch at all — the send was visible only on
        ``edi.message`` / ``queue.job``. Worse, a regenerate left two
        generation lines and no dispatch line, which reads as a double send.
        """
        self.ensure_one()
        from markupsafe import Markup, escape

        # Nothing in here may raise: with_delay() has already created the
        # queue.job row in this same transaction, so any exception escaping
        # this method rolls the dispatch back and the document is silently
        # never sent. That includes _edi_related_documents() itself — an
        # override, an access-rule denial or a broken link can all raise —
        # so the resolution is inside the guard, not outside it.
        try:
            docs = self._edi_related_documents()
        except Exception:
            _logger.exception(
                "Could not resolve related documents for edi.message %s",
                self.id,
            )
            return

        link = Markup(
            '<a href="#" data-oe-model="edi.message" data-oe-id="%d">%s</a>'
        ) % (self.id, escape(self.name or str(self.id)))
        body = Markup(_(
            "%(msg_type)s queued for dispatch via %(provider)s: %(link)s"
        )) % {
            "msg_type": self.message_type or _("EDI message"),
            "provider": self.provider or _("EDI"),
            "link": link,
        }
        # Dedup by (model, id): a message can carry links that resolve to
        # the same record, and with both edi_base_sale and edi_base_purchase
        # installed two independent overrides contribute to the same list.
        seen = set()
        for doc in docs:
            if not doc or not hasattr(doc, "message_post"):
                continue
            key = (doc._name, doc.id)
            if key in seen:
                continue
            seen.add(key)
            try:
                doc.message_post(body=body)
            except Exception:
                _logger.exception(
                    "Could not post dispatch trace for edi.message %s on %s",
                    self.id, doc,
                )

    def _enqueue_send_description(self):
        """Human-readable description stamped on the queue.job so jobs are
        searchable by message identifier in the Job Queue list. Override
        per-provider to customise the format.
        """
        self.ensure_one()
        label = self.name or self.external_id or self.message_type or f"#{self.id}"
        return f"Send {label} ({self.provider or 'EDI'})"

    def action_send(self):
        """Manually dispatch an outbound message for sending.

        Accepted source states: 'draft', 'ready', 'queued', 'error'. This
        makes the button work for initial sends (auto-send off), for
        re-queuing a still-pending job from the UI, and for retries of
        failed sends. Delegates the actual enqueue + state bookkeeping to
        ``_enqueue_send``.
        """
        for rec in self.filtered(
            lambda r: r.direction == "out" and r.state in self.SENDABLE_STATES
        ):
            rec._enqueue_send()

    def action_queue_send_selected(self):
        """Bulk-send entry point invoked from the list view's Actions menu.

        Splits the selection into sendable (outbound + in SENDABLE_STATES)
        and skipped, then always opens a confirmation wizard so the user
        can review the lists before queuing the dispatch.
        """
        sendable = self.filtered(
            lambda r: r.direction == "out" and r.state in self.SENDABLE_STATES
        )
        skipped = self - sendable

        if not sendable:
            raise UserError(_(
                "None of the selected messages can be sent (must be outbound "
                "and in state draft / ready / error)."
            ))

        wizard = self.env["edi.message.send.wizard"].create({
            "sendable_ids": [(6, 0, sendable.ids)],
            "skipped_ids": [(6, 0, skipped.ids)],
        })
        return {
            "type": "ir.actions.act_window",
            "name": _("Send EDI Messages"),
            "res_model": "edi.message.send.wizard",
            "view_mode": "form",
            "res_id": wizard.id,
            "target": "new",
        }
