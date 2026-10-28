"""The variable symbol and the bank account an EDI message carries for an
invoice."""

import re

from odoo import api, models

# Country code, check digits, then 11 to 30 alphanumerics (ISO 13616).
_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{11,30}$")


def _is_iban(number):
    """ISO 13616 shape and its ISO 7064 mod-97 check. Done here rather than
    with stdnum's ``iban``, which loads a data file at import and cannot be
    relied on in every deployment's packaging."""
    if not _IBAN_RE.match(number):
        return False
    rotated = number[4:] + number[:4]
    return int("".join(str(int(char, 36)) for char in rotated)) % 97 == 1


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

    def _edi_payment_bank(self):
        """The account this invoice asks to be paid to: its own (the one the
        PDF and the payment QR code name), else the company's first account
        that is an IBAN, else its first account."""
        self.ensure_one()
        banks = self.company_id.partner_id.bank_ids
        return (
            self.partner_bank_id
            or banks.filtered(lambda bank: self._edi_iban(bank))[:1]
            or banks[:1]
        )

    @api.model
    def _edi_iban(self, bank):
        """``bank``'s number as an IBAN for an ``<iban>`` element — upper case,
        no spaces — or ``""`` when it is not one.

        A domestic number (``19-2000145399/0800``) is not an IBAN, and neither
        is an IBAN typed with spaces: the receiving system validates the
        element and refuses the whole document, or misreads the account. The
        check is the number's own (ISO 7064 mod 97), not ``acc_type``, which
        reads ``iban`` only when ``base_iban`` is installed.
        """
        number = (bank.sanitized_acc_number or "") if bank else ""
        number = number.replace(" ", "").upper()
        return number if _is_iban(number) else ""
