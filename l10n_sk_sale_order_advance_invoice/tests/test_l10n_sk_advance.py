from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nSkAdvanceWiring(TransactionCase):
    """The post_init hook should wire the Slovak advance-invoice accounts/journal
    onto every company on the Slovak chart template."""

    def test_sk_companies_are_wired(self):
        companies = self.env["res.company"].search([("chart_template", "=", "sk")])
        if not companies:
            self.skipTest("No company on the Slovak chart template in this database.")
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
        from odoo.addons.l10n_sk_sale_order_advance_invoice import SK_SPEC
        from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec

        companies = self.env["res.company"].search([("chart_template", "=", "sk")])
        if not companies:
            self.skipTest("No company on the Slovak chart template in this database.")
        before = {c.id: c.advance_received_account_id.id for c in companies}
        apply_advance_invoice_spec(self.env, "sk", SK_SPEC)
        after = {c.id: c.advance_received_account_id.id for c in companies}
        self.assertEqual(before, after, "re-applying the spec must not change config")

    def test_a_company_whose_chart_comes_later_is_wired(self):
        """The hook only saw companies that had the chart at install time; a
        chart loaded afterwards (a new company, or one install run doing both)
        must be wired as it loads."""
        company = self.env["res.company"].create({
            "name": "Later s.r.o.", "country_id": self.env.ref("base.sk").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].try_loading("sk", company, install_demo=False)
        clearing = company.advance_received_account_id.with_company(company)
        self.assertEqual(clearing.code, "324001")
        self.assertTrue(clearing, "advance clearing account must be set")
        self.assertTrue(company.advance_tax_doc_account_id)
        self.assertEqual(company.advance_invoice_journal_id.code, "TDADV")
        self.assertEqual(company.advance_invoice_journal_id.company_id, company)
