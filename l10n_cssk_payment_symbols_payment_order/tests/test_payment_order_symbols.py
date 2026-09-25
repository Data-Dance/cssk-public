# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestPaymentOrderSymbols(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.env.user.group_ids |= cls.env.ref(
            "account_payment_order.group_account_payment"
        )
        cls.manual_out = cls.env.ref(
            "account.account_payment_method_manual_out"
        )
        cls.mode = cls.env["account.payment.mode"].create({
            "name": "Manual out",
            "company_id": cls.env.company.id,
            "payment_method_id": cls.manual_out.id,
            "bank_account_link": "fixed",
            "fixed_journal_id": cls.company_data["default_journal_bank"].id,
        })

    def _bill(self, ref, **vals):
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "partner_id": self.partner_a.id,
            "invoice_date": "2026-07-01",
            "ref": ref,
            "invoice_line_ids": [
                Command.create({
                    "name": "stuff",
                    "quantity": 1,
                    "price_unit": 100.0,
                })
            ],
            **vals,
        })
        bill.action_post()
        return bill

    def test_symbols_copied_to_payment_line(self):
        bill = self._bill("FAK-2026-0042")
        bill.l10n_cssk_constant_symbol = "0308"
        bill.l10n_cssk_specific_symbol = "555"
        self.assertEqual(bill.l10n_cssk_variable_symbol, "20260042")

        order = self.env["account.payment.order"].create({
            "payment_mode_id": self.mode.id,
            "payment_type": "outbound",
        })
        payable = bill.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        payable.create_payment_line_from_move_line(order)

        line = order.payment_line_ids
        self.assertEqual(len(line), 1)
        self.assertEqual(line.variable_symbol, "20260042")
        self.assertEqual(line.constant_symbol, "0308")
        self.assertEqual(line.specific_symbol, "555")

    def test_no_symbols_no_vals(self):
        bill = self._bill(False)
        self.assertFalse(bill.l10n_cssk_variable_symbol)
        order = self.env["account.payment.order"].create({
            "payment_mode_id": self.mode.id,
            "payment_type": "outbound",
        })
        payable = bill.line_ids.filtered(
            lambda line: line.account_id.account_type == "liability_payable"
        )
        payable.create_payment_line_from_move_line(order)
        line = order.payment_line_ids
        self.assertEqual(len(line), 1)
        self.assertFalse(line.variable_symbol)
        self.assertFalse(line.constant_symbol)
        self.assertFalse(line.specific_symbol)
