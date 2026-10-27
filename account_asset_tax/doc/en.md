---
title: Tax Depreciation (CZ/SK)
summary: A second, never-posted depreciation board per asset for Czech and Slovak tax depreciation, next to the accounting depreciation, with the year-end book-versus-tax reconciliation, deferred tax and a tax depreciation register.
verified: 19.0.1.11.0
---

## What it is for {#purpose}

Czech and Slovak companies depreciate every fixed asset **twice**:

- **Accounting depreciation** (*účtovné odpisy* / *účetní odpisy*) follows the
  company's own depreciation plan and is posted to the ledger (account 551).
- **Tax depreciation** (*daňové odpisy*) follows the depreciation groups and
  methods of the income tax act. It is **never posted**: it is what the tax
  return deducts instead of the accounting depreciation, so the difference
  between the two adjusts the income tax base.

Odoo's asset registers — Enterprise *Assets* and the OCA
`account_asset_management` register used on Community — keep only the first.
This module adds the second: a tax depreciation board on each asset, computed
from the statutory rules, plus the year-end tools that turn the two boards into
figures for the tax return.

It works as a family. Install:

| Module | What it brings |
|---|---|
| this module | the calculation, the depreciation groups model, the wizards and reports |
| **one** asset bridge: [module:account_asset_tax_oca](module:account_asset_tax_oca) (Community, OCA register) or [module:account_asset_tax_ee](module:account_asset_tax_ee) (Enterprise *Assets*) | the *Tax Depreciation* tab on the asset form; see [Community](#oca) and [Enterprise](#ee) |
| the country data: [module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) and/or [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax) | the statutory depreciation groups with their periods, rates and coefficients |

On its own this module does nothing visible on assets; it needs a bridge.

## Legal background {#legal}

Statutory terms are given in Slovak and Czech, as in the acts.

**Slovakia** — [Act No. 595/2003 Z. z. on income tax](law:sk/2003/595):

- **Depreciation groups and periods** (*odpisové skupiny*, *doba odpisovania*):
  seven groups, 0 to 6, from 2 to 40 years —
  [§ 26 ods. 1](law:sk/2003/595#paragraf-26.odsek-1).
- **Method.** Straight-line (*rovnomerné*) for all groups; accelerated
  (*zrýchlené*) only for groups 2 and 3. The method is chosen for each newly
  acquired asset and *"nemožno ho zmeniť po celú dobu jeho odpisovania"* —
  [§ 26 ods. 3](law:sk/2003/595#paragraf-26.odsek-3).
- **Straight-line**: the annual charge is the entry price divided by the
  period; in the first year only the part for the months from the month of
  putting into use, and the unclaimed part is claimed in the year after the
  period ends — [§ 27 ods. 1 and 2](law:sk/2003/595#paragraf-27.odsek-2).
- **Accelerated**: coefficients 6/7/6 (group 2) and 8/9/8 (group 3), a
  pro-rated first year, and a second-year residual computed as if the full
  first-year charge had been taken —
  [§ 28 ods. 1 and 2](law:sk/2003/595#paragraf-28.odsek-2); after a technical
  improvement [§ 28 ods. 3](law:sk/2003/595#paragraf-28.odsek-3).
- **Technical improvement** (*technické zhodnotenie*) and the longer period it
  brings — [§ 26 ods. 5](law:sk/2003/595#paragraf-26.odsek-5).
- **Interruption** (*prerušenie odpisovania*) for whole tax periods, after
  which depreciation continues as if uninterrupted and the period is
  extended — [§ 22 ods. 9](law:sk/2003/595#paragraf-22.odsek-9).
- **Disposal.** The annual charge can be claimed only for an asset still on
  the books on the last day of the tax period —
  [§ 22 ods. 11](law:sk/2003/595#paragraf-22.odsek-11) — so the year of
  disposal carries no tax depreciation and the residual tax value is an
  expense under
  [§ 19 ods. 3 písm. b)](law:sk/2003/595#paragraf-19.odsek-3.pismeno-b)
  (for passenger cars and the other assets in its first point, only up to the
  sale proceeds). A charge for the whole months held is kept only for the
  assets named in [§ 22 ods. 12](law:sk/2003/595#paragraf-22.odsek-12):
  those depreciated under § 26 ods. 6 and 7, and — since 2016, if the
  taxpayer chooses — those whose residual is capped at the sale proceeds.
- **Passenger cars from 48 000 €**: the tax base is increased by the
  difference over straight-line depreciation of a 48 000 € car, but only when
  the base falls below a threshold —
  [§ 17 ods. 34](law:sk/2003/595#paragraf-17.odsek-34). The depreciation itself
  is not capped.
- Calculations are rounded to the cent —
  [§ 47](law:sk/2003/595#paragraf-47).

**Czech Republic** — [Act No. 586/1992 Sb. on income taxes](law:cz/1992/586):

- **Depreciation groups and minimum periods**: six groups, 1 to 6, from 3 to
  50 years (§ 30 odst. 1); straight-line (§ 31) or accelerated (§ 32), chosen
  for each newly acquired asset and not changeable for its whole life
  (§ 30 odst. 2).
- **Straight-line** (*rovnoměrné*): a first-year rate and a rate for further
  years, both of the entry price, with no pro-rating by months; higher
  first-year rates (+10, +15, +20 %) in § 31 odst. 1 písm. b) to d) for the
  cases in § 31 odst. 2 to 4; a rate for the increased entry price after a
  technical improvement (§ 31 odst. 8).
- **Accelerated** (*zrychlené*): entry price ÷ coefficient in the first year,
  then twice the residual ÷ (coefficient − years already depreciated)
  (§ 32 odst. 2); a first depreciator may add 20, 15 or 10 % of the entry
  price to the first year in the same cases as the straight-line increase
  (§ 32 odst. 2 písm. a)); after a technical improvement, the coefficient for the
  increased residual (§ 32 odst. 3).
- **Extraordinary depreciation** (*mimořádné odpisy*) of emission-free
  vehicles acquired from 1 January 2024 to 31 December 2028 by their first
  depreciator: 60 % in the first 12 months and 40 % in the next 12, in whole
  months starting the month after the conditions are met (§ 30a).
- **Disposal**: only half of the annual charge in the year of disposal, and
  only for an asset held at the start of the period (§ 26 odst. 7); an asset
  put into use and disposed of in the same year gets none.
- **Interruption** allowed, continuing as if uninterrupted (§ 26 odst. 8).
- **M1 passenger vehicles**: only the share of each depreciation that
  2 000 000 Kč bears to the entry price is deductible (§ 30e).
- Charges are rounded **up to whole crowns** (§ 31 odst. 9, § 32 odst. 5,
  § 30a odst. 2).

Accounting depreciation is governed separately, by the accounting acts:
[§ 28 ods. 1 of Act No. 431/2002 Z. z.](law:sk/2002/431#paragraf-28.odsek-1)
and [§ 28 of Act No. 563/1991 Sb.](law:cz/1991/563) — each company depreciates
under its own accounting methods. That plan is the asset register's
depreciation board, which this module leaves untouched.

## Setting it up {#setup}

1. Install this module, the bridge for your edition and the country data
   module. The groups appear under *Accounting → Configuration → Tax
   Depreciation Groups*.
2. **Company settings**, on the company form (*Settings → Companies*), next
   to the currency — only needed for the features named:

   | Field | Used for |
   |---|---|
   | Tax Vehicle Depreciation Cap | The statutory vehicle limit for assets ticked *Apply Vehicle Depreciation Cap*, in company currency: 2 000 000 Kč for a Czech company, 48 000 € for a Slovak one. 0 = no limit. See the field of the same name on the asset for what each country does with it. |
   | Deferred Tax Journal | The miscellaneous journal for the deferred-tax entry from the [reconciliation](#reconciliation). |
   | Deferred Tax Account (481) | The balance-sheet deferred-tax account. Use one that holds only the deferred tax on depreciation (for example an analytical 481 sub-account): the reconciliation trues its whole balance up. |
   | Deferred Tax P&L Account (592) | The profit-and-loss deferred-tax account. |

3. **Defaults per asset category.** Set *Track Tax Depreciation*, the group,
   the method and (CZ) the increased first-year rate on the asset profile
   (Community) or the asset model (Enterprise); new assets created from it
   inherit them. See the bridge sections below.

The menus of this family are visible to accounting **Administrators**
only. Menu paths on this page start at *Accounting*; on Community, without
Enterprise accounting, the same root menu is called *Invoicing*.

## Depreciation groups {#groups}

*Accounting → Configuration → Tax Depreciation Groups* lists the statutory
groups loaded by the country modules. Each group holds:

- **Country**, **Group** number, **Depreciation Period (years)**;
- the methods it allows — *Allows Straight-line*, *Allows Accelerated*,
  *Allows Extraordinary (CZ §30a)*;
- Czech straight-line rates (first year, further years, increased price) and
  the accelerated coefficients (first year, further years, increased
  residual).

The values come from the acts and are reloaded when the country module is
updated, so do not edit them to suit one asset. The tables are on the pages of
[module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) and
[module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax).

Which group an asset belongs to depends on what it is (the annex to each act
classifies assets by production classification), not on its account. Choosing
it is the accountant's decision.

## Setting up an asset {#usage}

Open the asset and the **Tax Depreciation** tab:

| Field | Meaning |
|---|---|
| Track Tax Depreciation | Keep a tax board for this asset. |
| Tax Depreciation Group | Only the groups of the company's country are offered. |
| Tax Method | Straight-line, accelerated, or (CZ group 2) extraordinary — only methods the group allows are accepted. |
| Increased First-Year Rate | CZ, straight-line or accelerated, groups 1–3, first depreciator only: +10 % for any such asset, +15 % only for the water-treatment and recycling equipment of § 31 odst. 3, +20 % only for agricultural and forestry machines of a mainly agricultural taxpayer (§ 31 odst. 2); never for the assets in § 31 odst. 5. The field's help lists the conditions. Straight-line uses the higher first-year rate table, accelerated adds the percentage of the entry price to the first-year charge. Refused outside Czech groups 1–3. |
| Tax Method Locked | Ticked automatically when the first year is filed (see [Closing a tax year](#year-close)); the method and group can then no longer be changed. |
| Tax Entry Value | The tax entry price (*vstupná cena* / *vstupní cena*). Filled from the accounting acquisition value when tracking is switched on; change it where the tax price differs. |
| Apply Vehicle Depreciation Cap | A passenger vehicle under the company's *Tax Vehicle Depreciation Cap*. **CZ** (§ 30e): the board is computed on the limit, which is the deductible share of each depreciation. **SK** (§ 17 ods. 34): the board keeps the full depreciation and its hidden *Vehicle Add-back (SK §17(34))* column shows, per year, the excess over straight-line depreciation of 48 000 € — see [Year-end reconciliation](#reconciliation). |
| Depreciate Whole Months in Disposal Year | SK only (§ 22 ods. 12): keep the depreciation for the whole months held in the year of disposal. Tick it for assets depreciated under § 26 ods. 6 and 7 and, if you choose, for assets whose residual is deductible only up to the sale proceeds (passenger cars, boats, aircraft, motorcycles, group-6 buildings sold …). Unticked, the year of disposal carries no depreciation. |
| Tax In-Service Date | The date of putting into use for tax purposes. Empty = the accounting depreciation start date. |
| Tax Depreciated / Tax Residual Value | The sum of filed board lines, and the sum of the board lines not yet filed. |

Then click **Compute Tax Board**. The board is recomputed from these fields
every time; years already filed are kept as they are.

To recompute many assets at once, select them in the asset list and choose
*Action → Compute Tax Depreciation*, or run
*Accounting → Configuration → Compute Tax Depreciation* for every asset that
tracks tax depreciation. Filed years are kept here too.

## The tax depreciation board {#board}

One line per tax year (per month for Czech extraordinary depreciation), with
the year's tax depreciation, the cumulative amount, the tax residual value, a
note on how the line was computed and the *Filed* flag. Two more columns line
the accounting depreciation of the same calendar year up against it:
**Book Depreciation** and **Difference (Book − Tax)**. These count all
accounting depreciation lines of the year, posted or planned. On a monthly
(§ 30a) board the year's accounting figures appear once, on the year's last
line.

How the lines are computed:

| | Slovakia | Czech Republic |
|---|---|---|
| Straight-line, first year | annual charge × months from the month of putting into use ÷ 12 | full first-year rate, whatever the month |
| Straight-line, later years | entry price ÷ period | further-years rate |
| Unclaimed first-year part | an extra line in the year after the period ends | — |
| Accelerated | § 28: pro-rated first year, later years from the un-pro-rated residual | § 32: entry price ÷ k₁ (+ the elected 10/15/20 % of the entry price), then 2 × residual ÷ (k − n) |
| Extraordinary | — | § 30a: 24 monthly lines from the month after putting into use, 60 % then 40 % |

Examples:

- **SK**, machine, group 1 (4 years), entry price 12 000 €, put into use in
  October: 750 € (3/12), then 3 000 € for three years, then 2 250 € in the
  fifth year.
- **CZ**, machine, group 2, straight-line, 300 000 Kč: 33 000 Kč (11 %),
  then 66 750 Kč (22.25 %) for four years.

Czech charges are rounded up to whole crowns, and the next year's residual
is what the rounded charges leave. The last line of every board is adjusted
so the board adds up exactly to the depreciable base; on a § 30a board the
twelfth month also stops at 60 %.

## Technical improvement, interruption, disposal {#events}

Events change the board from a date on. Record them with the buttons under
**Lifecycle Events** on the tab — *Technical Improvement*, *Suspension*,
*Disposal* — and enter the date (and the amount, or the number of years). The
board is recomputed at once and the event is kept, so every later
recomputation replays it.

- **Technical improvement**: from its year, the board continues from the
  increased price — CZ straight-line at the increased-price rate, SK
  straight-line at increased price ÷ period, accelerated at the increased
  residual coefficient. The *Tax Entry Value* field keeps the original price;
  the increase lives in the event.
- **Suspension**: the chosen years get a zero line and the rest of the board
  moves out by as many years.
- **Disposal**: the board stops. CZ: half the annual charge in the year of
  disposal, rounded up — none if the asset was put into use that same year.
  SK: no depreciation in the year of disposal, so the whole remaining tax
  residual is the § 19 ods. 3 písm. b) expense; with *Depreciate Whole Months
  in Disposal Year* ticked, the annual charge × whole months held ÷ 12 (the
  month of disposal does not count). Disposing of the asset in the
  register itself records this event automatically (OCA *Remove*, Enterprise
  *Dispose* / *Sell*).

Refused: an event dated in or before the last filed year, a technical
improvement of a § 30a asset (it is depreciated as a separate asset,
§ 30a odst. 3 — create a new asset), and a suspension of a § 30a asset.

## Assets already being depreciated {#migration}

For an asset whose tax depreciation started before Odoo, click
**Backfill (migration)** on the tab. Enter the group, method, tax entry value,
tax in-service date and **Filed Through Fiscal Year** — the last year already
claimed in a filed return. Optionally enter **Expected Tax Residual** from your
previous records: if the computed residual at the end of that year differs,
nothing is written and the wizard tells you so. The check replays the
lifecycle events already recorded on the asset, exactly as the board will.

When the difference is a technical improvement or suspension not recorded
yet, record it as an event and run the wizard again. An event cannot be
recorded inside a year that is already filed; for an asset with filed years,
first run the wizard without an expected residual and with *Filed Through
Fiscal Year* set to the year before the event, record the event, then run
the wizard again with the real filed year and the expected residual.

The wizard computes the full statutory board, marks every year up to the
filed year as filed and locks the method. It is also the sanctioned way to
correct the tax parameters of an asset whose filed years are frozen.

## Closing a tax year {#year-close}

When the income tax return for a year has been filed, run
*Accounting → Configuration → Close Tax Depreciation Year*, choose the year
(default: last year) and click **File Year**. On every tax-tracked asset of
the company, all board lines up to and including that year are marked
**Filed** and the method is locked.

From then on:

- recomputing the board never changes a filed line — if a changed parameter
  would, the computation is refused;
- the tax entry value, in-service date, increased first-year rate and vehicle
  cap cannot be changed;
- filed lines cannot be edited.

The *Backfill (migration)* wizard is the only way to reopen filed years.

## Year-end reconciliation and deferred tax {#reconciliation}

*Accounting → Reporting → Tax Depreciation Reconciliation*. Choose the period
(default: the current calendar year), check the **Income Tax Rate (%)**
(default 21) and click **Compute**. One line per tax-tracked asset:

| Column | Content |
|---|---|
| Accounting Depreciation | posted accounting depreciation in the period |
| Tax Depreciation | tax board lines starting in the period |
| Add-back | accounting − tax, when positive |
| Deduction | tax − accounting, when positive |
| Accounting NBV, Tax Residual (hidden by default) | the two residual values at period end |
| Temporary Difference | accounting NBV − tax residual |
| Deferred Tax | temporary difference × rate: positive = liability, negative = asset |
| Vehicle Add-back (SK §17(34)) (hidden by default) | for Slovak cars ticked *Apply Vehicle Depreciation Cap*: the period's depreciation above straight-line depreciation of 48 000 € |

The return rows follow the company's country and are shown next to the totals
and in the PDF and XLSX headings: **Slovakia** r. 150 (pripočítateľná) and
r. 250 (odpočítateľná položka), **Czech Republic** ř. 50 (účetní odpisy
převyšují daňové) and ř. 150 (daňové převyšují účetní).

The **vehicle add-back** is kept out of the add-back column on purpose: § 17
ods. 34 adds it to the tax base only when that base is lower than the number
of such cars × the annual straight-line depreciation of 48 000 €, and a lessor
of a car leased without a purchase option never adds it. Whether it applies
is decided on the return; the wizard shows the amount.

From the wizard:

- **Post Deferred Tax (draft)** creates an entry in the *Deferred Tax
  Journal*, dated at period end, that brings the posted balance of account
  481 **at the period end** to the computed deferred tax, against 592.
  Entries dated after the period are left out. It stays in draft unless
  *Post Deferred Tax Immediately* is ticked.
- **Export XLSX** and **Print PDF** give the table as a spreadsheet or a PDF.

The Slovak corporate tax return in
[module:l10n_sk_dppo](module:l10n_sk_dppo) reads rows 150 and 250 from this
module automatically (not the vehicle add-back, which you enter yourself
when it applies). It takes the **company total** — accounting minus tax
for all assets together — whereas the wizard shows add-backs and deductions
asset by asset, so the two differ when some assets go one way and some the
other. The Czech return module does not read these figures.

## Register and analysis {#register}

- **Tax Depreciation Register** (*Accounting → Reporting*): choose the year
  and click **Print register**. A PDF grouped by depreciation group: entry
  price, opening residual, the year's depreciation, accumulated depreciation,
  closing residual, method, and the accounting depreciation with the
  difference, with group subtotals and a total. An asset on a monthly
  (§ 30a) board appears once, with the year's months added up. Its headings
  are in Slovak and English.
- **Book vs Tax Depreciation** (*Accounting → Reporting*): pivot, graph and
  list of accounting against tax depreciation per asset and year, by group.
  *Book Depreciation* counts every accounting depreciation line of the year,
  *Book Depreciation (Posted)* only those already posted; *Filed* filters the
  years that are frozen.

## On Community — the OCA register {#oca}

[module:account_asset_tax_oca](module:account_asset_tax_oca) attaches the tax
board to the OCA `account_asset_management` register:

- the **Tax Depreciation** tab on the asset form; entry value = the asset's
  purchase value, in-service date = its depreciation start date;
- a **Tax Depreciation Defaults** block on the asset profile (*Track Tax
  Depreciation*, group, method, increased first-year rate), copied to assets
  created with that profile unless they set their own group;
- removing the asset with the register's *Remove* wizard records the tax
  disposal on the removal date;
- book depreciation = the register's depreciation lines (posted = those with
  a journal entry);
- it also relabels the register's *Number of Years* field on the asset form as
  *Number of years* or *Number of periods*, depending on the time method, and
  shows the period length next to it.

[module:l10n_sk_account_asset_profile](module:l10n_sk_account_asset_profile)
builds on it with ready-made Slovak asset profiles.

## On Enterprise — Odoo Assets {#ee}

[module:account_asset_tax_ee](module:account_asset_tax_ee) attaches the tax
board to Odoo Enterprise *Assets*:

- the **Tax Depreciation** tab after the depreciation board; entry value = the
  asset's original value, in-service date = its first depreciation date
  (falling back to the acquisition date);
- tax defaults set on an **asset model** are copied to assets created from it
  unless they set their own group;
- disposing of or selling the asset records the tax disposal on the disposal
  date;
- book depreciation = the asset's depreciation entries (posted = posted
  entries; cancelled ones are ignored).

Only one bridge can be installed, because only one of the two asset registers
can be.

## Limitations {#limitations}

- **Boards filed before version 19.0.1.10.0 keep their old figures.** Up to
  that version the board rounded Czech charges to the haléř, gave every
  Slovak asset a pro-rated charge in the year of disposal, capped Slovak cars
  from 48 000 € at that amount and gave a Czech asset disposed of in its
  first year half a charge. Filed years are frozen, so recomputing such an
  asset is refused; correct it with *Backfill (migration)* if the filed
  figures were wrong. Unfiled years are corrected by **Compute Tax Board**.
- **§ 30a rounding** is applied to each monthly charge (rounded up, the
  twelfth month stopping at 60 % in whole crowns). § 30a odst. 2 does not say
  whether the round-up applies per month or per tax period; the year's total
  can differ from a per-year round-up by a few crowns.
- *Depreciate Whole Months in Disposal Year* is not checked against the
  asset: whether it is a § 26 ods. 6–7 asset or one whose residual is capped
  at the sale proceeds, and the 2016 start of the second case, are yours to
  confirm. The month of disposal is never counted as a whole month.
- The Slovak **vehicle add-back** compares the depreciation with
  straight-line depreciation of 48 000 € year by year in order; after a
  technical improvement that lengthens the period, the extra years are added
  back in full. Whether the add-back applies at all is not evaluated.
- **Eligibility is not checked**: Odoo cannot see whether you are the first
  depreciator (§ 31 odst. 6) or whether the asset is one of those that may
  take +15 % or +20 % (§ 31 odst. 2 and 3) or none at all (§ 31 odst. 5), so
  every Czech group 1–3 asset offers all three increases; the conditions are
  yours to confirm. So are the § 30a conditions (emission-free, acquired
  2024–2028, first depreciator).
- A technical improvement completed in the first year is handled as an event,
  not added to the entry price; enter it in the *Tax Entry Value* instead if
  that is what your accountant prefers.
- Not covered: intangible assets, the Slovak micro-taxpayer regime
  (§ 26 ods. 12), assets depreciated over a set period or output (SK § 26
  ods. 6–7, CZ § 30 odst. 4–5), lower-than-maximum Czech rates, mandatory
  interruptions (the module does not know when an asset was unused), and the
  depreciation thresholds (1 700 € / 80 000 Kč) — whether an asset is
  depreciated for tax at all is your decision.
- The reconciliation compares depreciation only. The difference between the
  accounting and tax residual value of a disposed asset is not computed.
- The deferred-tax entry trues up the **whole posted balance** of the 481
  account at the period end against the depreciation difference alone. Use
  it only if that account carries nothing else.
- Years are calendar years: a company with a fiscal year other than the
  calendar year gets calendar-year boards.
- The register's headings are Slovak/English also for Czech companies.
