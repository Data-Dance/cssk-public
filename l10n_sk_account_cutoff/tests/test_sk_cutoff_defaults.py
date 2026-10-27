# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from ..hooks import post_init_hook


@tagged("post_install", "-at_install")
class TestSkCutoffDefaults(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def test_deferral_accounts_wired(self):
        self.assertEqual(
            self.company.default_prepaid_expense_account_id.code, "381000"
        )
        self.assertEqual(
            self.company.default_prepaid_revenue_account_id.code, "384000"
        )
        self.assertEqual(
            self.company.default_accrued_expense_account_id.code, "383000"
        )
        self.assertEqual(
            self.company.default_accrued_revenue_account_id.code, "385000"
        )

    # -- VAT is not accrued (accrual_taxes) ------------------------------
    def _accrued_expense_cutoff(self):
        """A December service billed in January, with VAT on the line."""
        tax = self.company_data["default_tax_purchase"]
        self.assertTrue(tax.amount)
        bill = self.env["account.move"].create({
            "move_type": "in_invoice",
            "company_id": self.company.id,
            "partner_id": self.partner_a.id,
            "invoice_date": "2026-01-15",
            "date": "2026-01-15",
            "invoice_line_ids": [Command.create({
                "name": "December service",
                "quantity": 1.0,
                "price_unit": 100.0,
                "account_id": self.company_data["default_account_expense"].id,
                "tax_ids": [Command.set(tax.ids)],
                "start_date": "2025-12-01",
                "end_date": "2025-12-31",
            })],
        })
        bill.action_post()
        return self.env["account.cutoff"].create({
            "company_id": self.company.id,
            "cutoff_date": "2025-12-31",
            "cutoff_type": "accrued_expense",
        })

    def test_vat_is_not_accrued(self):
        """With accrual_taxes left on, this failed with "Missing 'Accrued
        Expense Tax Account'": the chart has no account for it, and the VAT
        of an invoice not yet received is not deductible anyway."""
        self.assertFalse(self.company.accrual_taxes)
        cutoff = self._accrued_expense_cutoff()
        cutoff.get_lines()
        self.assertEqual(len(cutoff.line_ids), 1)
        self.assertEqual(cutoff.line_ids.cutoff_amount, -100.0)
        self.assertFalse(cutoff.line_ids.tax_line_ids)
        self.assertEqual(cutoff.cutoff_account_id.code, "383000")

    def test_install_turns_off_vat_accrual_that_has_no_account(self):
        self.company.accrual_taxes = True
        post_init_hook(self.env)
        self.assertFalse(self.company.accrual_taxes)

    def test_install_keeps_vat_accrual_somebody_configured(self):
        account = self.env["account.account"].create({
            "code": "343900", "name": "VAT on accruals",
            "account_type": "asset_current", "company_ids": [self.company.id],
        })
        self.company.write({
            "accrual_taxes": True,
            "default_accrued_expense_tax_account_id": account.id,
        })
        post_init_hook(self.env)
        self.assertTrue(self.company.accrual_taxes)
