# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from ..hooks import post_init_hook
from ..models.res_company import SK_LOAN_ACCOUNT_ROLES, SK_LOAN_COMPANY_FIELDS

EXPECTED_CODES = {
    "long_term": "474000",
    "short_term": "474100",
    "interest": "562000",
    "leased_asset": "022000",
}


@tagged("post_install", "-at_install")
class TestSkLoanAccounts(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def test_accounts_wired_from_the_chart(self):
        for role, code in EXPECTED_CODES.items():
            account = self.company[SK_LOAN_COMPANY_FIELDS[role]]
            self.assertEqual(account.code, code, f"role {role}")

    def test_every_role_has_a_field_and_a_default(self):
        """The role list, the field map and the chart mapping stay in step."""
        self.assertEqual(set(SK_LOAN_ACCOUNT_ROLES), set(SK_LOAN_COMPANY_FIELDS))
        self.assertEqual(set(SK_LOAN_ACCOUNT_ROLES), set(EXPECTED_CODES))

    def test_accessor_returns_roles_not_field_names(self):
        accounts = self.company.l10n_sk_loan_accounts()
        self.assertEqual(set(accounts), set(SK_LOAN_ACCOUNT_ROLES))
        self.assertEqual(accounts["short_term"].code, "474100")

    def test_accessor_skips_unset_roles(self):
        self.company.l10n_sk_loan_leased_asset_account_id = False
        accounts = self.company.l10n_sk_loan_accounts()
        self.assertNotIn("leased_asset", accounts)
        self.assertIn("long_term", accounts)

    def test_hook_fills_only_empty_fields(self):
        """Install on an existing SK company must not overwrite a changed map."""
        other = self.env["account.account"].search(
            [("code", "=", "379000"), ("company_ids", "in", self.company.id)], limit=1
        )
        self.assertTrue(other, "379000 should exist on the SK chart")
        self.company.l10n_sk_loan_short_term_account_id = other
        self.company.l10n_sk_loan_interest_account_id = False

        post_init_hook(self.env)

        # Accountant's choice kept, the blank one refilled from the chart.
        self.assertEqual(self.company.l10n_sk_loan_short_term_account_id, other)
        self.assertEqual(self.company.l10n_sk_loan_interest_account_id.code, "562000")

    def test_settings_flag_is_sk_only(self):
        self.assertTrue(self.company.l10n_sk_loan_is_sk_company)
        other_chart = self.env["res.company"].create({"name": "Nezávislá s.r.o."})
        self.assertFalse(other_chart.l10n_sk_loan_is_sk_company)
