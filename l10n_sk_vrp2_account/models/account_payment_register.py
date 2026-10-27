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
        rounding = 0.0
        if self.vrp2_fiscalize:
            rounding = self._vrp2_prepare_cash_rounding()
        payments = super()._create_payments()
        if self.vrp2_fiscalize:
            self._vrp2_fiscalize_payments(payments, rounding)
        return payments

    def _vrp2_prepare_cash_rounding(self):
        """Book the 0.05 € rounding of a fiscalized cash payment.

        § 3 ods. 4 zákona č. 18/1996 Z. z.: "Cena platená v hotovosti sa
        zaokrúhľuje na 5 eurocentov". The receipt reports the rounded sum as
        paid, so the payment in Odoo must be that sum too, or the cash book
        drifts from the register by every rounding. For a payment settling
        the invoice in full, the wizard is switched to the rounded amount and
        the difference written off to the company's VRP2 cash rounding
        account. A partial cash payment or several invoices at once cannot be
        rounded that way, so an amount that is not a multiple of 0.05 € is
        refused before anything reaches VRP2.

        Returns the difference (rounded − invoice amount) carried by the one
        payment, 0.0 when nothing was rounded.
        """
        self.ensure_one()
        company = self.company_id
        if self.vrp2_payment_type != "CASH" or not company.vrp2_round_5c:
            return 0.0
        round5 = self.env["account.move"]._vrp2_round_5c_amount
        currency = self.currency_id
        batches = self.batches
        edit_mode = self.can_edit_wizard and batches and (
            len(batches[0]["lines"]) == 1 or self.group_payment
        )
        if not edit_mode:
            for move in self.line_ids.move_id:
                residual = abs(sum(
                    self.line_ids.filtered(lambda l: l.move_id == move)
                    .mapped("amount_residual_currency")
                ))
                if currency.compare_amounts(round5(residual), residual):
                    raise UserError(_(
                        "Invoice %(invoice)s is paid in cash, which is rounded "
                        "to 0.05 €. Register its payment on its own so the "
                        "rounding can be booked.",
                        invoice=move.name,
                    ))
            return 0.0
        amount = self.amount
        rounded = round5(amount)
        if not currency.compare_amounts(rounded, amount):
            return 0.0
        if self.payment_difference_handling == "reconcile" or not currency.is_zero(
            self.payment_difference
        ):
            raise UserError(_(
                "A cash payment is rounded to 0.05 €. Pay %(amount)s in cash "
                "only together with the rest of the invoice, or enter an "
                "amount that is a multiple of 0.05 €.",
                amount=amount,
            ))
        rounding = company.vrp2_cash_rounding_id
        account = (
            rounding.profit_account_id if rounded > amount
            else rounding.loss_account_id
        )
        if not account:
            raise UserError(_(
                "The 0.05 € rounding of this cash payment has nowhere to be "
                "booked. Set the VRP2 cash rounding, with its profit and loss "
                "accounts, in Accounting ▸ Settings ▸ VRP2."
            ))
        # Two writes: a new amount recomputes the difference handling.
        self.amount = rounded
        self.write({
            "payment_difference_handling": "reconcile",
            "writeoff_account_id": account.id,
            "writeoff_label": _("Cash rounding"),
        })
        return currency.round(rounded - amount)

    def _vrp2_fiscalize_payments(self, payments, rounding=0.0):
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

        ``rounding`` is the cash rounding written off on the (single) payment
        by :meth:`_vrp2_prepare_cash_rounding`: the receipt reports the
        invoice part as the price and the payment as the rounded sum paid.
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
                        amount=payment.amount - rounding,
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
