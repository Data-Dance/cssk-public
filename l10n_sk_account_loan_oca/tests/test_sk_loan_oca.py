# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

from odoo import Command
from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from ..models.account_loan import OCA_LOAN_ACCOUNT_FIELDS

EXPECTED_CODES = {
    "long_term_loan_account_id": "474000",
    "short_term_loan_account_id": "474100",
    "interest_expenses_account_id": "562000",
    "leased_asset_account_id": "022000",
}


@tagged("post_install", "-at_install")
class TestSkLoanOca(AccountTestInvoicingCommon):
    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]

    def test_new_loan_opens_with_the_slovak_accounts(self):
        values = (
            self.env["account.loan"]
            .with_company(self.company)
            .default_get(list(EXPECTED_CODES))
        )
        for fname, code in EXPECTED_CODES.items():
            account = self.env["account.account"].browse(values.get(fname))
            self.assertEqual(account.code, code, f"field {fname}")

    def test_role_map_covers_every_base_role(self):
        """Field names differ per engine; the roles must not drift apart."""
        from odoo.addons.l10n_sk_account_loan_base.models.res_company import (
            SK_LOAN_ACCOUNT_ROLES,
        )

        self.assertEqual(set(OCA_LOAN_ACCOUNT_FIELDS), set(SK_LOAN_ACCOUNT_ROLES))
        for fname in OCA_LOAN_ACCOUNT_FIELDS.values():
            self.assertIn(
                fname,
                self.env["account.loan"]._fields,
                f"{fname} is not a field on the OCA engine",
            )

    def test_company_onchange_refills_instead_of_clearing(self):
        """The engine blanks these on a company change — we put them back."""
        loan = self.env["account.loan"].with_company(self.company).new(
            {"company_id": self.company.id}
        )
        loan.long_term_loan_account_id = False
        loan.short_term_loan_account_id = False
        loan.interest_expenses_account_id = False

        loan._onchange_company()

        self.assertEqual(loan.long_term_loan_account_id.code, "474000")
        self.assertEqual(loan.short_term_loan_account_id.code, "474100")
        self.assertEqual(loan.interest_expenses_account_id.code, "562000")

    def test_lease_term_warns_below_the_60_percent_threshold(self):
        """§ 2 písm. s): finančný prenájom needs >= 60 % of the depreciation period."""
        from odoo.addons.l10n_sk_account_loan_base.models.l10n_sk_lease_mixin import (
            sk_min_lease_months,
        )

        # Odpisová skupina 1 = 4 years => 48 months => minimum 29 months.
        self.assertEqual(sk_min_lease_months("1"), 29)
        self.assertEqual(sk_min_lease_months("2"), 43)  # 6 years

        loan = self.env["account.loan"].with_company(self.company).new(
            {
                "company_id": self.company.id,
                "l10n_sk_depreciation_group": "1",
                "periods": 24,
                "method_period": 1,
            }
        )
        self.assertEqual(loan.l10n_sk_lease_months, 24)
        self.assertIn("menej", loan.l10n_sk_lease_term_warning)

        loan.periods = 36
        self.assertFalse(loan.l10n_sk_lease_term_warning)

    def test_vat_treatment_defaults_to_supply_of_goods(self):
        """§ 8 ods. 1 písm. c) is the ordinary finančný prenájom case."""
        loan = self.env["account.loan"].with_company(self.company).new(
            {"company_id": self.company.id}
        )
        self.assertEqual(loan.l10n_sk_vat_treatment, "goods")

    def _leasing(self, treatment):
        journal = self.env["account.journal"].search(
            [("type", "=", "purchase"), ("company_id", "=", self.company.id)], limit=1
        )
        return self.env["account.loan"].with_company(self.company).create(
            {
                "name": f"Lízing {treatment}",
                "company_id": self.company.id,
                "journal_id": journal.id,
                "loan_type": "leasing",
                "l10n_sk_vat_treatment": treatment,
                "partner_id": self.env["res.partner"].create({"name": "Lízingovka"}).id,
                "loan_amount": 12000.0,
                "periods": 12,
                "method_period": 1,
                "rate": 5.0,
                "start_date": "2026-01-31",
            }
        )

    def _instalment_line(self, loan, product):
        """A move line as the engine builds it for one instalment."""
        move = self.env["account.move"].create(
            {
                "move_type": "in_invoice",
                "partner_id": loan.partner_id.id,
                "company_id": self.company.id,
                "loan_id": loan.id,
                "invoice_line_ids": [
                    Command.create(
                        {"product_id": product.id, "quantity": 1, "price_unit": 1000.0}
                    )
                ],
            }
        )
        return move.invoice_line_ids[0]

    def test_goods_lease_instalments_carry_no_vat(self):
        """§ 8 ods. 1 písm. c): the whole VAT fell due at handover.

        The product deliberately CARRIES a purchase tax, so the assertion fails
        if the override is removed — otherwise it would pass vacuously on a
        product that has no tax to begin with.
        """
        tax = self.env.ref(f"account.{self.company.id}_vs_tuz_23")
        product = self.env["product.product"].create(
            {"name": "Splátka lízingu", "supplier_taxes_id": [Command.set(tax.ids)]}
        )
        service_loan = self._leasing("service")
        self.assertEqual(
            self._instalment_line(service_loan, product)._get_computed_taxes(),
            tax,
            "fixture check: this product must be taxed when nothing suppresses it",
        )

        loan = self._leasing("goods")
        line = self._instalment_line(loan, product)
        self.assertFalse(
            line._get_computed_taxes(),
            "taxing the instalments would tax the same supply twice",
        )

    def test_service_lease_instalments_are_taxed_as_before(self):
        """The opposite case must keep the engine's own behaviour."""
        tax = self.env.ref(f"account.{self.company.id}_vs_tuz_23")
        product = self.env["product.product"].create(
            {"name": "Nájom", "supplier_taxes_id": [Command.set(tax.ids)]}
        )
        loan = self._leasing("service")
        line = self._instalment_line(loan, product)
        self.assertEqual(line._get_computed_taxes(), tax)

    def test_non_slovak_company_is_untouched(self):
        other = self.env["res.company"].create({"name": "Autre SARL"})
        values = (
            self.env["account.loan"]
            .with_company(other)
            .default_get(list(EXPECTED_CODES))
        )
        for fname in EXPECTED_CODES:
            self.assertFalse(values.get(fname), f"{fname} should stay empty")
