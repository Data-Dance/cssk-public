# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _post(self, soft=True):
        posted = super()._post(soft=soft)
        posted._pay_on_post()
        return posted

    def _pay_on_post(self):
        """Register the full payment of invoices whose payment mode asks for
        it, dated the invoice date, in the mode's fixed journal.

        Through the core payment wizard, so the payment is exactly what a user
        registering it by hand would get — same accounts, same reconciliation.
        """
        to_pay = self.filtered(
            lambda m: m.is_invoice(include_receipts=True)
            and m.payment_mode_id.pay_on_post
            and m.payment_state in ("not_paid", "partial")
            and not m.currency_id.is_zero(m.amount_residual))
        for move in to_pay:
            journal = move.payment_mode_id.fixed_journal_id
            wizard = self.env["account.payment.register"].with_context(
                active_model="account.move", active_ids=move.ids,
            ).create({
                "journal_id": journal.id,
                "payment_date": move.invoice_date or move.date,
            })
            wizard._create_payments()
