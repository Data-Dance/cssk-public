# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).
"""The provider a Czech company gets on install, and what it refuses to do.

Every case here is one the naive version got wrong: creating a second provider
beside an archived one (overriding a decision), creating one for a company that
does not file in Czechia, and creating one with the company's own currency in
the list, which fetches nothing and looks configured.
"""

from unittest.mock import patch

from odoo.tests import tagged
from odoo.tests.common import TransactionCase


@tagged("post_install", "-at_install")
class TestCZDefaultProvider(TransactionCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.Provider = cls.env["res.currency.rate.provider"]
        cls.cz = cls.env.ref("base.cz")
        cls.sk = cls.env.ref("base.sk")
        cls.czk = cls.env.ref("base.CZK")
        # Two active foreign currencies, so the currency selection is tested
        # on more than one row — a single-element list hides an awful lot.
        cls.usd = cls.env.ref("base.USD")
        cls.gbp = cls.env.ref("base.GBP")
        (cls.czk | cls.usd | cls.gbp).write({"active": True})

    def _company(self, country, name="CZ Co"):
        return self.env["res.company"].create({
            "name": name, "country_id": country.id,
            "currency_id": self.czk.id,
        })

    def test_a_czech_company_gets_the_cnb_provider(self):
        company = self._company(self.cz)
        created = self.Provider._cz_ensure_default_provider(company)
        self.assertEqual(len(created), 1)
        self.assertEqual(created.service, "CNB")
        self.assertEqual(created.company_id, company)
        self.assertTrue(created.active)
        self.assertTrue(created.daily, "the statutory rate is a daily rate")

    def test_the_company_s_own_currency_is_not_fetched(self):
        """A provider quoting CZK against CZK fetches nothing and reads as
        configured, which is worse than a shorter list."""
        company = self._company(self.cz)
        created = self.Provider._cz_ensure_default_provider(company)
        self.assertNotIn(self.czk, created.currency_ids)
        self.assertIn(self.usd, created.currency_ids)
        self.assertIn(self.gbp, created.currency_ids)

    def test_it_is_idempotent(self):
        company = self._company(self.cz)
        first = self.Provider._cz_ensure_default_provider(company)
        second = self.Provider._cz_ensure_default_provider(company)
        self.assertEqual(len(first), 1)
        self.assertFalse(second, "a second run must create nothing")

    def test_an_archived_provider_is_a_decision_and_is_respected(self):
        """Somebody archived it on purpose. Creating a live one beside it
        would reverse that without saying so."""
        company = self._company(self.cz)
        existing = self.Provider._cz_ensure_default_provider(company)
        existing.active = False
        again = self.Provider._cz_ensure_default_provider(company)
        self.assertFalse(again)

    def test_a_company_that_does_not_file_in_czechia_gets_nothing(self):
        company = self._company(self.sk, name="SK Co")
        self.assertFalse(self.Provider._cz_ensure_default_provider(company))

    def test_no_active_foreign_currency_means_no_provider(self):
        """Nothing to fetch is not a half-configured provider; it is none.

        The condition is reached by patching the resolver, NOT by deactivating
        currencies. Odoo refuses to archive a currency that any company on the
        database is using — "This currency is set on a company and therefore
        cannot be deactivated" — so the obvious version of this test fails on
        every database that has more than the one company it just made, which
        is all of them.
        """
        company = self._company(self.cz)
        with patch.object(
            type(self.Provider), "_cz_default_provider_currencies",
            return_value=self.env["res.currency"].browse(),
        ):
            self.assertFalse(self.Provider._cz_ensure_default_provider(company))

    def test_an_existing_provider_s_currency_list_is_left_alone(self):
        """The whole reason this is a hook and not `_load_data`: an upgrade
        must not revert a list the user narrowed."""
        company = self._company(self.cz)
        provider = self.Provider._cz_ensure_default_provider(company)
        provider.currency_ids = self.usd
        self.Provider._cz_ensure_default_provider(company)
        self.assertEqual(provider.currency_ids, self.usd)
    def test_a_stale_fiscal_country_does_not_hide_the_company(self):
        """The bug that created zero providers on a Czech company.

        ``compute_account_tax_fiscal_country`` fills the fiscal country only
        when it is EMPTY and never re-syncs, so a database built from the
        US-defaulted template and then made Czech keeps
        ``account_fiscal_country_id = US``. Reading
        ``account_fiscal_country_id or country_id`` therefore never reaches the
        fallback, and the company matched nothing.
        """
        company = self._company(self.cz)
        if "account_fiscal_country_id" not in company._fields:
            self.skipTest("account is not installed")
        company.account_fiscal_country_id = self.env.ref("base.us")
        self.assertEqual(company.country_id, self.cz,
                         "precondition: still CZ by country")
        created = self.Provider._cz_ensure_default_provider(company)
        self.assertEqual(len(created), 1,
                         "a stale fiscal country must not hide the company")

    def test_the_fiscal_country_alone_is_enough(self):
        """The mirror: a foreign-registered branch that FILES in Czechia."""
        company = self._company(self.env.ref("base.us"), name="Branch")
        if "account_fiscal_country_id" not in company._fields:
            self.skipTest("account is not installed")
        company.account_fiscal_country_id = self.cz
        self.assertEqual(len(self.Provider._cz_ensure_default_provider(company)), 1)

