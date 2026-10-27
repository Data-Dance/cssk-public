---
title: Asset Depreciation Board
summary: An interactive depreciation schedule and a pivot/graph analysis of accounting depreciation for the Community asset register (OCA account_asset_management).
verified: 19.0.1.0.2
---

## What it is for {#purpose}

The Community asset register, OCA
[module:account_asset_management](module:account_asset_management), keeps a
depreciation board per asset but offers only a static XLSX report across
assets. This module adds two screens for reviewing **accounting
depreciation** across the whole register:

- **Depreciation Schedule (dynamic)** — a movement schedule of fixed assets
  for any date range: acquisition value, accumulated depreciation at the
  start, depreciation in the period, disposals, accumulated depreciation at
  the end and the residual value, per asset and per asset profile.
- **Depreciation Analysis** — the depreciation lines in pivot and graph
  views, by asset, profile and year.

Both read the depreciation boards; they post nothing and change nothing. Tax
depreciation (*daňové odpisy*) is a separate, non-posted board with its own
reports — see [module:account_asset_tax](module:account_asset_tax).

## Setting it up {#setup}

Nothing to configure. Both screens appear under
*Invoicing → Assets* (*Accounting → Assets* where Odoo Enterprise Accounting
is installed)
only for users with the *Show Full Accounting Features* right
(`account.group_account_user`, granted on the user form); other users of the
asset register do not see them.

The figures are only as good as the boards behind them: an asset appears once
it is confirmed and its board is computed.

## Depreciation Schedule {#schedule}

*Assets → Depreciation Schedule (dynamic)*. Pick **From** and **To** at the
top; the default is the current fiscal year of the active company. The
schedule recalculates as soon as a date changes.

One row per asset, grouped by **asset profile** with a subtotal per profile
and a **Total** line. Click a profile row to fold or unfold it; click an asset
to open its form.

| Column | What it contains |
|---|---|
| Asset | Asset reference and name. |
| Acquisition Value | The asset's *Purchase Value*. |
| Opening Depreciated Value | Depreciation lines dated **before** *From*. Lines marked *Initial Balance Entry* (depreciation taken over from a previous system) count here. |
| + Depreciation | Depreciation lines dated from *From* to *To*. |
| Disposals / Decreases | For an asset removed in the period: the net book value that left the register — acquisition value − closing depreciated value. That is the residual written off by the removal wizard (*Remove*) plus any salvage value. |
| Closing Depreciated Value | Opening + depreciation in the period. |
| Residual at End | Acquisition value − closing depreciated value − disposals: the net book value at *To*, salvage value included; zero for an asset disposed of in the period. |

**Posted and planned lines are counted alike.** The schedule shows the
depreciation plan, not only what has reached the ledger: a period that has
not been posted yet still shows its planned depreciation. Use the analysis
below with the *Posted* filter to see what is actually booked.

Which assets are included: confirmed (*Running*), fully depreciated
(*Close*) and removed assets whose start date is on or before *To*. A removed
asset drops out once its removal date is before *From*. Draft assets are not
shown. A fully depreciated asset that is still held keeps appearing, with no
movement in the period.

## Depreciation Analysis {#analysis}

*Assets → Depreciation Analysis* opens the depreciation lines (only lines of
the *Depreciation* type, not the initial acquisition or removal lines, and
none of draft assets) in a
pivot view: assets in rows, years in columns, measure *Amount*. The graph view
shows the yearly depreciation as stacked bars.

Filters and groupings in the search panel:

- **Posted** — lines with a journal entry; **Planned** — lines not posted yet;
- group by **Asset**, **Asset Profile** or **Year**.

*Amount* is the only measure. OCA's *Next Period Depreciation* field, which
despite its label holds the remaining value after each line, is a balance:
summed over a year's lines it meant nothing, so it is not offered.

## Limitations {#limitations}

- The schedule reports **only the active company**, in its currency, even when
  several companies are selected. The analysis follows the usual multi-company
  selection and can mix companies.
- The schedule cannot be printed or exported; use the pivot view's export or
  OCA's *Financial Assets report* under *Reporting*.
- Accounting depreciation only. Tax depreciation and the difference between
  the two are reported by [module:account_asset_tax](module:account_asset_tax).
- Community engine only. Odoo Enterprise has its own depreciation schedule for
  its `account_asset` register.
