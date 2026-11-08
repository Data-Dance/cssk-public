# l10n_cssk_recycling_fee: developer notes

Not user documentation: this file is not rendered into a page.

## Why an OCA base

`account_ecotax` (Akretion, AGPL-3, on OCA 19.0) already has what is not
country-specific: a classification per tariff line (fixed or weight based,
household/professional, category, sector, collector), several classifications
per product and per variant, a sub-line per document line holding the fee, the
sale-order side (`account_ecotax_sale`) including the SO → invoice hand-over,
and the "fee included in the price" model. Rebuilding that would duplicate a
maintained OCA module for no gain.

Consequence to be aware of: the module sits on third-party AGPL code, so it can
only ever be distributed under AGPL — it cannot be dual-licensed into the
proprietary Enterprise line the way a module we wholly own can.
