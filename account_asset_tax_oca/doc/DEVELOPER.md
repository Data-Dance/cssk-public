# account_asset_tax_oca: developer notes

Not user documentation: this file is not rendered into a page.

## Implementation

Wires the country-neutral `account_asset_tax` core onto OCA
`account_asset_management` (Community): the non-posted tax-depreciation board,
the asset ↔ tax-line/event relations, the *Tax Depreciation* page, the
removal-wizard disposal hook (`state='removed'`), the deferred-tax
accounting-residual reader, and tax-default inheritance from the asset profile.
