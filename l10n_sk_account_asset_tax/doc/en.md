---
title: SK Tax Depreciation Groups
summary: The seven Slovak tax depreciation groups (odpisové skupiny 0–6) with their periods and accelerated coefficients, for the tax depreciation board.
verified: 19.0.1.0.3
---

## What it is for {#purpose}

Loads the Slovak statutory depreciation groups (*odpisové skupiny*) into the
tax depreciation module, [module:account_asset_tax](module:account_asset_tax).
With them, a Slovak company can put an asset into a group and have its tax
depreciation board (*daňové odpisy*) computed by the Slovak rules: monthly
pro-rating in the first year, the unclaimed remainder in the year after the
period, and accelerated depreciation for groups 2 and 3.

How the board is computed, and everything you do with it, is described in the
[tax depreciation guide](module:account_asset_tax#board).

## Legal background {#legal}

[Act No. 595/2003 Z. z. on income tax](law:sk/2003/595):

- the groups and periods are in
  [§ 26 ods. 1](law:sk/2003/595#paragraf-26.odsek-1); which group an asset
  belongs to is set by annex 1 to the act, by production classification;
- accelerated depreciation is allowed only in groups 2 and 3, and the method
  cannot change during the asset's depreciation —
  [§ 26 ods. 3](law:sk/2003/595#paragraf-26.odsek-3);
- straight-line annual charge = entry price ÷ period, with the first year
  pro-rated by months — [§ 27](law:sk/2003/595#paragraf-27.odsek-1);
- the accelerated coefficients —
  [§ 28 ods. 1](law:sk/2003/595#paragraf-28.odsek-1).

## The groups {#groups}

| Group | Period | Straight-line annual charge | Accelerated (§ 28) — first year / later years / increased residual |
|---|---|---|---|
| 0 | 2 years | 1/2 | — |
| 1 | 4 years | 1/4 | — |
| 2 | 6 years | 1/6 | 6 / 7 / 6 |
| 3 | 8 years | 1/8 | 8 / 9 / 8 |
| 4 | 12 years | 1/12 | — |
| 5 | 20 years | 1/20 | — |
| 6 | 40 years | 1/40 | — |

The records are named *Odpisová skupina 0* to *6* with codes `SK-0` to
`SK-6`, and appear in the asset's group field as, for example,
`SK-2 — Odpisová skupina 2 (6 y)`.

## Setting it up {#setup}

Install it with the tax depreciation module and a bridge to your asset
register ([module:account_asset_tax_oca](module:account_asset_tax_oca) on
Community, [module:account_asset_tax_ee](module:account_asset_tax_ee) on
Enterprise). It requires Odoo's Slovak localization (`l10n_sk`). There is
nothing to configure: the groups are visible under *Accounting →
Configuration → Tax Depreciation Groups*, and the asset form offers them to
companies whose country is Slovakia. The values are reloaded every time the
module is updated, so changes made by hand do not survive an update.

## Limitations {#limitations}

- Only the groups are loaded. Classifying an asset into a group is your
  decision; nothing suggests a group from the product or the account.
- No straight-line rates are stored: the board derives the annual charge from
  the period.
- Where the board departs from the act or does not cover it — the
  disposal year, cars from 48 000 €, the micro-taxpayer regime — is listed in
  the
  [tax depreciation guide](module:account_asset_tax#limitations).
