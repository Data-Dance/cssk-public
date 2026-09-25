from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.exceptions import UserError
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestAccrual(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.expense_account = cls.company_data["default_account_expense"]
        cls.income_account = cls.company_data["default_account_revenue"]
        cls.journal = cls.company_data["default_journal_misc"]
        cls.accrual_account = cls.env["account.account"].create({
            "name": "Dohadné účty pasívne",
            "code": "389000",
            "account_type": "liability_current",
            "reconcile": True,
            "company_ids": [Command.link(cls.company.id)],
        })

    def _estimate(self, amount=1000.0, atype="payable"):
        counterpart = (
            self.expense_account if atype == "payable" else self.income_account
        )
        return self.env["cssk.accrual.estimate"].create({
            "company_id": self.company.id,
            "partner_id": self.partner_a.id,
            "accrual_type": atype,
            "date": "2026-12-31",
            "amount": amount,
            "label": "Energy Dec 2026",
            "journal_id": self.journal.id,
            "accrual_account_id": self.accrual_account.id,
            "counterpart_account_id": counterpart.id,
        })

    def _accrual_lines(self, *moves):
        lines = self.env["account.move.line"]
        for m in moves:
            lines |= m.line_ids
        return lines.filtered(lambda l: l.account_id == self.accrual_account)

    def test_post_payable_entry(self):
        est = self._estimate(1000.0, "payable")
        self.assertTrue(est.name.startswith("DOHAD/"))
        est.action_post()
        self.assertEqual(est.state, "posted")
        self.assertEqual(est.move_id.state, "posted")
        debit = est.move_id.line_ids.filtered(lambda l: l.debit)
        credit = est.move_id.line_ids.filtered(lambda l: l.credit)
        self.assertEqual(debit.account_id, self.expense_account)
        self.assertEqual(credit.account_id, self.accrual_account)
        self.assertAlmostEqual(credit.credit, 1000.0)

    def test_receivable_entry_is_mirrored(self):
        est = self._estimate(500.0, "receivable")
        est.action_post()
        debit = est.move_id.line_ids.filtered(lambda l: l.debit)
        credit = est.move_id.line_ids.filtered(lambda l: l.credit)
        self.assertEqual(debit.account_id, self.accrual_account)
        self.assertEqual(credit.account_id, self.income_account)

    def test_settle_reverses_and_clears_accrual(self):
        est = self._estimate(1000.0, "payable")
        est.action_post()
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2027-01-15",
            amounts=[1050.0], taxes=self.env["account.tax"], post=True,
        )
        est.invoice_id = bill
        est.action_settle()
        self.assertEqual(est.state, "settled")
        self.assertTrue(est.reversal_move_id)
        # Estimate + reversal net to zero on the accrual account and reconcile.
        lines = self._accrual_lines(est.move_id, est.reversal_move_id)
        self.assertTrue(all(lines.mapped("reconciled")))
        self.assertAlmostEqual(sum(lines.mapped("balance")), 0.0, places=2)
        # Reversal is dated at the invoice date (difference lands in the period).
        self.assertEqual(est.reversal_move_id.date.isoformat(), "2027-01-15")

    def test_settle_requires_invoice(self):
        est = self._estimate()
        est.action_post()
        with self.assertRaises(UserError):
            est.action_settle()

    def test_post_only_from_draft(self):
        est = self._estimate()
        est.action_post()
        with self.assertRaises(UserError):
            est.action_post()

    def test_settle_reversal_date_never_before_estimate(self):
        """An invoice dated before the estimate must not pull the reversal
        into (or before) the accrued period: reversal date = max(invoice
        date, estimate date)."""
        est = self._estimate(1000.0, "payable")
        est.action_post()
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-12-15",
            amounts=[950.0], taxes=self.env["account.tax"], post=True,
        )
        est.invoice_id = bill
        est.action_settle()
        self.assertEqual(est.reversal_move_id.date.isoformat(), "2026-12-31")

    def test_settle_lock_date_error_names_accrual(self):
        est = self._estimate(1000.0, "payable")
        est.action_post()
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2027-01-15",
            amounts=[1050.0], taxes=self.env["account.tax"], post=True,
        )
        est.invoice_id = bill
        self.company.fiscalyear_lock_date = "2027-01-31"
        with self.assertRaisesRegex(UserError, est.name):
            est.action_settle()
        self.assertEqual(est.state, "posted")  # unchanged

    def test_settle_blocked_when_accrual_line_already_reconciled(self):
        """If someone already matched the accrual line manually, reversing
        would silently drop that matching — refuse with a clear error."""
        est = self._estimate(1000.0, "payable")
        est.action_post()
        counter = self.env["account.move"].create({
            "move_type": "entry",
            "journal_id": self.journal.id,
            "date": "2027-01-10",
            "line_ids": [
                Command.create({
                    "account_id": self.accrual_account.id,
                    "partner_id": self.partner_a.id,
                    "debit": 1000.0,
                }),
                Command.create({
                    "account_id": self.expense_account.id,
                    "partner_id": self.partner_a.id,
                    "credit": 1000.0,
                }),
            ],
        })
        counter.action_post()
        (self._accrual_lines(est.move_id, counter)).reconcile()

        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2027-01-15",
            amounts=[1000.0], taxes=self.env["account.tax"], post=True,
        )
        est.invoice_id = bill
        with self.assertRaisesRegex(UserError, "already reconciled"):
            est.action_settle()
        with self.assertRaisesRegex(UserError, "already reconciled"):
            est.action_cancel()

    def test_cancel_only_from_draft_or_posted(self):
        est = self._estimate(1000.0, "payable")
        est.action_post()
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2027-01-15",
            amounts=[1050.0], taxes=self.env["account.tax"], post=True,
        )
        est.invoice_id = bill
        est.action_settle()
        with self.assertRaises(UserError):
            est.action_cancel()  # settled
        draft = self._estimate(500.0, "payable")
        draft.action_cancel()  # draft → cancelled is fine (no reversal)
        self.assertEqual(draft.state, "cancelled")
        self.assertFalse(draft.reversal_move_id)
        with self.assertRaises(UserError):
            draft.action_cancel()  # already cancelled

    def test_post_requires_reconcilable_accrual_account(self):
        non_reconcilable = self.env["account.account"].create({
            "name": "Dohadné účty (non-reconcilable)",
            "code": "389999",
            "account_type": "liability_current",
            "reconcile": False,
            "company_ids": [Command.link(self.company.id)],
        })
        est = self._estimate(1000.0, "payable")
        est.accrual_account_id = non_reconcilable
        with self.assertRaises(UserError):
            est.action_post()
        self.assertEqual(est.state, "draft")

    def test_cancel_reverses_posted_estimate(self):
        est = self._estimate(1000.0, "payable")
        est.action_post()
        est.action_cancel()
        self.assertEqual(est.state, "cancelled")
        self.assertTrue(est.reversal_move_id)
        lines = self._accrual_lines(est.move_id, est.reversal_move_id)
        self.assertTrue(all(lines.mapped("reconciled")))
