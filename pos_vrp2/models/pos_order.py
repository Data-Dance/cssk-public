import json
import logging
import time
from datetime import datetime, timezone

from odoo import _, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class PosOrder(models.Model):
    _inherit = "pos.order"

    vrp2_state = fields.Selection(
        [
            ("not_fiscalized", "Not Fiscalized"),
            ("fiscalized", "Fiscalized"),
            ("error", "Error"),
        ],
        string="VRP2 Status",
        default="not_fiscalized",
        readonly=True,
        copy=False,
        index=True,
    )
    vrp2_receipt_number = fields.Char(
        string="VRP2 Receipt Number", readonly=True, copy=False
    )
    vrp2_server_id = fields.Char(
        string="VRP2 Receipt ID", readonly=True, copy=False
    )
    vrp2_receipt_uuid = fields.Char(
        string="VRP2 Receipt UUID", readonly=True, copy=False
    )
    vrp2_created = fields.Datetime(
        string="VRP2 Fiscalized On", readonly=True, copy=False
    )
    vrp2_okp = fields.Char(string="OKP", readonly=True, copy=False)
    vrp2_qr_content = fields.Char(
        string="VRP2 QR Content", readonly=True, copy=False
    )
    vrp2_pdf = fields.Binary(
        string="VRP2 Receipt PDF", readonly=True, copy=False, attachment=True
    )
    vrp2_pdf_filename = fields.Char(readonly=True, copy=False)
    vrp2_request_json = fields.Text(
        string="VRP2 Request", readonly=True, copy=False
    )
    vrp2_response_json = fields.Text(
        string="VRP2 Response", readonly=True, copy=False
    )
    vrp2_error_message = fields.Text(readonly=True, copy=False)

    # ------------------------------------------------------------------
    # Actions
    # ------------------------------------------------------------------

    def action_vrp2_fiscalize(self):
        """Manually fiscalize the selected orders in VRP2."""
        for order in self:
            order._vrp2_fiscalize()
        return True

    def action_vrp2_print_receipt(self):
        """Download the official VRP2 PDF receipt for this order."""
        self.ensure_one()
        if not self.vrp2_pdf:
            raise UserError(_("No VRP2 PDF is stored for this order."))
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/pos.order/%s/vrp2_pdf/%s?download=true"
            % (self.id, self.vrp2_pdf_filename or "receipt.pdf"),
            "target": "self",
        }

    # ------------------------------------------------------------------
    # Fiscalization
    # ------------------------------------------------------------------

    def _vrp2_fiscalize(self):
        """Create a fiscal sale receipt (pokladničný doklad) in VRP2.

        Mirrors the invoice-payment flow in ``l10n_sk_vrp2_account``: a VRP2
        error raises so the transaction rolls back and the order is not left
        in a half-fiscalized state.
        """
        self.ensure_one()
        till = self.config_id
        if not till.vrp2_enabled:
            raise UserError(
                _("VRP2 is not enabled for Point of Sale '%s'.")
                % till.display_name
            )
        if not till.vrp2_login:
            raise UserError(
                _("VRP2 credentials are not configured on till '%s'.")
                % till.display_name
            )
        if self.vrp2_state == "fiscalized":
            raise UserError(
                _("Order %s is already fiscalized in VRP2.") % self.name
            )

        # The receipt is issued on THIS till's own VRP2 cash register.
        client = self.env["vrp2.client"]
        client._ensure_session(till)

        request_body = self._vrp2_build_receipt_dto()
        self.vrp2_request_json = json.dumps(
            request_body, ensure_ascii=False, indent=2
        )

        response = client._create_receipt_valid(till, request_body)
        self._vrp2_apply_response(response)
        _logger.info(
            "VRP2 POS receipt %s created for order %s",
            self.vrp2_receipt_number,
            self.name,
        )
        return True

    def _vrp2_build_receipt_dto(self):
        """Build the body for POST /v5/receipt/create/valid.

        The request ENVELOPE is now verified from the create/invoice capture
        (2026-06-18): flat object (no ``dto`` wrapper), ``version`` ms-epoch,
        a ``payments`` array of {type,sum,currency,exchangeRate,amount}, and
        ``roundingAmount``/``useRounding``.

        [VERIFY LIVE] The ``items`` shape for a sale receipt is still a guess
        (no POS sale-receipt traffic captured). Confirm item field names
        (name/quantity/priceWithVat/vatId) against a real "Pokladničný doklad"
        capture; that is then the only thing left to correct here.
        """
        self.ensure_one()
        company = self.company_id
        tax_to_vat = company._vrp2_tax_to_vat_id()
        if not tax_to_vat:
            raise UserError(
                _(
                    "VRP2 VAT mapping is not configured for company '%s'. "
                    "Set it in Accounting settings and log in to VRP2 first."
                )
                % company.display_name
            )

        items = []
        for line in self.lines:
            vat_id = None
            for tax in line.tax_ids:
                if tax.id in tax_to_vat:
                    vat_id = tax_to_vat[tax.id]
                    break
            if vat_id is None:
                raise UserError(
                    _(
                        "Order line '%s' has no tax mapped to a VRP2 VAT rate. "
                        "Complete the VRP2 tax mapping."
                    )
                    % (line.full_product_name or line.product_id.display_name)
                )
            items.append({
                "name": line.full_product_name or line.product_id.display_name,
                "quantity": line.qty,
                "priceWithVat": round(line.price_subtotal_incl, 2),
                "vatId": vat_id,
            })

        currency = self.currency_id.name or "EUR"
        payments = []
        for payment in self.payment_ids:
            payment_type = (
                "CASH" if payment.payment_method_id.is_cash_count else "CARD"
            )
            amt = round(payment.amount, 2)
            payments.append({
                "type": payment_type,
                "sum": amt,
                "currency": currency,
                "exchangeRate": None,
                "amount": amt,
            })

        return {
            "version": int(time.time() * 1000),
            "priceWithVat": round(self.amount_total, 2),
            "items": items,
            "payments": payments,
            "roundingAmount": 0,
            "useRounding": True,
        }

    def _vrp2_apply_response(self, response):
        """Store the VRP2 create/valid response on the order.

        Response mapping follows the verified create/invoice response
        (2026-06-18): ``receiptNumber``/``receiptId``/``id``/``okp``, the
        official ``pdfBase64`` and the ``dataBase64`` QR payload; no PKP.
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
            "vrp2_state": "fiscalized",
            "vrp2_receipt_number": str(number) if number not in (None, "") else (
                receipt_uuid or False
            ),
            "vrp2_server_id": str(server_id) if server_id else False,
            "vrp2_receipt_uuid": receipt_uuid or False,
            "vrp2_okp": data.get("okp"),
            "vrp2_qr_content": data.get("dataBase64"),
            "vrp2_created": created,
            "vrp2_error_message": False,
        }

        pdf_b64 = data.get("pdfBase64")
        if pdf_b64:
            vals["vrp2_pdf"] = pdf_b64
            vals["vrp2_pdf_filename"] = "VRP2-%s.pdf" % (
                number or receipt_uuid or self.id
            )

        slim = {k: v for k, v in data.items() if k not in ("pdfBase64",)}
        vals["vrp2_response_json"] = json.dumps(slim, ensure_ascii=False, indent=2)

        self.write(vals)
