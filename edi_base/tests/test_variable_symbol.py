"""The variable symbol an EDI invoice carries is digits, ten at most."""

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestVariableSymbol(AccountTestInvoicingCommon):

    def test_digits_of_the_reference_or_number(self):
        move = self.init_invoice("out_invoice", amounts=[100.0], post=True)
        move.payment_reference = "INV/2026/00012"
        expected = "202600012"
        if "l10n_cssk_variable_symbol" in move._fields:
            move.l10n_cssk_variable_symbol = expected
        self.assertEqual(move._edi_variable_symbol(), expected)

    def test_trailing_ten_digits(self):
        move = self.init_invoice("out_invoice", amounts=[100.0])
        move.payment_reference = "SO 2026 / 000 000 001 234"
        if "l10n_cssk_variable_symbol" in move._fields:
            move.l10n_cssk_variable_symbol = False
        self.assertEqual(move._edi_variable_symbol(), "0000001234")

    def test_vendor_bill_uses_the_supplier_reference(self):
        bill = self.init_invoice("in_invoice", amounts=[100.0])
        bill.write({"ref": "FV-2026-77", "payment_reference": False})
        if "l10n_cssk_variable_symbol" in bill._fields:
            bill.l10n_cssk_variable_symbol = False
        self.assertEqual(bill._edi_variable_symbol(), "202677")
