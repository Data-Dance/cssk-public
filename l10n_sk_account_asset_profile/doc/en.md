---
title: Slovakia — Starter Asset Profiles
summary: Ten ready-made asset profiles for a Slovak company, one per depreciable asset account of the chart, each posting to its own accumulated-depreciation account and to 551.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

In the Community asset register (OCA
[module:account_asset_management](module:account_asset_management)) every asset
needs an **asset profile**: it says which accounts the depreciation posts to
and over how long the asset is depreciated. A new Slovak company has all the
asset accounts in its chart but no profile, so the first asset — created by
hand or imported — has nothing to point to.

This module gives each Slovak company ten starter profiles, one for every
depreciable asset account of the Slovak chart of accounts. They cover
**accounting depreciation** (*účtovné odpisy*) only. Tax depreciation
(*daňové odpisy*) follows the statutory depreciation groups and is handled
separately by [module:account_asset_tax](module:account_asset_tax), which this
module installs with it.

## Legal background {#legal}

Under [§ 28 ods. 3 of the Accounting Act](law:sk/2002/431#paragraf-28.odsek-3)
the company must draw up its own depreciation plan (*odpisový plán*), and
under [§ 28 ods. 4](law:sk/2002/431#paragraf-28.odsek-4) it depreciates an
asset over its expected useful life; goodwill and capitalised development
costs whose useful life cannot be estimated reliably must be written off
within five years.
[§ 28 ods. 2](law:sk/2002/431#paragraf-28.odsek-2) says that land is not
depreciated.

The useful lives in these profiles are therefore **defaults for your
depreciation plan, not statutory values**. Review them against your internal
policy (*vnútorná smernica*) before the first asset is confirmed.

## The profiles {#profiles}

Each profile posts depreciation to **551000** (*Odpisy*) in the
miscellaneous operations journal, straight-line, one entry per month:

| Profile (name as shown) | Asset account | Accumulated depreciation | Years |
|---|---|---|---|
| Aktivované náklady na vývoj | 012000 | 072000 | 5 |
| Softvér | 013000 | 073000 | 4 |
| Oceniteľné práva | 014000 | 074000 | 5 |
| Goodwill | 015000 | 075000 | 5 |
| Ostatný dlhodobý nehmotný majetok | 019000 | 079000 | 5 |
| Stavby | 021000 | 081000 | 40 |
| Samostatné hnuteľné veci a súbory hnuteľných vecí | 022000 | 082000 | 6 |
| Pestovateľské celky trvalých porastov | 025000 | 085000 | 12 |
| Základné stádo a ťažné zvieratá | 026000 | 086000 | 4 |
| Ostatný dlhodobý hmotný majetok | 029000 | 089000 | 6 |

Profile settings: *Computation Method* Linear, *Time Method* Number of Years or end date,
*Period Length* Month, *Prorata Temporis* on. The first year therefore gets
only its share of the annual depreciation, from the asset's depreciation
start date to the year end — OCA counts that share in days — and not a whole
year's charge for an asset put into use in November. That matters twice for
intangible assets (012–019): under
[§ 22 ods. 8 of the Income Tax Act](law:sk/2003/595#paragraf-22.odsek-8)
their tax depreciation follows the accounting depreciation. Set the start
date to the first day of the month your plan starts depreciating in (the
month of putting into use, or the month after) to get whole months.

**031 Pozemky** (land) and **032 Umelecké diela a zbierky** (works of art and
collections) get no profile: nothing on them is depreciated, and a profile
would assert a useful life they do not have.

**No profile has a tax depreciation group.** *Track Tax Depreciation* is off
and *Tax Depreciation Group* is empty on every one, deliberately: the account
does not decide the group — a building may be group 5 or 6, a machine 1, 2
or 3 — and a wrong default would quietly produce wrong tax depreciation.

## Setting it up {#setup}

The profiles are created for every company using the Slovak chart of
accounts: when the chart is loaded, and on installation for companies that
already had it. A profile the company already has is never recreated or
overwritten, so your edits survive later upgrades. A company that has deleted
or renumbered one of the accounts the profiles use is skipped (the server log
records a warning) and has to create its profiles by hand.

After installation, in
*Invoicing → Configuration → Assets → Asset Profiles* (the root reads
*Accounting* where Odoo Enterprise Accounting is installed):

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

- The useful lives are common practice, not law, and the same for every
  company. They do not depend on the tax depreciation group.
- OCA pro-rates the first year **by days** from the depreciation start date,
  not by whole months: a start on 1 July gives 184/365 of the annual amount,
  not 6/12. Start on the first of a month and the difference is a few days'
  worth.
- Profiles created before version 19.0.1.2.0 keep the yearly, not pro-rated
  settings; change them by hand (step 1).
- Existing assets are not touched. Changing a profile later does not change
  assets already created from it.
- Community asset register only: the module requires
  [module:account_asset_tax_oca](module:account_asset_tax_oca) and so cannot be
  installed alongside Odoo Enterprise's `account_asset`. On Enterprise, Odoo's
  own Slovak chart ships asset models instead — and in Odoo 19.0 two of them
  point to the wrong asset account (*Základné stádo a ťažné zvieratá* to
  029000 and *Ostatný dlhodobý hmotný majetok* to 031000, land). This module
  pairs each profile with the asset account its accumulated-depreciation
  account belongs to; check those two models by hand on Enterprise.
