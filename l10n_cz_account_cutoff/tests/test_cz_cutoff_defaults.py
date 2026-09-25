# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged


@tagged("post_install", "-at_install")
class TestCzCutoffDefaults(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("cz")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def test_deferral_accounts_wired(self):
        self.assertEqual(self.company.default_prepaid_expense_account_id.code, "381000")
        self.assertEqual(self.company.default_prepaid_revenue_account_id.code, "384000")
        self.assertEqual(self.company.default_accrued_expense_account_id.code, "383000")
        self.assertEqual(self.company.default_accrued_revenue_account_id.code, "385000")
