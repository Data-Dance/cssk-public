# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).

from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestCounterAccountOnReconcileForm(TransactionCase):

    def _reconcile_arch(self):
        view = self.env.ref(
            "account_reconcile_oca.bank_statement_line_form_reconcile_view"
        )
        return self.env["account.bank.statement.line"].get_view(
            view_id=view.id, view_type="form",
        )["arch"]

    def test_the_counterparty_account_is_on_the_reconciliation_form(self):
        """Without it, a payer who quoted no variable symbol is identifiable
        only by name — which is the guess that mismatches receivables."""
        arch = self._reconcile_arch()
        self.assertIn('name="account_number"', arch)
        self.assertIn('name="partner_bank_id"', arch)

    def test_the_reference_is_still_there(self):
        """The anchor must not have displaced anything."""
        self.assertIn('name="payment_ref"', self._reconcile_arch())

    def test_the_standard_form_is_untouched(self):
        """This module changes one screen, not the model or its other views."""
        arch = self.env["account.bank.statement.line"].get_view(
            view_type="form",
        )["arch"]
        self.assertIn('name="account_number"', arch)
