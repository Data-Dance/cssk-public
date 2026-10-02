import logging
import re

from odoo import _, api, models
from odoo.exceptions import UserError

_logger = logging.getLogger(__name__)

# "ADV00042"-style document tokens and bare digit runs (3+ digits so a
# stray "12" doesn't look like a symbol; dates still slip through, which is
# why the digits tier requires an exact amount match to auto-apply).
_EXACT_TOKEN_RE = re.compile(r"\b[A-Z]{2,6}\d{3,10}\b")
_DIGITS_RE = re.compile(r"\d{3,10}")


class AccountBankStatementLine(models.Model):
    _inherit = "account.bank.statement.line"

    # ------------------------------------------------------------------
    # matching keys
    # ------------------------------------------------------------------
    def _cssk_advance_matching_keys(self):
        """Candidate keys for advance matching, by tier:

        * ``exact`` — full document tokens ("ADV00042") from the label/ref,
        * ``vs`` — the structured variable symbol, when the line has such a
          field (``l10n_cssk_payment_symbols`` or upstream odoo/odoo#275611;
          duck-typed so neither is a dependency),
        * ``digits`` — loose digit runs from the label (weakest signal).
        """
        self.ensure_one()
        keys = {"exact": set(), "vs": set(), "digits": set()}
        if "variable_symbol" in self._fields and self.variable_symbol:
            keys["vs"].add(self.variable_symbol)
        texts = [self.payment_ref or "", self.ref or ""]
        if self.transaction_details:
            texts.append(str(self.transaction_details))
        blob = " ".join(texts).upper()
        keys["exact"].update(_EXACT_TOKEN_RE.findall(blob))
        keys["digits"].update(_DIGITS_RE.findall(blob))
        return keys

    # ------------------------------------------------------------------
    # auto flow (cron / EE shim)
    # ------------------------------------------------------------------
    @api.model
    def _cron_match_advance_statement_lines(self, batch_size=200):
        companies = self.env["res.company"].search([
            ("advance_invoice_auto_match_statement", "=", True),
        ])
        if not companies:
            return
        lines = self.search(
            [
                ("company_id", "in", companies.ids),
                ("is_reconciled", "=", False),
                ("amount", ">", 0),
                ("journal_id.type", "=", "bank"),
                ("state", "=", "posted"),
            ],
            order="internal_index desc",
            limit=batch_size,
        )
        for line in lines:
            line._cssk_try_match_advance()

    def _cssk_try_match_advance(self):
        """Auto path: match and apply when safe, never raise. Returns the
        applied payment or False."""
        self.ensure_one()
        if not self.company_id.advance_invoice_auto_match_statement:
            return False
        error = self._cssk_advance_apply_blockers()
        if error:
            return False
        result = self.env["sale.order"]._cssk_find_advance_for_statement_line(
            self
        )
        if not result:
            return False
        order, tier = result
        remaining = order.amount_total - order.amount_paid
        if self.currency_id.compare_amounts(self.amount, remaining) > 0:
            _logger.info(
                "advance match: st_line %s exceeds remainder of %s — skipped",
                self.id,
                order.name,
            )
            return False
        if tier == "digits" and self.currency_id.compare_amounts(
            self.amount, remaining
        ):
            # a loose digit run (could be a date fragment) is only trusted
            # when the amount matches the open remainder exactly
            return False
        try:
            with self.env.cr.savepoint():
                payment = self._cssk_apply_advance_order(order)
        except UserError as apply_error:  # belt for racy/misconfigured cases
            _logger.warning(
                "advance match: applying st_line %s to %s failed: %s",
                self.id,
                order.name,
                apply_error,
            )
            return False
        _logger.info(
            "advance match: st_line %s paid %s (%s tier)",
            self.id,
            order.name,
            tier,
        )
        return payment

    # ------------------------------------------------------------------
    # apply
    # ------------------------------------------------------------------
    def _cssk_advance_apply_blockers(self):
        """Reason this line cannot pay an advance right now, or False."""
        self.ensure_one()
        if self.state != "posted" or self.is_reconciled:
            return _("The statement line is already reconciled.")
        if self.currency_id.compare_amounts(self.amount, 0.0) <= 0:
            return _("Only incoming transactions can pay an advance invoice.")
        if (
            self.foreign_currency_id
            or self.currency_id != self.company_id.currency_id
        ):
            return _(
                "Multi-currency transactions are not supported for "
                "automatic advance matching."
            )
        if not self.company_id.advance_received_account_id:
            return _(
                "Configure the advance clearing account on the company "
                "first (Advance Invoices settings)."
            )
        if not self._cssk_advance_payment_method_line():
            return _(
                "Journal %s has no inbound payment method with an "
                "outstanding receipts account.",
                self.journal_id.display_name,
            )
        return False

    def _cssk_advance_payment_method_line(self):
        self.ensure_one()
        return self.journal_id.inbound_payment_method_line_ids.filtered(
            "payment_account_id"
        )[:1]

    def _cssk_apply_advance_order(self, order):
        """Pay ``order`` with this statement line: real payment to the
        advance clearing account (the module's manual-payment path), its
        outstanding leg reconciled against this line's suspense leg, then
        the offline transaction that drives the advance statuses. Optional
        tax-document creation per company setting."""
        self.ensure_one()
        order.ensure_one()
        error = self._cssk_advance_apply_blockers()
        if error:
            raise UserError(error)
        if order.currency_id != self.currency_id:
            raise UserError(
                _("The advance invoice and the transaction use different "
                  "currencies.")
            )
        remaining = order.amount_total - order.amount_paid
        if self.currency_id.compare_amounts(self.amount, remaining) > 0:
            raise UserError(
                _("The transaction amount exceeds the advance's unpaid "
                  "amount.")
            )

        method_line = self._cssk_advance_payment_method_line()
        payment = self.env["account.payment"].create({
            "payment_type": "inbound",
            "partner_type": "customer",
            "partner_id": order.partner_invoice_id.commercial_partner_id.id,
            "amount": self.amount,
            "date": self.date,
            "memo": self.payment_ref or order.name,
            "journal_id": self.journal_id.id,
            "company_id": self.company_id.id,
            "currency_id": self.currency_id.id,
            "payment_method_line_id": method_line.id,
            "destination_account_id":
                self.company_id.advance_received_account_id.id,
        })
        payment.action_post()
        order._link_payment_to_transaction(payment)
        if order.state in ("draft", "sent"):
            order.action_confirm()

        # The partner first: writing it resynchronises the line's entry, and
        # once the suspense leg is rewritten to the payment's account the
        # entry has no suspense line left, so the resync rebuilds the lines
        # and tries to delete a posted one. A bank line without a partner is
        # the usual case for a match by variable symbol.
        if not self.partner_id:
            self.with_context(skip_readonly_check=True).partner_id = (
                payment.partner_id
            )
        self._cssk_reconcile_with_payment(payment)

        self._cssk_maybe_create_tax_document(order)
        return payment

    def _cssk_reconcile_with_payment(self, payment):
        """Rewrite this line's suspense leg to the payment's outstanding
        account and reconcile the two — the amounts are equal by
        construction (the payment was created from this line)."""
        self.ensure_one()
        _liquidity, suspense, _other = self._seek_for_lines()
        counterpart = payment.move_id.line_ids.filtered(
            lambda line: line.account_id == payment.outstanding_account_id
            and not line.reconciled
        )
        if not suspense or not counterpart:
            raise UserError(
                _("The statement line or the payment has no open leg left "
                  "to reconcile.")
            )
        suspense.with_context(skip_readonly_check=True).write({
            "account_id": counterpart[0].account_id.id,
            "partner_id": payment.partner_id.id,
        })
        (suspense | counterpart).reconcile()

    def _cssk_maybe_create_tax_document(self, order):
        mode = self.company_id.advance_invoice_auto_tax_doc
        if (
            mode not in ("draft", "post")
            or order.advance_invoice_accounting_status != "waiting"
        ):
            return
        invoices_before = order.invoice_ids
        order.action_create_invoice_direct_for_advance()
        invoice = (order.invoice_ids - invoices_before)[:1]
        if invoice and mode == "post":
            invoice.action_post()
