import logging

from odoo import _, api, fields, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)


class AccountPaymentRegister(models.TransientModel):
    _inherit = "account.payment.register"

    vrp2_available = fields.Boolean(compute="_compute_vrp2_available")
    vrp2_fiscalize = fields.Boolean(
        string="Fiscalize in VRP2",
        compute="_compute_vrp2_fiscalize",
        store=True,
        readonly=False,
        help="Issue a Slovak VRP2 fiscal receipt for the payment created here.",
    )
    vrp2_payment_type = fields.Selection(
        [("CASH", "Cash"), ("CARD", "Card")],
        string="VRP2 Payment Type",
        default="CASH",
    )

    @api.depends("company_id", "line_ids")
    def _compute_vrp2_available(self):
        for wizard in self:
            moves = wizard.line_ids.move_id
            wizard.vrp2_available = bool(
                wizard.company_id.vrp2_fiscalize_on_payment
                and wizard.company_id.vrp2_login
                and moves
                and all(m.move_type == "out_invoice" for m in moves)
            )

    @api.depends("vrp2_available")
    def _compute_vrp2_fiscalize(self):
        for wizard in self:
            wizard.vrp2_fiscalize = wizard.vrp2_available

    def _create_payments(self):
        payments = super()._create_payments()
        if self.vrp2_fiscalize:
            self._vrp2_fiscalize_payments(payments)
        return payments

    def _vrp2_fiscalize_payments(self, payments):
        """Issue a VRP2 invoice receipt for each created payment.

        Transactional design (fiscalization at the Financial Administration
        is an external side effect that a database rollback cannot undo):

        1. VALIDATE everything offline first. Any precondition problem
           raises *before a single byte reaches the FS*, so the whole
           wizard — payments included — rolls back cleanly and nothing
           exists on either side.
        2. EXECUTE one payment at a time, each attempt inside its own
           savepoint (so a failed attempt leaves no partial local rows).
           Once at least one receipt has been fiscalized at the FS, a later
           failure is CAUGHT and recorded (error-state ``vrp2.receipt`` +
           invoice chatter) instead of raised: raising would roll back the
           earlier receipt's local record while its FS-side receipt keeps
           existing. A failure of the *first* receipt (nothing fiscalized
           yet) still raises, keeping the fail-fast UX when there is
           nothing to protect.

        No ``cr.commit()`` is used — persistence of the successful receipts
        comes from the request transaction committing normally because no
        exception escapes once a receipt exists remotely.
        """
        Receipt = self.env["vrp2.receipt"]

        # -- Phase 1: validate ALL payments before ANY network call -------
        todo = []
        for payment in payments:
            invoices = payment.reconciled_invoice_ids.filtered(
                lambda m: m.move_type == "out_invoice"
            )
            if not invoices:
                continue
            if len(invoices) > 1:
                raise UserError(
                    _(
                        "VRP2 fiscalization supports one invoice per payment. "
                        "Disable 'Group Payments' and register payments "
                        "individually."
                    )
                )
            if invoices.state != "posted":
                raise UserError(
                    _("Invoice %s must be posted before fiscalization.")
                    % invoices.name
                )
            if invoices._vrp2_active_receipt():
                raise UserError(
                    _("Invoice %s already has an active VRP2 receipt.")
                    % invoices.name
                )
            todo.append((payment, invoices))

        # -- Phase 2: fiscalize one by one ---------------------------------
        done = Receipt.browse()
        for payment, invoice in todo:
            try:
                with self.env.cr.savepoint():
                    done |= Receipt._create_for_invoice(
                        invoice,
                        payment_type=self.vrp2_payment_type,
                        amount=payment.amount,
                        payment=payment,
                    )
            except Exception as exc:
                if not done:
                    # Nothing fiscalized yet — safe to fail the whole wizard.
                    raise
                _logger.exception(
                    "VRP2 fiscalization failed for invoice %s after %s "
                    "receipt(s) had already been issued; keeping the "
                    "successful receipts.",
                    invoice.name,
                    len(done),
                )
                error = str(exc)
                # Local audit trail of the failed attempt (the FS may or may
                # not hold a receipt, e.g. on a timeout — never lose track).
                Receipt.create(
                    {
                        "company_id": invoice.company_id.id,
                        "partner_id": invoice.partner_id.id,
                        "currency_id": invoice.currency_id.id,
                        "receipt_type": "invoice",
                        "move_id": invoice.id,
                        "payment_id": payment.id,
                        "amount": payment.amount,
                        "payment_method": self.vrp2_payment_type,
                        "state": "error",
                        "error_message": error,
                    }
                )
                invoice.message_post(
                    body=_(
                        "⚠ VRP2 fiscalization of this invoice's payment "
                        "FAILED: %s\nThe payment was registered; issue the "
                        "fiscal receipt again from the invoice ('Fiscalize "
                        "in VRP2')."
                    )
                    % error
                )
        return done
