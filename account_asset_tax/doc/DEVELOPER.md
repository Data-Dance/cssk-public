# account_asset_tax: developer notes

Not user documentation: this file is not rendered into a page.

## Engine

All statutory maths lives in `engine/depreciation.py` with **no Odoo import**,
so it is unit-tested in isolation (`tests/test_engine.py`, runnable with plain
`python3`) and reused unchanged by both bridges, which differ only in *where*
they read the entry value and in-service date.

## Entry value hooks

The proposed tax entry price is `_tax_default_entry_value()` =
`_tax_get_entry_value()` (bridge: EE `original_value`, OCA `purchase_value`)
minus `_tax_entry_value_excluded()` (0 here). A country module overrides the
second on `account.asset.tax.mixin`: the bridges override only
`_tax_get_entry_value`, so an override on the mixin is reached.
`l10n_sk_account_asset_tax` uses it for § 52zzzk (the undeducted § 85n VAT
on a passenger vehicle), reading the asset's bill lines through the bridge
hook `_tax_source_move_lines()` and the tax there through
`account.move.line._tax_capitalised_tax_by_line()`: non-closing tax legs
booked on the base line's own account, which is also what the OCA bridge
adds to the purchase value and what the EE bridge restricts Odoo Assets'
`non_deductible_tax_value` to for CZ/SK companies.
