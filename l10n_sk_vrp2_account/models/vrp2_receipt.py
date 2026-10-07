import json
import logging
from datetime import datetime, timezone

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class Vrp2Receipt(models.Model):
    _name = "vrp2.receipt"
    _description = "VRP2 Fiscal Receipt"
    _inherit = ["mail.thread"]
    _order = "create_date desc"
    _rec_name = "name"

    name = fields.Char(
        string="Receipt Number",
        readonly=True,
        copy=False,
        index=True,
        default="/",
    )
    company_id = fields.Many2one(
        "res.company",
        required=True,
        readonly=True,
        default=lambda self: self.env.company,
    )
    partner_id = fields.Many2one("res.partner", string="Customer", readonly=True)
    currency_id = fields.Many2one("res.currency", readonly=True)

    receipt_type = fields.Selection(
        [
            ("invoice", "Invoice Payment"),
            ("deposit", "Deposit"),
            ("withdraw", "Withdrawal"),
            ("storno", "Storno"),
        ],
        default="invoice",
        required=True,
        readonly=True,
    )
    state = fields.Selection(
        [
            ("draft", "Draft"),
            ("confirmed", "Confirmed"),
            ("error", "Error"),
            ("cancelled", "Cancelled"),
        ],
        default="draft",
        readonly=True,
        tracking=True,
    )

    move_id = fields.Many2one("account.move", string="Invoice", readonly=True)
    payment_id = fields.Many2one(
        "account.payment", string="Payment", readonly=True
    )

    # Storno linkage: a storno receipt points to the original it cancels;
    # an original is "stornoed" once such a storno receipt is confirmed.
    reversed_receipt_id = fields.Many2one(
        "vrp2.receipt",
        string="Reverses",
        readonly=True,
        copy=False,
        index=True,
        help="The original receipt this storno cancels.",
    )
    storno_ids = fields.One2many(
        "vrp2.receipt", "reversed_receipt_id", string="Stornos"
    )
    storno_receipt_id = fields.Many2one(
        "vrp2.receipt",
        string="Storno",
        compute="_compute_storno_receipt_id",
        help="The storno receipt that cancelled this one (if any).",
    )
    is_stornoed = fields.Boolean(
        string="Stornoed",
        compute="_compute_storno_receipt_id",
        help="True when a confirmed storno has cancelled this receipt.",
    )

    @api.depends("storno_ids.state", "storno_ids.receipt_type")
    def _compute_storno_receipt_id(self):
        for receipt in self:
            storno = receipt.storno_ids.filtered(
                lambda s: s.receipt_type == "storno"
                and s.state == "confirmed"
            )[:1]
            receipt.storno_receipt_id = storno
            receipt.is_stornoed = bool(storno)

    amount = fields.Monetary(currency_field="currency_id", readonly=True)
    payment_method = fields.Char(readonly=True)

    # ------------------------------------------------------------------
    # Fiscal data returned by VRP2
    # ------------------------------------------------------------------
    vrp2_server_id = fields.Char("VRP2 Receipt ID", readonly=True, copy=False)
    vrp2_receipt_uuid = fields.Char(
        "Receipt UUID", readonly=True, copy=False,
        help="VRP2 receiptId (e.g. V-...).",
    )
    vrp2_created = fields.Datetime("Fiscalized On", readonly=True)
    okp = fields.Char("OKP", readonly=True, help="Overovací kód podnikateľa.")
    qr_content = fields.Char(
        "Receipt Data",
        readonly=True,
        help="VRP2 dataBase64: the whole receipt as base64 JSON (items, VAT "
        "summary, payments). NOT the QR code — the printed QR encodes only "
        "the receiptId (decoded from four official receipts, 2026-10-06).",
    )
    pdf_receipt = fields.Binary(
        "Receipt PDF", readonly=True, copy=False, attachment=True,
        help="Official fiscal receipt PDF returned by VRP2.",
    )
    pdf_filename = fields.Char(readonly=True, copy=False)

    request_json = fields.Text("Request", readonly=True)
    response_json = fields.Text("Response", readonly=True)
    error_message = fields.Text(readonly=True)

    # ------------------------------------------------------------------
    # Creation from an invoice (no Odoo payment — the customer registers the
    # payment separately; this only issues + retains the VRP2 fiscal receipt)
    # ------------------------------------------------------------------

    def _create_for_invoice(self, move, payment_type="CASH", amount=None,
                            payment=None):
        """Fiscalize a customer invoice in VRP2 and persist the receipt.

        Runs inside the calling transaction: any VRP2 error raises, rolling
        back this receipt so a failed call leaves no half-recorded state.

        ``amount`` defaults to the full invoice total (manual fiscalization);
        the Register Payment flow passes the payment amount and links
        ``payment`` so partial payments fiscalize the paid sum.
        """
        move.ensure_one()
        if move.move_type != "out_invoice":
            raise UserError(
                _(
                    "VRP2 invoice receipts can only be issued for customer "
                    "invoices (%s is a %s). Cancelling a fiscal receipt is "
                    "the separate storno flow."
                )
                % (move.display_name, move.move_type)
            )
        company = move.company_id
        client = self.env["vrp2.client"]
        client._ensure_session(company)

        if amount is None:
            amount = move.amount_total
        request_body = move._vrp2_invoice_dto(amount, payment_type)

        receipt = self.create({
            "company_id": company.id,
            "partner_id": move.partner_id.id,
            "currency_id": move.currency_id.id,
            "receipt_type": "invoice",
            "move_id": move.id,
            "payment_id": payment.id if payment else False,
            "amount": amount,
            "payment_method": payment_type,
            "request_json": json.dumps(
                request_body, ensure_ascii=False, indent=2
            ),
        })

        response = client._create_invoice(company, request_body)
        receipt._apply_vrp2_response(response)
        _logger.info(
            "VRP2 invoice receipt %s created for %s (%.2f %s)",
            receipt.name,
            move.name,
            amount,
            move.currency_id.name,
        )
        return receipt

    # ------------------------------------------------------------------
    # Storno (cancellation)
    # ------------------------------------------------------------------

    def _create_storno(self):
        """Issue a VRP2 storno that cancels this (original) receipt.

        A storno is a normal *valid* receipt (POST /v5/receipt/create/valid)
        carrying a single ``CORRECTION`` line that references the original
        receipt (verified against a real storno capture, 2026-07-15). It always
        settles as an ``EXPENSE`` (refund) payment.

        Creates a ``storno``-type receipt linked back to the original and, on
        success, the original is marked cancelled (``is_stornoed`` flips True).
        """
        self.ensure_one()
        # Serialize concurrent stornos of the same receipt: take a row lock and
        # re-read the storno state so a double click / racing call can't fire
        # two fiscal stornos for one original.
        self.env.cr.execute(
            "SELECT id FROM vrp2_receipt WHERE id = %s FOR UPDATE", (self.id,)
        )
        self.invalidate_recordset(["state", "storno_ids"])

        if self.receipt_type == "storno":
            raise UserError(_("A storno receipt cannot itself be stornoed."))
        if self.state != "confirmed":
            raise UserError(
                _("Only a confirmed receipt can be stornoed.")
            )
        if self.is_stornoed:
            raise UserError(
                _("Receipt %s has already been stornoed.") % self.name
            )
        if not self.vrp2_receipt_uuid:
            raise UserError(
                _("Receipt %s has no VRP2 receiptId to reference for a storno.")
                % self.name
            )

        company = self.company_id
        move = self.move_id
        client = self.env["vrp2.client"]
        client._ensure_session(company)

        request_body = self._vrp2_storno_dto()

        storno = self.create({
            "company_id": company.id,
            "partner_id": self.partner_id.id,
            "currency_id": self.currency_id.id,
            "receipt_type": "storno",
            "move_id": move.id,
            "reversed_receipt_id": self.id,
            "amount": -self._vrp2_storno_amount(),
            "payment_method": "EXPENSE",
            "request_json": json.dumps(
                request_body, ensure_ascii=False, indent=2
            ),
        })

        response = client._create_receipt_valid(company, request_body)
        storno._apply_vrp2_response(response)
        # Cancel the original now that the storno is confirmed.
        self.write({"state": "cancelled"})
        _logger.info(
            "VRP2 storno %s cancelled receipt %s (invoice %s)",
            storno.name, self.name, move.name or "-",
        )
        return storno

    def _vrp2_storno_item_name(self):
        """Reconstruct the original receipt's line name for the storno line.

        The original invoice-payment receipt printed a single "Úhrada faktúry:
        <invoiceNumber>" line, where ``invoiceNumber`` is exactly what we sent
        on the original ``/create/invoice`` request. Reuse that stored value so
        the storno line matches the original print byte-for-byte; fall back to
        the linked invoice's name if the original request is unavailable.
        """
        self.ensure_one()
        invoice_number = ""
        if self.request_json:
            try:
                invoice_number = (
                    json.loads(self.request_json).get("invoiceNumber") or ""
                )
            except (ValueError, TypeError):
                invoice_number = ""
        if not invoice_number:
            invoice_number = self.move_id.name or ""
        return _("Úhrada faktúry: %s") % invoice_number

    def _vrp2_storno_amount(self):
        """The exact positive sum to reverse on the storno.

        Reverse what was actually *fiscalized* on the original receipt — the
        rounded paid amount, if 5-cent cash rounding was applied — not the
        pre-rounding invoice total in ``amount``. Otherwise a rounded original
        would leave a few-cent cash residual in the register after the storno.
        Read it from the payments of the original request we sent; fall back to
        the stored ``amount`` when that is unavailable. With no rounding the two
        are identical.
        """
        self.ensure_one()
        if self.request_json:
            try:
                payments = json.loads(self.request_json).get("payments") or []
                paid = sum(abs(p.get("amount") or 0) for p in payments)
                if paid:
                    return round(paid, 2)
            except (ValueError, TypeError, AttributeError):
                pass
        return round(abs(self.amount), 2)

    def _vrp2_storno_dto(self):
        """Build the storno request body for POST /v5/receipt/create/valid.

        Verified against a real storno capture (2026-07-15): the storno is a
        valid receipt with one negative ``CORRECTION`` item referencing the
        original ``receiptId`` and an ``EXPENSE`` payment for the refunded sum.
        Invoice-payment receipts carry no VAT breakdown (VAT lives on the
        invoice), so the correction line uses ``vatRate`` 0.

        ``vatPayer`` and ``version`` come from the register's dashboard
        (``organization.vatPayer``, ``cashRegister.version``) — the capture's
        version equalled the dashboard's, not the clock.
        """
        self.ensure_one()
        amount = self._vrp2_storno_amount()
        currency = self.currency_id.name or "EUR"
        header = self.company_id._vrp2_valid_receipt_header()
        return {
            "vatPayer": header["vatPayer"],
            "items": [{
                "priceWithVat": -amount,
                "discount": 0,
                "quantity": 1,
                "type": "CORRECTION",
                "vatRate": 0,
                "referenceReceiptId": self.vrp2_receipt_uuid,
                "receiptItemName": self._vrp2_storno_item_name(),
            }],
            "payments": [{
                "type": "EXPENSE",
                "sum": -amount,
                "currency": currency,
                "exchangeRate": None,
                "amount": -amount,
            }],
            "priceWithVat": -amount,
            "version": header["version"],
            "useRounding": False,
        }

    def _apply_vrp2_response(self, response):
        """Store the VRP2 create/invoice response on the receipt.

        Mapping verified against a real "Úhrada faktúry" response
        (2026-06-18). VRP2 returns the official receipt PDF (``pdfBase64``)
        and the QR payload (``dataBase64``); online receipts have no PKP.
        """
        self.ensure_one()
        data = response or {}

        number = data.get("receiptNumber")
        receipt_uuid = data.get("receiptId")
        server_id = data.get("id")

        created = fields.Datetime.now()
        created_ms = data.get("createDate") or data.get("issueDate")
        if created_ms:
            created = fields.Datetime.to_string(
                datetime.fromtimestamp(created_ms / 1000.0, tz=timezone.utc)
            )

        vals = {
            "vrp2_server_id": str(server_id) if server_id else False,
            "vrp2_receipt_uuid": receipt_uuid or False,
            "name": str(number) if number not in (None, "") else (
                receipt_uuid or "/"
            ),
            "okp": data.get("okp"),
            "qr_content": data.get("dataBase64"),
            "vrp2_created": created,
            "state": "confirmed",
        }

        pdf_b64 = data.get("pdfBase64")
        if pdf_b64:
            vals["pdf_receipt"] = pdf_b64
            vals["pdf_filename"] = "VRP2-%s.pdf" % (
                number or receipt_uuid or self.id
            )

        # Keep the raw response for audit, but drop the bulky base64 blobs.
        slim = {k: v for k, v in data.items() if k not in ("pdfBase64",)}
        vals["response_json"] = json.dumps(slim, ensure_ascii=False, indent=2)

        self.write(vals)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_view_invoice(self):
        self.ensure_one()
        if not self.move_id:
            return False
        return {
            "type": "ir.actions.act_window",
            "res_model": "account.move",
            "res_id": self.move_id.id,
            "view_mode": "form",
            "target": "current",
        }

    def action_print_receipt(self):
        """Download the official VRP2 PDF receipt."""
        self.ensure_one()
        if not self.pdf_receipt:
            raise UserError(_("No VRP2 PDF is stored for this receipt."))
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/vrp2.receipt/%s/pdf_receipt/%s?download=true"
            % (self.id, self.pdf_filename or "receipt.pdf"),
            "target": "self",
        }

    def action_send_email(self):
        """Email the fiscal receipt to the customer via VRP2."""
        for receipt in self:
            if receipt.state != "confirmed" or not receipt.vrp2_server_id:
                raise UserError(
                    _("Only a confirmed receipt with a VRP2 id can be emailed.")
                )
            email = receipt.partner_id.email
            if not email:
                raise UserError(
                    _("Customer '%s' has no email address.")
                    % receipt.partner_id.display_name
                )
            self.env["vrp2.client"]._send_receipt_email(
                receipt.company_id, receipt.vrp2_server_id, email
            )
        return True
