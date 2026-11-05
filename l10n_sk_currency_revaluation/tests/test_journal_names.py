# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
from odoo.tests import TransactionCase, tagged

from odoo.addons.l10n_sk_currency_revaluation.hooks import KURZ_NAMES, adopt_kurz_journal_names, post_init_hook


@tagged("post_install", "-at_install")
class TestKurzJournalNames(TransactionCase):

    def _company(self):
        company = self.env["res.company"].create({
            "name": "Kurz", "country_id": self.env.ref("base.sk").id})
        self.env.user.company_ids |= company
        self.env["account.chart.template"].try_loading("sk", company, install_demo=False)
        return company

    def _names(self, journal):
        self.env.flush_all()
        self.env.cr.execute("SELECT name FROM account_journal WHERE id = %s", [journal.id])
        return self.env.cr.fetchone()[0]

    def test_a_new_company_revalues_through_its_exchange_journal(self):
        company = self._company()
        self.assertTrue(company.currency_exchange_journal_id)
        self.assertEqual(company.currency_reval_journal_id, company.currency_exchange_journal_id)

    def test_the_hook_reuses_the_exchange_journal(self):
        """Loaded in English the exchange journal is EXCH; the hook must use it
        rather than create a second journal for the same differences."""
        company = self._company()
        company.currency_exchange_journal_id.code = "EXCH"
        company.currency_reval_journal_id = False
        post_init_hook(self.env)
        self.assertEqual(company.currency_reval_journal_id, company.currency_exchange_journal_id)
        self.assertFalse(self.env["account.journal"].search(
            [("code", "=", "KURZ"), ("company_id", "=", company.id)]))

    def test_the_hook_creates_kurz_only_without_an_exchange_journal(self):
        company = self._company()
        company.currency_exchange_journal_id.code = "EXCH"
        company.currency_exchange_journal_id = False
        company.currency_reval_journal_id = False
        post_init_hook(self.env)
        journal = company.currency_reval_journal_id
        self.assertEqual(journal.code, "KURZ")
        self.assertEqual(self._names(journal), KURZ_NAMES)

    def test_an_old_kurz_is_renamed_a_user_one_kept(self):
        company = self._company()
        journal = self.env["account.journal"].search(
            [("code", "=", "KURZ"), ("company_id", "=", company.id)]) or self.env["account.journal"].create(
            {"name": "x", "code": "KURZ", "type": "general", "company_id": company.id})
        def set_names(value):
            self.env.cr.execute("UPDATE account_journal SET name = %s::jsonb WHERE id = %s", [value, journal.id])
            journal.invalidate_recordset(["name"])
        set_names('{"en_US": "Kurzové rozdiely"}')
        adopt_kurz_journal_names(self.env, "sk")
        self.assertEqual(self._names(journal), KURZ_NAMES)
        set_names('{"en_US": "Our FX journal"}')
        adopt_kurz_journal_names(self.env, "sk")
        self.assertEqual(self._names(journal), {"en_US": "Our FX journal"})
