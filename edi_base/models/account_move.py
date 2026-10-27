"""The variable symbol an EDI message carries for an invoice."""

import re

from odoo import models


class AccountMove(models.Model):
    _inherit = "account.move"

    def _edi_variable_symbol(self):
        """The invoice's variable symbol: up to ten digits, or ``""``.

        A variable symbol is what a Czech or Slovak payment order carries to
        pair the payment with the invoice, so it is digits only and at most
        ten of them. The payment reference or invoice number may well be
        ``INV/2026/00012``; sent as it is, the receiving system either rejects
        the element or pays under a symbol that pairs with nothing. Taken from
        ``l10n_cssk_payment_symbols`` when that is installed, otherwise the
        digits of the payment reference, else of the number (the supplier's
        number, ``ref``, on a vendor bill) — the trailing ten, which are the
        significant ones of a document number.
        """
        self.ensure_one()
        if "l10n_cssk_variable_symbol" in self._fields and self.l10n_cssk_variable_symbol:
            return self.l10n_cssk_variable_symbol
        if self.is_purchase_document(include_receipts=True):
            source = self.payment_reference or self.ref or ""
        else:
            source = self.payment_reference or self.name or ""
        return re.sub(r"\D", "", source)[-10:]
