# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _generate_qr_code(self, silent_errors=False):
        """Hand the due date to the QR stack.

        ``res.partner.bank`` never sees the move, only the communication
        strings, so PAY by square's PaymentDueDate travels via context — the
        same way ``l10n_cssk_payment_symbols`` passes VS/KS/SS.
        """
        self.ensure_one()
        move = self
        if self.invoice_date_due:
            move = self.with_context(qr_code_date_due=self.invoice_date_due)
        return super(AccountMove, move)._generate_qr_code(
            silent_errors=silent_errors
        )
