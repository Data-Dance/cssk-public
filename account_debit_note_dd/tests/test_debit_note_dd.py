# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Posting is core's, and the Credit Notes list holds customer documents only."""

from unittest.mock import patch

from odoo.exceptions import UserError
from odoo.tests import tagged
from odoo.tools.safe_eval import safe_eval

from odoo.addons.account.models.account_move import AccountMove as CoreAccountMove
from odoo.addons.account.tests.common import AccountTestInvoicingCommon


@tagged("post_install", "-at_install")
class TestDebitNoteDd(AccountTestInvoicingCommon):

    def _debit_note(self, invoice):
        wizard = self.env["account.debit.note"].with_context(
            active_model="account.move", active_ids=invoice.ids,
        ).create({"reason": "Price increase", "copy_lines": True})
        wizard.create_debit()
        return self.env["account.move"].search(
            [("debit_origin_id", "=", invoice.id)])

    def test_core_post_runs(self):
        """The module used to replace ``_post`` without calling ``super()``:
        core's routine, and every extension of it loaded earlier, never ran."""
        invoice = self.init_invoice(
            "out_invoice", amounts=[100.0])
        with patch.object(CoreAccountMove, "_post", autospec=True,
                          side_effect=CoreAccountMove._post) as core_post:
            invoice.action_post()
        self.assertTrue(core_post.called, "account.move._post of core never ran")
        self.assertEqual(invoice.state, "posted")

    def test_negative_total_is_refused(self):
        """One of the core checks the copy had dropped, for every invoice."""
        invoice = self.init_invoice(
            "out_invoice", amounts=[-100.0])
        with self.assertRaisesRegex(UserError, "negative total"):
            invoice.action_post()

    def test_negative_debit_note_is_refused(self):
        """A reduction is a credit note, debit note or not."""
        invoice = self.init_invoice(
            "out_invoice", amounts=[100.0], post=True)
        debit_note = self._debit_note(invoice)
        debit_note.invoice_line_ids.price_unit = -50.0
        with self.assertRaisesRegex(UserError, "negative total"):
            debit_note.action_post()

    def test_credit_notes_action_lists_customer_documents_only(self):
        sale = self.init_invoice(
            "out_invoice", amounts=[100.0], post=True)
        bill = self.init_invoice(
            "in_invoice", amounts=[100.0], post=True)
        customer_debit = self._debit_note(sale)
        vendor_debit = self._debit_note(bill)
        refund = self.init_invoice(
            "out_refund", amounts=[10.0])
        action = self.env.ref("account.action_move_out_refund_type_non_legacy")
        listed = self.env["account.move"].search(safe_eval(action.domain))
        self.assertIn(customer_debit, listed)
        self.assertIn(refund, listed)
        self.assertNotIn(vendor_debit, listed,
                         "a vendor debit note is not a customer credit note")
        self.assertNotIn(sale, listed)
