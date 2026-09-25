from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nCzAdvanceWiring(TransactionCase):
    """The post_init hook should wire the Czech advance-invoice accounts/journal
    onto every company on the Czech chart template."""

    def test_cz_companies_are_wired(self):
        companies = self.env["res.company"].search([("chart_template", "=", "cz")])
        if not companies:
            self.skipTest("No company on the Czech chart template in this database.")
        for company in companies:
            # account.code is company-dependent in Odoo 19: read it for the company.
            clearing = company.advance_received_account_id.with_company(company)
            self.assertTrue(clearing, "advance clearing account must be set")
            self.assertEqual(clearing.code, "324001")
            self.assertTrue(clearing.reconcile, "clearing account must be reconcilable")

            st = company.advance_tax_doc_account_id.with_company(company)
            self.assertTrue(st, "short-term account must be set")
            self.assertEqual(st.code, "324000")

            lt = company.advance_tax_doc_account_lt_id.with_company(company)
            self.assertTrue(lt, "long-term account must be set")
            self.assertEqual(lt.code, "475000")

            self.assertTrue(company.advance_invoice_journal_id, "advance journal must be set")

    def test_spec_is_idempotent_and_non_destructive(self):
        """Re-running the spec must not change already-configured accounts."""
        from odoo.addons.l10n_cz_sale_order_advance_invoice import CZ_SPEC
        from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec

        companies = self.env["res.company"].search([("chart_template", "=", "cz")])
        if not companies:
            self.skipTest("No company on the Czech chart template in this database.")
        before = {c.id: c.advance_received_account_id.id for c in companies}
        apply_advance_invoice_spec(self.env, "cz", CZ_SPEC)
        after = {c.id: c.advance_received_account_id.id for c in companies}
        self.assertEqual(before, after, "re-applying the spec must not change config")
