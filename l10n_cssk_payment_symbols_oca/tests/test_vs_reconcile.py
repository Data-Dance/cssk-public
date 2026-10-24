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


    # -- several lines of one import (cssk-public#9) --------------------
    # OCA proposes for the whole batch first and reconciles afterwards, so an
    # invoice one line takes is still open while the next line looks.

    def _import(self, *lines):
        """``(amount, ref)`` pairs created in ONE call, as an import does."""
        return self.env["account.bank.statement.line"].create([{
            "journal_id": self.journal.id,
            "date": fields.Date.from_string("2026-07-10"),
            "amount": amount,
            "payment_ref": "Platba",
            "ref": ref,
        } for amount, ref in lines])

    def test_an_invoice_paid_twice_in_one_import_does_not_fail_it(self):
        invoice = self._invoice(100.0, "601")
        first, second = self._import((100.0, "/VS601/SS/KS"), (100.0, "/VS601/SS/KS"))
        self.assertTrue(first.is_reconciled)
        self.assertEqual(invoice.payment_state, "paid")
        self.assertFalse(second.is_reconciled, "the second payment is for a person")

    def test_two_instalments_in_one_import_pay_the_invoice(self):
        invoice = self._invoice(100.0, "602")
        lines = self._import((60.0, "/VS602/SS/KS"), (40.0, "/VS602/SS/KS"))
        self.assertTrue(all(lines.mapped("is_reconciled")))
        self.assertEqual(invoice.payment_state, "paid")

    def test_a_second_payment_larger_than_what_is_left_is_proposed(self):
        invoice = self._invoice(100.0, "603")
        first, second = self._import((60.0, "/VS603/SS/KS"), (100.0, "/VS603/SS/KS"))
        self.assertTrue(first.is_reconciled)
        self.assertFalse(second.is_reconciled)
        self.assertAlmostEqual(invoice.amount_residual, 40.0)
        proposed = sum(
            item["amount"] for item in second.reconcile_data_info["data"]
            if item.get("kind") == "other"
        )
        self.assertAlmostEqual(abs(proposed), 40.0, msg="only what the first left open")

    def test_ambiguous_symbol_with_two_matching_amounts_is_left(self):
        """cssk-public#7: the amount cannot choose between two that fit."""
        first = self._invoice(100.0, "557")
        second = self._invoice(100.0, "557", partner=self.partner_b)
        line = self._line(100.0, "/VS557/SS/KS")
        self.assertFalse(line.is_reconciled)
        self.assertEqual((first | second).mapped("payment_state"), ["not_paid", "not_paid"])

    def test_an_overpayment_left_for_a_person_takes_nothing_from_the_next_line(self):
        """A proposal that is not reconciled reconciles nothing, so the exact
        payment after it still pays the invoice."""
        invoice = self._invoice(100.0, "604")
        over, exact = self._import((150.0, "/VS604/SS/KS"), (100.0, "/VS604/SS/KS"))
        self.assertFalse(over.is_reconciled)
        self.assertTrue(exact.is_reconciled)
        self.assertEqual(invoice.payment_state, "paid")
