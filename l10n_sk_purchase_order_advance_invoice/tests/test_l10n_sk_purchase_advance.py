from odoo.tests import TransactionCase, tagged


@tagged("post_install", "-at_install")
class TestL10nSKPurchaseAdvanceWiring(TransactionCase):

    def test_a_company_whose_chart_comes_later_is_wired(self):
        """The hook only saw companies that had the chart at install time; a
        chart loaded afterwards (a new company, or one install run doing both)
        must be wired as it loads."""
        company = self.env["res.company"].create({
            "name": "Later", "country_id": self.env.ref("base.sk").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].try_loading("sk", company, install_demo=False)
        clearing = company.advance_paid_clearing_account_id.with_company(company)
        self.assertEqual(clearing.code, "314001")
        self.assertTrue(clearing.reconcile)
        self.assertEqual(
            company.advance_paid_account_id.with_company(company).code, "314000")
        self.assertEqual(company.advance_purchase_journal_id.code, "PDADV")
        self.assertEqual(company.advance_purchase_journal_id.company_id, company)

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
        self.env.cr.execute(f'SELECT name FROM "{account._table}" WHERE id = %s', [account.id])
        return self.env.cr.fetchone()[0]

    def test_clearing_account_has_an_english_and_a_slovak_name(self):
        account = self._later_company().advance_paid_clearing_account_id
        names = self._stored_names(account)
        self.assertEqual(names["en_US"], "Advances granted – clearing (tax document)")
        self.assertEqual(names["sk_SK"], "Poskytnuté preddavky – zúčtovanie (daňový doklad)")

    def test_an_old_untranslated_account_is_renamed_a_renamed_one_kept(self):
        """Earlier versions stored the Slovak name as the English source;
        re-applying the spec (the upgrade does) fixes such an account and only
        such an account."""
        from odoo.addons.l10n_sk_purchase_order_advance_invoice import SK_SPEC
        from odoo.addons.purchase_order_advance_invoice.tools import apply_purchase_advance_spec

        company = self._later_company()
        account = company.advance_paid_clearing_account_id
        self.env.cr.execute(
            "UPDATE account_account SET name = %s::jsonb WHERE id = %s",
            ['{"en_US": "Poskytnuté preddavky – zúčtovanie (daňový doklad)"}', account.id])
        account.invalidate_recordset(["name"])
        apply_purchase_advance_spec(self.env, "sk", SK_SPEC)
        names = self._stored_names(account)
        self.assertEqual(names["en_US"], "Advances granted – clearing (tax document)")
        self.assertEqual(names["sk_SK"], "Poskytnuté preddavky – zúčtovanie (daňový doklad)")

        self.env.cr.execute(
            "UPDATE account_account SET name = %s::jsonb WHERE id = %s",
            ['{"en_US": "Our own name"}', account.id])
        account.invalidate_recordset(["name"])
        apply_purchase_advance_spec(self.env, "sk", SK_SPEC)
        self.assertEqual(self._stored_names(account), {"en_US": "Our own name"})

    # -- journal names ---------------------------------------------------------
    def test_the_journal_has_slovak_czech_and_english_names(self):
        journal = self._later_company().advance_purchase_journal_id
        self.assertEqual(journal.code, "PDADV")
        names = self._stored_names(journal)
        self.assertEqual(names["en_US"], "Tax Documents for Sent Advance Payments")
        self.assertEqual(names["sk_SK"], "Faktúry k odoslaným platbám")
        self.assertEqual(names["cs_CZ"], "Daňové doklady k odeslaným platbám")

    def test_the_account_has_all_three_names(self):
        names = self._stored_names(self._later_company().advance_paid_clearing_account_id)
        self.assertEqual(set(names), {"en_US", "sk_SK", "cs_CZ"})

    def test_an_old_journal_name_is_replaced_a_user_one_kept(self):
        from odoo.addons.l10n_sk_purchase_order_advance_invoice import SK_SPEC
        from odoo.addons.purchase_order_advance_invoice.tools import apply_purchase_advance_spec

        company = self._later_company()
        journal = company.advance_purchase_journal_id
        def set_names(value):
            self.env.cr.execute(
                "UPDATE account_journal SET name = %s::jsonb WHERE id = %s",
                [value, journal.id])
            journal.invalidate_recordset(["name"])
        for old in ['Faktúry k odoslaným platbám']:
            set_names('{"en_US": "%s"}' % old)
            apply_purchase_advance_spec(self.env, "sk", SK_SPEC)
            self.assertEqual(self._stored_names(journal)["en_US"], "Tax Documents for Sent Advance Payments", old)
            self.assertEqual(self._stored_names(journal)["sk_SK"], "Faktúry k odoslaným platbám", old)
        # English already ours, a Slovak name corrected by hand: kept, Czech added
        set_names('{"en_US": "Tax Documents for Sent Advance Payments", "sk_SK": "Môj denník"}')
        apply_purchase_advance_spec(self.env, "sk", SK_SPEC)
        names = self._stored_names(journal)
        self.assertEqual(names["sk_SK"], "Môj denník")
        self.assertEqual(names["cs_CZ"], "Daňové doklady k odeslaným platbám")
        # renamed by the user: left alone
        set_names('{"en_US": "Our journal"}')
        apply_purchase_advance_spec(self.env, "sk", SK_SPEC)
        self.assertEqual(self._stored_names(journal), {"en_US": "Our journal"})
