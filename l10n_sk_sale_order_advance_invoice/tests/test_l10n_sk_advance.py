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

    # -- names ---------------------------------------------------------------
    def _later_company(self):
        company = self.env["res.company"].create({
            "name": "Names", "country_id": self.env.ref("base.sk").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].try_loading("sk", company, install_demo=False)
        return company

    def _stored_names(self, account):
        """The name jsonb as stored: every language, installed or not."""
        self.env.flush_all()
        self.env.cr.execute("SELECT name FROM account_account WHERE id = %s", [account.id])
        return self.env.cr.fetchone()[0]

    def test_clearing_account_has_an_english_and_a_slovak_name(self):
        account = self._later_company().advance_received_account_id
        names = self._stored_names(account)
        self.assertEqual(names["en_US"], "Advances received – clearing (tax document)")
        self.assertEqual(names["sk_SK"], "Prijaté preddavky – zúčtovanie (daňový doklad)")

    def test_an_old_untranslated_account_is_renamed_a_renamed_one_kept(self):
        """Earlier versions stored the Slovak name as the English source;
        re-applying the spec (the upgrade does) fixes such an account and only
        such an account."""
        from odoo.addons.l10n_sk_sale_order_advance_invoice import SK_SPEC
        from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec

        company = self._later_company()
        account = company.advance_received_account_id
        self.env.cr.execute(
            "UPDATE account_account SET name = %s::jsonb WHERE id = %s",
            ['{"en_US": "Prijaté preddavky – zúčtovanie (daňový doklad)"}', account.id])
        account.invalidate_recordset(["name"])
        apply_advance_invoice_spec(self.env, "sk", SK_SPEC)
        names = self._stored_names(account)
        self.assertEqual(names["en_US"], "Advances received – clearing (tax document)")
        self.assertEqual(names["sk_SK"], "Prijaté preddavky – zúčtovanie (daňový doklad)")

        self.env.cr.execute(
            "UPDATE account_account SET name = %s::jsonb WHERE id = %s",
            ['{"en_US": "Our own name"}', account.id])
        account.invalidate_recordset(["name"])
        apply_advance_invoice_spec(self.env, "sk", SK_SPEC)
        self.assertEqual(self._stored_names(account), {"en_US": "Our own name"})
