# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from unittest.mock import patch

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

PARTNER = "odoo.addons.l10n_cssk_payment_reliability.models.res_partner.ResPartner"


@tagged("post_install", "-at_install")
class TestReliability(AccountTestInvoicingCommon):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        # The relevance gate keys on the fiscal country; no full SK chart needed.
        cls.company.account_fiscal_country_id = cls.env.ref("base.sk")
        cls.bank = cls.env["res.partner.bank"].create({
            "acc_number": "SK6807200002891987426353",
            "partner_id": cls.partner_a.id,
        })

    def _bill(self):
        bill = self.init_invoice(
            "in_invoice", partner=self.partner_a, invoice_date="2026-06-10",
            amounts=[100.0], taxes=self.env["account.tax"],
        )
        bill.partner_bank_id = self.bank
        return bill

    def _run(self, bill, accounts, reliability):
        with patch(f"{PARTNER}._cssk_get_registered_accounts", return_value=accounts), \
             patch(f"{PARTNER}._cssk_get_tax_reliability", return_value=reliability):
            bill._cssk_run_reliability_check()

    def test_registered_account_ok(self):
        bill = self._bill()
        self._run(bill, ["SK6807200002891987426353"], "reliable")
        self.assertEqual(bill.cssk_bank_acc_status, "registered")
        self.assertEqual(bill.cssk_supplier_reliability, "reliable")
        self.assertFalse(bill.cssk_reliability_warning)
        self.assertTrue(bill.cssk_reliability_checked_on)

    def test_unregistered_account_warns(self):
        bill = self._bill()
        self._run(bill, ["SK9999999999999999999999"], "reliable")
        self.assertEqual(bill.cssk_bank_acc_status, "not_registered")
        self.assertIn("§69", bill.cssk_reliability_warning)
        self.assertTrue(bill.cssk_reliability_alert)

    def test_unreliable_supplier_warns(self):
        bill = self._bill()
        self._run(bill, ["SK6807200002891987426353"], "unreliable")
        self.assertEqual(bill.cssk_bank_acc_status, "registered")
        self.assertIn("reliability", bill.cssk_reliability_warning.lower())

    def test_provider_unavailable_is_unknown(self):
        bill = self._bill()
        self._run(bill, None, None)
        self.assertEqual(bill.cssk_bank_acc_status, "unknown")
        self.assertFalse(bill.cssk_reliability_warning)

    def test_check_uses_single_combined_query(self):
        """The bill check goes through the combined provider hook exactly
        once instead of firing one roundtrip per individual hook."""
        bill = self._bill()
        with patch(
            f"{PARTNER}._cssk_get_reliability_data",
            return_value=(["SK6807200002891987426353"], "reliable"),
        ) as mock_data, patch(
            f"{PARTNER}._cssk_get_registered_accounts",
            side_effect=AssertionError("bill check must use the combined hook"),
        ), patch(
            f"{PARTNER}._cssk_get_tax_reliability",
            side_effect=AssertionError("bill check must use the combined hook"),
        ):
            bill._cssk_run_reliability_check()
        self.assertEqual(mock_data.call_count, 1)
        self.assertEqual(bill.cssk_bank_acc_status, "registered")
        self.assertEqual(bill.cssk_supplier_reliability, "reliable")

    def test_autocheck_on_post(self):
        bill = self._bill()
        with patch(f"{PARTNER}._cssk_get_registered_accounts",
                   return_value=["SK9999999999999999999999"]), \
             patch(f"{PARTNER}._cssk_get_tax_reliability", return_value="reliable"):
            bill.action_post()
        self.assertEqual(bill.state, "posted")  # never blocked
        self.assertEqual(bill.cssk_bank_acc_status, "not_registered")
        self.assertTrue(bill.cssk_reliability_warning)
