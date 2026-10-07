import base64
import logging
import time
from decimal import ROUND_HALF_UP, Decimal

from odoo import _, api, fields, models
from odoo.exceptions import UserError
from odoo.tools.pdf import merge_pdf

_logger = logging.getLogger(__name__)


class AccountMove(models.Model):
    _inherit = "account.move"

    vrp2_receipt_ids = fields.One2many(
        "vrp2.receipt", "move_id", string="VRP2 Receipts"
    )
    vrp2_receipt_count = fields.Integer(
        compute="_compute_vrp2_receipt_count"
    )
    vrp2_has_active_receipt = fields.Boolean(
        string="VRP2 Fiscalized",
        compute="_compute_vrp2_has_active_receipt",
        store=True,
        help="There is a confirmed VRP2 invoice receipt for this invoice that "
        "has not been stornoed.",
    )

    def _compute_vrp2_receipt_count(self):
        groups = self.env["vrp2.receipt"]._read_group(
            [("move_id", "in", self.ids)], ["move_id"], ["__count"]
        )
        mapping = {move.id: count for move, count in groups}
        for move in self:
            move.vrp2_receipt_count = mapping.get(move.id, 0)

    @api.depends(
        "vrp2_receipt_ids.state",
        "vrp2_receipt_ids.receipt_type",
        "vrp2_receipt_ids.is_stornoed",
    )
    def _compute_vrp2_has_active_receipt(self):
        for move in self:
            move.vrp2_has_active_receipt = any(
                r.receipt_type == "invoice"
                and r.state == "confirmed"
                and not r.is_stornoed
                for r in move.vrp2_receipt_ids
            )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _vrp2_active_receipt(self):
        """Return the confirmed, non-stornoed invoice receipt (if any)."""
        self.ensure_one()
        return self.vrp2_receipt_ids.filtered(
            lambda r: r.receipt_type == "invoice"
            and r.state == "confirmed"
            and not r.is_stornoed
        )[:1]

    def _vrp2_merged_pdf_action(self, receipts, filename):
        """Merge the official VRP2 PDFs of ``receipts`` into one download."""
        pdfs = [
            base64.b64decode(r.pdf_receipt)
            for r in receipts
            if r.pdf_receipt
        ]
        if not pdfs:
            raise UserError(
                _("None of the VRP2 receipts carry a PDF to merge.")
            )
        merged = merge_pdf(pdfs) if len(pdfs) > 1 else pdfs[0]
        attachment = self.env["ir.attachment"].create({
            "name": filename,
            "type": "binary",
            "datas": base64.b64encode(merged),
            "mimetype": "application/pdf",
        })
        return {
            "type": "ir.actions.act_url",
            "url": "/web/content/%s?download=true" % attachment.id,
            "target": "self",
        }

    # ------------------------------------------------------------------
    # Fiscalization actions
    # ------------------------------------------------------------------

    def _vrp2_fiscalize(self, payment_type="CASH"):
        """Issue a VRP2 invoice receipt for each invoice in ``self``.

        Returns the created ``vrp2.receipt`` recordset. Only posted customer
        invoices that are not already fiscalized are processed.

        Transactional design (mirrors the Register Payment flow — fiscalization
        at the Financial Administration is an external side effect a database
        rollback cannot undo):

        1. VALIDATE every invoice offline first; any precondition problem
           raises *before a single byte reaches the FS*, so the whole batch
           rolls back cleanly and nothing exists on either side.
        2. EXECUTE one invoice at a time, each inside its own savepoint. Once at
           least one receipt has been fiscalized remotely, a later failure is
           CAUGHT and recorded (error-state ``vrp2.receipt`` + invoice chatter)
           instead of raised — raising would roll back the earlier receipts'
           local records while their FS-side receipts keep existing. A failure
           of the *first* invoice (nothing fiscalized yet) still raises, keeping
           fail-fast UX (and the single-invoice action's behaviour) intact.
        """
        Receipt = self.env["vrp2.receipt"]

        # -- Phase 1: validate ALL invoices before ANY network call --------
        for move in self:
            if move.move_type == "out_refund":
                raise UserError(
                    _(
                        "Credit note %s cannot be fiscalized as a VRP2 "
                        "payment receipt (it would report a positive sale to "
                        "the Financial Administration). Cancelling a fiscal "
                        "receipt is a separate storno flow — use 'Storno "
                        "(VRP2)' on the original fiscalized invoice."
                    )
                    % move.name
                )
            if move.move_type != "out_invoice":
                raise UserError(
                    _("VRP2 receipts can only be issued for customer invoices "
                      "(%s).") % move.name
                )
            if move.state != "posted":
                raise UserError(
                    _("Invoice %s must be posted before fiscalization.")
                    % move.name
                )
            if move._vrp2_active_receipt():
                raise UserError(
                    _("Invoice %s already has an active VRP2 receipt.")
                    % move.name
                )

        # -- Phase 2: fiscalize one by one ---------------------------------
        receipts = Receipt.browse()
        for move in self:
            try:
                with self.env.cr.savepoint():
                    receipts |= Receipt._create_for_invoice(move, payment_type)
            except Exception as exc:
                if not receipts:
                    # Nothing fiscalized yet — safe to fail the whole batch.
                    raise
                _logger.exception(
                    "VRP2 fiscalization failed for invoice %s after %s "
                    "receipt(s) had already been issued; keeping the "
                    "successful receipts.",
                    move.name,
                    len(receipts),
                )
                error = str(exc)
                # Local audit trail of the failed attempt (the FS may or may
                # not hold a receipt, e.g. on a timeout — never lose track).
                Receipt.create({
                    "company_id": move.company_id.id,
                    "partner_id": move.partner_id.id,
                    "currency_id": move.currency_id.id,
                    "receipt_type": "invoice",
                    "move_id": move.id,
                    "amount": move.amount_total,
                    "payment_method": payment_type,
                    "state": "error",
                    "error_message": error,
                })
                move.message_post(
                    body=_(
                        "⚠ VRP2 fiscalization of this invoice FAILED: %s\n"
                        "Issue the fiscal receipt again from the invoice "
                        "('Fiscalize in VRP2')."
                    )
                    % error
                )
        return receipts

    def action_vrp2_fiscalize(self):
        """Fiscalize a single invoice in VRP2 (CASH) and download its PDF."""
        self.ensure_one()
        receipts = self._vrp2_fiscalize("CASH")
        return self._vrp2_merged_pdf_action(
            receipts, "VRP2-%s.pdf" % (self.name or "receipt").replace("/", "_")
        )

    def action_vrp2_mass_fiscalize(self):
        """Mass action: fiscalize all selected invoices, return one joined PDF."""
        invoices = self.filtered(lambda m: m.move_type == "out_invoice")
        if not invoices:
            raise UserError(
                _(
                    "Select posted customer invoices to fiscalize in VRP2 "
                    "(credit notes are handled by the storno flow on the "
                    "original invoice)."
                )
            )
        receipts = invoices._vrp2_fiscalize("CASH")
        return invoices._vrp2_merged_pdf_action(
            receipts, "VRP2-receipts.pdf"
        )

    def action_vrp2_storno(self):
        """Storno the active VRP2 receipt of this invoice."""
        self.ensure_one()
        receipt = self._vrp2_active_receipt()
        if not receipt:
            raise UserError(
                _("Invoice %s has no active VRP2 receipt to storno.")
                % self.name
            )
        storno = receipt._create_storno()
        return self._vrp2_merged_pdf_action(
            storno, "VRP2-storno-%s.pdf"
            % (self.name or "receipt").replace("/", "_")
        )

    def action_vrp2_view_receipts(self):
        self.ensure_one()
        return {
            "name": _("VRP2 Receipts"),
            "type": "ir.actions.act_window",
            "res_model": "vrp2.receipt",
            "view_mode": "list,form",
            "domain": [("move_id", "=", self.id)],
            "context": {"create": False},
        }

    # ------------------------------------------------------------------
    # VRP2 invoice-receipt payload
    # ------------------------------------------------------------------

    def _vrp2_invoice_dto(self, amount, payment_type):
        """Build the body for POST /v5/receipt/create/invoice.

        Verified against a real "Úhrada faktúry" capture (2026-06-18): the
        invoice-payment receipt is sent as a flat object (no ``dto`` wrapper)
        and carries NO VAT/item breakdown — the issued invoice already holds
        the VAT, so only the paid total and the payment(s) are reported.

        Rounding mirrors the VRP2 web app (reverse-engineered from app.js,
        2026-06-26):
        - ``priceWithVat`` is the EXACT (unrounded) total with VAT;
        - a CASH payment line is rounded to the nearest 0.05 € (``zaokruhli5``)
          when the register's ``vrp2_round_5c`` is on, other payment types stay
          at 2 decimals (``zaokruhli2``);
        - ``roundingAmount`` carries the signed difference
          (rounded payment − exact total), so the receipt balances:
          ``priceWithVat + roundingAmount == payment sum``;
        - ``useRounding`` reflects the register setting.
        """
        self.ensure_one()
        actual = round(amount, 2)
        currency = self.currency_id.name or "EUR"
        use_rounding = bool(self.company_id.vrp2_round_5c)
        if use_rounding and payment_type == "CASH":
            paid = self._vrp2_round_5c_amount(actual)
        else:
            paid = actual
        rounding_amount = round(paid - actual, 2)
        return {
            "version": int(time.time() * 1000),
            "priceWithVat": actual,
            "payments": [{
                "type": payment_type,
                "sum": paid,
                "currency": currency,
                "exchangeRate": None,
                "amount": paid,
            }],
            "invoiceNumber": self.name or self.ref or "",
            "roundingAmount": rounding_amount,
            "useRounding": use_rounding,
        }

    @staticmethod
    def _vrp2_round_5c_amount(amount):
        """Round to the nearest 0.05 € (round half up), matching VRP2 zaokruhli5.

        Computed in integer cents to avoid binary-float drift.
        """
        cents = (Decimal(str(amount)) * 100).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        )
        rounded5 = (cents / 5).quantize(
            Decimal("1"), rounding=ROUND_HALF_UP
        ) * 5
        return float(rounded5 / 100)
