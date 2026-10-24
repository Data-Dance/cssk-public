# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo import Command, fields
from odoo.tests import tagged

from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestVsReconcileOca(AccountTestInvoicingCommon):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # OCA skips auto-reconciliation under test unless asked for it
        cls.env = cls.env(context={**cls.env.context, "_test_account_reconcile_oca": True})
        cls.journal = cls.company_data["default_journal_bank"]

    def _invoice(self, amount, vs, partner=None, move_type="out_invoice"):
        invoice = self.env["account.move"].create({
            "move_type": move_type,
            "partner_id": (partner or self.partner_a).id,
            "invoice_date": fields.Date.from_string("2026-07-01"),
            "invoice_line_ids": [Command.create({
                "name": "Drevo",
                "quantity": 1,
                "price_unit": amount,
                "tax_ids": [Command.clear()],
            })],
        })
        invoice.action_post()
        # posting derives the symbol from the number; a test needs its own
        invoice.l10n_cssk_variable_symbol = vs
        return invoice

    def _line(self, amount, ref, payment_ref="Platba"):
        return self.env["account.bank.statement.line"].create({
            "journal_id": self.journal.id,
            "date": fields.Date.from_string("2026-07-10"),
            "amount": amount,
            "payment_ref": payment_ref,
            "ref": ref,
        })

    def test_short_symbol_in_the_structured_reference(self):
        """A 2-digit VS with leading zeros, only in the CAMT reference."""
        invoice = self._invoice(120.0, "42")
        line = self._line(120.0, "/VS0042/SS/KS0308")
        self.assertEqual(line.variable_symbol, "0042")
        self.assertTrue(line.is_reconciled)
        self.assertEqual(invoice.payment_state, "paid")

    def test_vendor_bill_is_paid_by_an_outgoing_line(self):
        bill = self._invoice(80.0, "2026077", move_type="in_invoice")
        line = self._line(-80.0, "/VS2026077/SS/KS")
        self.assertTrue(line.is_reconciled)
        self.assertEqual(bill.payment_state, "paid")

    def test_partial_payment_leaves_the_rest_open(self):
        invoice = self._invoice(300.0, "777")
        line = self._line(100.0, "/VS777/SS/KS")
        self.assertTrue(line.is_reconciled)
        self.assertEqual(invoice.payment_state, "partial")
        self.assertAlmostEqual(invoice.amount_residual, 200.0)

    def test_overpayment_is_proposed_not_reconciled(self):
        invoice = self._invoice(100.0, "888")
        line = self._line(150.0, "/VS888/SS/KS")
        self.assertFalse(line.is_reconciled)
        self.assertEqual(invoice.payment_state, "not_paid")
        proposed = [
            item["id"] for item in line.reconcile_data_info["data"]
            if item.get("kind") == "other"
        ]
        self.assertIn(invoice.line_ids.filtered(
            lambda aml: aml.account_id.reconcile).id, proposed)

    def test_ambiguous_symbol_resolved_only_by_amount(self):
        first = self._invoice(100.0, "555")
        second = self._invoice(250.0, "555", partner=self.partner_b)
        line = self._line(250.0, "/VS555/SS/KS")
        self.assertTrue(line.is_reconciled)
        self.assertEqual(second.payment_state, "paid")
        self.assertEqual(first.payment_state, "not_paid")

    def test_ambiguous_symbol_without_matching_amount_is_left(self):
        first = self._invoice(100.0, "556")
        second = self._invoice(250.0, "556", partner=self.partner_b)
        line = self._line(175.0, "/VS556/SS/KS")
        self.assertFalse(line.is_reconciled)
        self.assertEqual((first | second).mapped("payment_state"), ["not_paid", "not_paid"])

    def test_unknown_symbol_is_left_for_a_person(self):
        invoice = self._invoice(100.0, "999")
        line = self._line(100.0, "/VS123456/SS/KS")
        self.assertFalse(line.is_reconciled)
        self.assertEqual(invoice.payment_state, "not_paid")

    def test_another_partners_document_is_not_taken(self):
        """Two vendors can number their bills alike; the payer's account
        number tells them apart."""
        bill = self._invoice(80.0, "31", move_type="in_invoice")
        line = self.env["account.bank.statement.line"].create({
            "journal_id": self.journal.id,
            "date": fields.Date.from_string("2026-07-10"),
            "amount": -80.0,
            "payment_ref": "Platba",
            "ref": "/VS31/SS/KS",
            "partner_id": self.partner_b.id,
        })
        self.assertFalse(line.is_reconciled)
        self.assertEqual(bill.payment_state, "not_paid")

