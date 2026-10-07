# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""That a fresh Slovak company has profiles, and that they resolve.

The point of the module is that an asset created — or imported — on a new SK
company has something to point at. A profile whose accounts did not resolve
would satisfy that by existing and fail at the first depreciation, so the
resolution is what these assert, not the count.
"""

from odoo.addons.account.tests.common import AccountTestInvoicingCommon
from odoo.tests import tagged

from odoo.addons.l10n_sk_account_asset_profile.models.account_chart_template import (
    SK_ASSET_PROFILES,
)


@tagged("post_install", "-at_install")
class TestSkAssetProfile(AccountTestInvoicingCommon):

    @classmethod
    @AccountTestInvoicingCommon.setup_country("sk")
    def setUpClass(cls):
        super().setUpClass()
        cls.company = cls.company_data["company"]
        cls.profiles = cls.env["account.asset.profile"].with_company(
            cls.company
        ).search([("company_id", "=", cls.company.id)])

    def _by_asset_code(self):
        return {
            profile.account_asset_id.code: profile for profile in self.profiles
        }

    def test_a_fresh_slovak_company_has_profiles(self):
        """The whole point: nothing to map to is what this module removes."""
        self.assertTrue(
            self.profiles,
            "a Slovak company with no asset profile cannot depreciate anything",
        )

    def test_every_profile_resolves_all_three_accounts(self):
        """A profile that exists but whose accounts are empty is worse than
        none: it satisfies the mapping and fails at the first depreciation."""
        for profile in self.profiles:
            self.assertTrue(profile.account_asset_id,
                            "%s has no asset account" % profile.name)
            self.assertTrue(profile.account_depreciation_id,
                            "%s has no depreciation account" % profile.name)
            self.assertTrue(profile.account_expense_depreciation_id,
                            "%s has no expense account" % profile.name)
            self.assertTrue(profile.journal_id,
                            "%s has no journal" % profile.name)

    def test_the_accounts_belong_to_this_company(self):
        for profile in self.profiles:
            for field in ("account_asset_id", "account_depreciation_id",
                          "account_expense_depreciation_id", "journal_id"):
                record = profile[field]
                self.assertIn(
                    self.company, record.company_ids
                    if "company_ids" in record._fields else record.company_id,
                    "%s.%s belongs to another company" % (profile.name, field),
                )

    def test_each_profile_pairs_with_its_own_opravky_account(self):
        """The pairing is the part that is not a matter of taste.

        Core l10n_sk's own asset CSV has this wrong in 19.0 — its asset-account
        column slipped a row, handing the herd model 029 and the other-tangible
        model 031, which is LAND. If somebody ever "fixes" this module to match
        upstream, this fails.
        """
        by_code = self._by_asset_code()
        for code, depreciation, _years, _name in SK_ASSET_PROFILES:
            profile = by_code.get(code)
            self.assertTrue(profile, "no profile for asset account %s" % code)
            self.assertEqual(
                profile.account_depreciation_id.code, depreciation,
                "%s must depreciate into %s" % (code, depreciation),
            )

    def test_land_and_art_have_no_profile(self):
        """Nothing on 031 or 032 is depreciated, so a profile would assert a
        useful life neither has."""
        by_code = self._by_asset_code()
        self.assertNotIn("031000", by_code, "land is not depreciated")
        self.assertNotIn("032000", by_code, "art is not depreciated")

    def test_no_profile_guesses_a_tax_group(self):
        """The account does not determine the odpisová skupina, and a wrong
        default here posts real numbers without saying anything."""
        for profile in self.profiles:
            self.assertFalse(
                profile.tax_class_id,
                "%s guesses a tax depreciation group" % profile.name,
            )
            self.assertFalse(profile.tax_depreciation_enabled)

    def test_the_expense_side_is_the_slovak_depreciation_account(self):
        for profile in self.profiles:
            self.assertEqual(
                profile.account_expense_depreciation_id.code, "551000",
                "%s does not post its depreciation to 551" % profile.name,
            )

    def test_an_asset_can_actually_be_created_from_one(self):
        """The end-to-end shape the importer needs.

        A profile is enough to make an asset, and the duration comes across.
        The accounts are NOT copied onto the asset — OCA keeps them on the
        profile and reads them when it posts — so the profile resolving (above)
        is what makes the posting work, and this only has to prove that an
        asset can be made at all.
        """
        profile = self._by_asset_code()["022000"]
        asset = self.env["account.asset"].with_company(self.company).create({
            "name": "Test machine",
            "profile_id": profile.id,
            "purchase_value": 12000.0,
            "date_start": "2026-01-01",
        })
        self.assertEqual(asset.profile_id, profile)
        self.assertEqual(asset.method_number, 6,
                         "the profile's duration must reach the asset")
        self.assertEqual(profile.account_depreciation_id.code, "082000")

    def test_a_company_that_had_its_chart_first_gets_them_once(self):
        """Installed after the chart, the module used to create nothing: the
        template only applies when the chart is LOADED. The hook gives them
        to the company, and running it again changes nothing."""
        from odoo.addons.l10n_sk_account_asset_profile.hooks import post_init_hook

        Profile = self.env["account.asset.profile"].with_company(self.company)
        data = self.env["ir.model.data"].search([
            ("model", "=", "account.asset.profile"),
            ("res_id", "in", self.profiles.ids)])
        self.profiles.unlink()
        data.unlink()
        self.assertFalse(Profile.search([("company_id", "=", self.company.id)]))

        post_init_hook(self.env)
        restored = Profile.search([("company_id", "=", self.company.id)])
        self.assertEqual(len(restored), len(SK_ASSET_PROFILES))

        restored[:1].method_number = 9
        post_init_hook(self.env)
        again = Profile.search([("company_id", "=", self.company.id)])
        self.assertEqual(again, restored, "idempotent")
        self.assertEqual(restored[:1].method_number, 9,
                         "an accountant's edit is not reverted")
