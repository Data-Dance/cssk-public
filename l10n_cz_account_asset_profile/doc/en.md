---
title: Czech Republic — Starter Asset Profiles
summary: Ten ready-made asset profiles for a Czech company, one per depreciable asset account of the chart, each posting to its own accumulated-depreciation account and to 551.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

In the Community asset register (OCA
[module:account_asset_management](module:account_asset_management)) every asset
needs an **asset profile**: it says which accounts the depreciation posts to
and over how long the asset is depreciated. A new Czech company has all the
asset accounts in its chart but no profile, so the first asset — created by
hand or imported — has nothing to point to.

This module gives each Czech company ten starter profiles, one for every
depreciable asset account of the Czech chart of accounts. They cover
**accounting depreciation** (*účetní odpisy*) only. Tax depreciation
(*daňové odpisy*) follows the statutory depreciation groups and is handled
separately by [module:account_asset_tax](module:account_asset_tax), which this
module installs with it; the Czech groups themselves come from
[module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax).

## Legal background {#legal}

Under [§ 28 odst. 6 of the Accounting Act](law:cz/1991/563) the company must
draw up its own depreciation plan (*odpisový plán*) and depreciate an asset
in the course of its use, up to its carrying value. The implementing
[vyhláška č. 500/2002 Sb.](law:cz/2002/500) adds:

- § 56 odst. 2: where the useful life of goodwill or of development results
  cannot be estimated, the company chooses a period of 60 to 120 months;
- § 6 odst. 3 písm. c): goodwill is written off evenly within 60 months at
  the latest;
- § 56 odst. 11: land, works of art and collections, emission allowances and
  preferential limits are **not depreciated**.

The useful lives in these profiles are therefore **defaults for your
depreciation plan, not statutory values**. Review them against your internal
policy (*vnitřní směrnice*) before the first asset is confirmed.

## The profiles {#profiles}

Each profile posts depreciation to **551000** (*Odpisy dlouhodobého
nehmotného a hmotného majetku*) in the miscellaneous operations journal,
straight-line, one entry per month:

| Profile (name as shown) | Asset account | Accumulated depreciation | Years |
|---|---|---|---|
| Nehmotné výsledky vývoje | 012000 | 072000 | 5 |
| Software | 013000 | 073000 | 3 |
| Ostatní ocenitelná práva | 014000 | 074000 | 6 |
| Goodwill | 015000 | 075000 | 5 |
| Ostatní dlouhodobý nehmotný majetek | 019000 | 079000 | 5 |
| Stavby | 021000 | 081000 | 30 |
| Hmotné movité věci a jejich soubory | 022000 | 082000 | 5 |
| Pěstitelské celky trvalých porostů | 025000 | 085000 | 10 |
| Dospělá zvířata a jejich skupiny | 026000 | 086000 | 5 |
| Jiný dlouhodobý hmotný majetek | 029000 | 089000 | 5 |

Profile settings: *Computation Method* Linear, *Time Method* Number of Years or end date,
*Period Length* Month, *Prorata Temporis* on. The first year therefore gets
only its share of the annual depreciation, from the asset's depreciation
start date to the year end — OCA counts that share in days — and not a whole
year's charge for an asset put into use in November. That matters twice for
intangible assets (012–019) acquired from 2021: the Income Tax Act no longer
has tax depreciation of intangibles, so their accounting depreciation is what
reaches the tax base. Set the start date to the first day of the month your
plan starts depreciating in (the month of putting into use, or the month
after) to get whole months.

No profile is created for:

- **031 Pozemky**, **032 Umělecká díla a sbírky**, **016 Povolenky na emise**
  and **017 Preferenční limity**: nothing on them is depreciated, and a
  profile would assert a useful life they do not have;
- **027 Oceňovací rozdíl k nabytému majetku**: it is depreciated (evenly
  over 180 months, § 7 odst. 10 of the vyhláška), but it arises only when a
  business is acquired and posts to 557, not 551. Create its profile by hand
  when you need it.

**No profile has a tax depreciation group.** *Track Tax Depreciation* is off
and *Tax Depreciation Group* is empty on every one, deliberately: the account
does not decide the group — a building may be group 4, 5 or 6, a movable
thing 1, 2 or 3 — and a wrong default would quietly produce wrong tax
depreciation.

## Setting it up {#setup}

The profiles are created for every company using the Czech chart of
accounts: when the chart is loaded, and on installation for companies that
already had it. A profile the company already has is never recreated or
overwritten, so your edits survive later upgrades. A company that has deleted
or renumbered one of the accounts the profiles use is skipped (the server log
records a warning) and has to create its profiles by hand.

After installation, in
*Invoicing → Configuration → Assets → Asset Profiles*:

1. **Adjust the useful lives** to your depreciation plan. Change *Period
   Length* to *Year* if you post depreciation once a year; keep *Prorata
   Temporis* on unless your plan really charges a whole year in the first
   year.
2. **For profiles whose assets all fall into one depreciation group**, tick
   *Track Tax Depreciation* and pick the *Tax Depreciation Group*. Assets
   created from the profile afterwards take the group with them (see
   [module:account_asset_tax](module:account_asset_tax#oca)). Otherwise leave
   it empty and set the group on each asset.
3. Create further profiles where one account holds assets with very different
   useful lives (for example several profiles on 022000).

## Limitations {#limitations}

- The useful lives are defaults, not law, and the same for every company.
  They do not depend on the tax depreciation group.
- OCA pro-rates the first year **by days** from the depreciation start date,
  not by whole months: a start on 1 July gives 184/365 of the annual amount,
  not 6/12. Start on the first of a month and the difference is a few days'
  worth.
- Existing assets are not touched. Changing a profile later does not change
  assets already created from it.
- Community asset register only: the module requires
  [module:account_asset_tax_oca](module:account_asset_tax_oca) and so cannot be
  installed alongside Odoo Enterprise's `account_asset`.
