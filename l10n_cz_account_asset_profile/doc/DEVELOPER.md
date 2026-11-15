# l10n_cz_account_asset_profile: developer notes

Not user documentation: this file is not rendered into a page.

## Twin

Same shape as `l10n_sk_account_asset_profile`. Differences that are the law's
or the chart's, not ours:

- Core `l10n_cz` ships no asset models of its own (the Slovak chart does, with
  two wrong rows the Slovak module documents), so there is no upstream pairing
  to disagree with.
- 016 and 017 exist only on the Czech chart and are not depreciated.
- 027 / 097 / 098 (oceňovací rozdíl k nabytému majetku) is depreciated to 557
  over 180 months; left out of the starter set on purpose.

A test compares the profiles with every 01x / 02x account of the chart, so a
depreciable account added upstream fails the suite until it is either given a
profile or added to the list of accounts left out.
