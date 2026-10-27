---
title: CZ Tax Depreciation Groups
summary: The six Czech tax depreciation groups (odpisové skupiny 1–6) with their straight-line rates, accelerated coefficients and the § 30a extraordinary regime, for the tax depreciation board.
verified: 19.0.1.0.3
---

## What it is for {#purpose}

Loads the Czech statutory depreciation groups (*odpisové skupiny*) into the
tax depreciation module, [module:account_asset_tax](module:account_asset_tax).
With them, a Czech company can put an asset into a group and have its tax
depreciation board (*daňové odpisy*) computed by the Czech rules: the full
first-year rate whatever the month of putting into use, the higher first-year
rates, accelerated depreciation in every group, and extraordinary
depreciation of emission-free vehicles in group 2.

How the board is computed, and everything you do with it, is described in the
[tax depreciation guide](module:account_asset_tax#board).

## Legal background {#legal}

[Act No. 586/1992 Sb. on income taxes](law:cz/1992/586):

- § 30 odst. 1 — the groups and minimum depreciation periods; which group an
  asset belongs to is set by annex 1 to the act;
- § 30 odst. 2 — straight-line or accelerated, chosen for each newly acquired
  asset and not changeable for its whole depreciation;
- § 31 odst. 1 — the maximum straight-line rates, including the higher
  first-year rates of písm. b) to d);
- § 32 odst. 1 — the accelerated coefficients;
- § 30a — extraordinary depreciation of emission-free vehicles acquired from
  1 January 2024 to 31 December 2028 by their first depreciator: 60 % and
  40 % over 24 months.

## The groups {#groups}

| Group | Minimum period | Straight-line rate — first year / later years / increased entry price (%) | Accelerated coefficient — first year / later years / increased residual | Extraordinary (§ 30a) |
|---|---|---|---|---|
| 1 | 3 years | 20 / 40 / 33.3 | 3 / 4 / 3 | — |
| 2 | 5 years | 11 / 22.25 / 20 | 5 / 6 / 5 | allowed |
| 3 | 10 years | 5.5 / 10.5 / 10 | 10 / 11 / 10 | — |
| 4 | 20 years | 2.15 / 5.15 / 5.0 | 20 / 21 / 20 | — |
| 5 | 30 years | 1.4 / 3.4 / 3.4 | 30 / 31 / 30 | — |
| 6 | 50 years | 1.02 / 2.02 / 2.0 | 50 / 51 / 50 | — |

The higher first-year straight-line rates (§ 31 odst. 1 písm. b) to d)), for
groups 1–3, are part of the calculation and chosen on the asset as
*Increased First-Year Rate*:

| Increase | Group 1 | Group 2 | Group 3 |
|---|---|---|---|
| +10 % | 30 / 35 | 21 / 19.75 | 15.4 / 9.4 |
| +15 % | 35 / 32.5 | 26 / 18.5 | 19 / 9 |
| +20 % | 40 / 30 | 31 / 17.25 | 24.4 / 8.4 |

(first year / later years, % of the entry price)

The records are named *Odpisová skupina 1* to *6* with codes `CZ-1` to
`CZ-6`, and appear in the asset's group field as, for example,
`CZ-2 — Odpisová skupina 2 (5 y)`.

## Setting it up {#setup}

Install it with the tax depreciation module and a bridge to your asset
register ([module:account_asset_tax_oca](module:account_asset_tax_oca) on
Community, [module:account_asset_tax_ee](module:account_asset_tax_ee) on
Enterprise). It requires Odoo's Czech localization (`l10n_cz`). There is
nothing to configure: the groups are visible under *Accounting →
Configuration → Tax Depreciation Groups*, and the asset form offers them to
companies whose country is the Czech Republic. The values are reloaded every
time the module is updated, so changes made by hand do not survive an update.

## Limitations {#limitations}

- Only the groups are loaded. Classifying an asset into a group is your
  decision; nothing suggests a group from the product or the account.
- The +20 % rate belongs only to agricultural and forestry machinery of a
  predominantly agricultural taxpayer, the +15 % rate only to the equipment
  named in § 31 odst. 3, and all three only to first depreciators; nothing
  checks this.
- Extraordinary depreciation is enabled on group 2 only, as the group of road
  vehicles; whether a vehicle is emission-free and qualifies is yours to
  confirm.
- The board rounds to the haléř, not up to whole crowns as the act requires;
  this and the other deviations are listed in the
  [tax depreciation guide](module:account_asset_tax#limitations).
