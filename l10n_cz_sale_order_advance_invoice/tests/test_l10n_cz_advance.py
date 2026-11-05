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

    def test_a_company_whose_chart_comes_later_is_wired(self):
        """The hook only saw companies that had the chart at install time; a
        chart loaded afterwards (a new company, or one install run doing both)
        must be wired as it loads."""
        company = self.env["res.company"].create({
            "name": "Later s.r.o.", "country_id": self.env.ref("base.cz").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].try_loading("cz", company, install_demo=False)
        clearing = company.advance_received_account_id.with_company(company)
        self.assertEqual(clearing.code, "324001")
        self.assertTrue(clearing, "advance clearing account must be set")
        self.assertTrue(company.advance_tax_doc_account_id)
        self.assertEqual(company.advance_invoice_journal_id.code, "TDADV")
        self.assertEqual(company.advance_invoice_journal_id.company_id, company)

    # -- names ---------------------------------------------------------------
    def _later_company(self):
        company = self.env["res.company"].create({
            "name": "Names", "country_id": self.env.ref("base.cz").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].try_loading("cz", company, install_demo=False)
        return company

    def _stored_names(self, account):
        """The name jsonb as stored: every language, installed or not."""
        self.env.flush_all()
        self.env.cr.execute(f'SELECT name FROM "{account._table}" WHERE id = %s', [account.id])
        return self.env.cr.fetchone()[0]

    def test_clearing_account_has_an_english_and_a_czech_name(self):
        account = self._later_company().advance_received_account_id
        names = self._stored_names(account)
        self.assertEqual(names["en_US"], "Advances received – clearing (tax document)")
        self.assertEqual(names["cs_CZ"], "Přijaté zálohy – zúčtování (daňový doklad)")

    def test_an_old_untranslated_account_is_renamed_a_renamed_one_kept(self):
        """Earlier versions stored the Czech name as the English source;
        re-applying the spec (the upgrade does) fixes such an account and only
        such an account."""
        from odoo.addons.l10n_cz_sale_order_advance_invoice import CZ_SPEC
        from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec

        company = self._later_company()
        account = company.advance_received_account_id
        self.env.cr.execute(
            "UPDATE account_account SET name = %s::jsonb WHERE id = %s",
            ['{"en_US": "Přijaté zálohy – zúčtování (daňový doklad)"}', account.id])
        account.invalidate_recordset(["name"])
        apply_advance_invoice_spec(self.env, "cz", CZ_SPEC)
        names = self._stored_names(account)
        self.assertEqual(names["en_US"], "Advances received – clearing (tax document)")
        self.assertEqual(names["cs_CZ"], "Přijaté zálohy – zúčtování (daňový doklad)")

        self.env.cr.execute(
            "UPDATE account_account SET name = %s::jsonb WHERE id = %s",
            ['{"en_US": "Our own name"}', account.id])
        account.invalidate_recordset(["name"])
        apply_advance_invoice_spec(self.env, "cz", CZ_SPEC)
        self.assertEqual(self._stored_names(account), {"en_US": "Our own name"})

    # -- journal names ---------------------------------------------------------
    def test_the_journal_has_slovak_czech_and_english_names(self):
        journal = self._later_company().advance_invoice_journal_id
        self.assertEqual(journal.code, "TDADV")
        names = self._stored_names(journal)
        self.assertEqual(names["en_US"], "Tax Documents for Received Advance Payments")
        self.assertEqual(names["sk_SK"], "Faktúry k prijatým platbám")
        self.assertEqual(names["cs_CZ"], "Daňové doklady k přijatým platbám")

    def test_the_account_has_all_three_names(self):
        names = self._stored_names(self._later_company().advance_received_account_id)
        self.assertEqual(set(names), {"en_US", "sk_SK", "cs_CZ"})

    def test_an_old_journal_name_is_replaced_a_user_one_kept(self):
        from odoo.addons.l10n_cz_sale_order_advance_invoice import CZ_SPEC
        from odoo.addons.sale_order_advance_invoice.tools import apply_advance_invoice_spec

        company = self._later_company()
        journal = company.advance_invoice_journal_id
        def set_names(value):
            self.env.cr.execute(
                "UPDATE account_journal SET name = %s::jsonb WHERE id = %s",
                [value, journal.id])
            journal.invalidate_recordset(["name"])
        for old in ['Daňové doklady k přijatým platbám', 'Tax Documents for Advance Invoices']:
            set_names('{"en_US": "%s"}' % old)
            apply_advance_invoice_spec(self.env, "cz", CZ_SPEC)
            self.assertEqual(self._stored_names(journal)["en_US"], "Tax Documents for Received Advance Payments", old)
            self.assertEqual(self._stored_names(journal)["cs_CZ"], "Daňové doklady k přijatým platbám", old)
        # English already ours, a Slovak name corrected by hand: kept, Czech added
        set_names('{"en_US": "Tax Documents for Received Advance Payments", "sk_SK": "Môj denník"}')
        apply_advance_invoice_spec(self.env, "cz", CZ_SPEC)
        names = self._stored_names(journal)
        self.assertEqual(names["sk_SK"], "Môj denník")
        self.assertEqual(names["cs_CZ"], "Daňové doklady k přijatým platbám")
        # renamed by the user: left alone
        set_names('{"en_US": "Our journal"}')
        apply_advance_invoice_spec(self.env, "cz", CZ_SPEC)
        self.assertEqual(self._stored_names(journal), {"en_US": "Our journal"})
