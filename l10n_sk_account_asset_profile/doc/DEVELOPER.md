# l10n_sk_account_asset_profile: developer notes

Not user documentation: this file is not rendered into a page.

## Do not fix to match upstream

Core contradicts itself: `account.account-sk.csv` links 026000 to the herd
model and 029000 to the other-tangible one, which is right. The pairs in this
module follow the oprávky accounts, each of which names the asset account it
belongs to. Do not "fix" them to match upstream — `test_each_profile_pairs_with_its_own_opravky_account` exists to catch that.
