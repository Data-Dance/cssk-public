---
title: SK Management P&L (MIS Builder)
summary: A management profit-and-loss statement on the Slovak chart of accounts, delivered as an editable MIS Builder template for Odoo Community.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Odoo Enterprise has its own management reports; Community has none. This
module gives a Community database a **manažérska výsledovka** (management
P&L) for companies keeping their books on Odoo's Slovak chart of accounts. It
is a template for the OCA engine [module:mis_builder](module:mis_builder), so
periods, comparisons, budgets, PDF and XLSX export all come from that engine,
and the template itself can be changed by your controller.

It is a management view, **not** the statutory *Výkaz ziskov a strát*. The
statutory statements filed with the *účtovná závierka* are produced by
[module:l10n_sk_fs](module:l10n_sk_fs). The groupings here are chosen for
readability and do not follow the rows of the official form, so do not try to
reconcile the two line by line.

## What the report shows {#lines}

The template is called **Manažérska výsledovka (SK)**. It reads accounts of
classes 5 and 6 by their code prefix, so it needs no account tags:

| Line | Accounts | Sign |
|---|---|---|
| Tržby za tovar | 604 | revenue |
| Tržby za vlastné výrobky a služby | 601, 602, 606, 607 | revenue |
| Ostatné výnosy z hospodárskej činnosti | 61, 62, 64, 65 | revenue |
| **Výnosy spolu** | sum of the three above | |
| Predaný tovar | 504 | cost |
| Predané nehnuteľnosti na predaj | 507 | cost |
| Spotreba materiálu a energie | 501, 502, 503, 505 | cost |
| Služby | 51 | cost |
| Osobné náklady | 52 | cost |
| Dane a poplatky | 53 | cost |
| Odpisy dlhodobého majetku | 551 | cost |
| (pomocný riadok) trieda 54 a 55 vrátane odpisov | 54, 55 | cost |
| Ostatné náklady na hospodársku činnosť | 54 and 55 less 551 | cost |
| **Náklady spolu** | sum of the cost lines (the helper line is not counted) | |
| **Prevádzkový výsledok hospodárenia** | Výnosy spolu − Náklady spolu | |
| Finančné výnosy | 66 | revenue |
| Finančné náklady | 56 | cost |
| **Výsledok hospodárenia pred zdanením** | operating result + financial revenue − financial costs | |
| Daň z príjmov | 591, 592, 595 | cost |
| Prevod podielov na výsledku hospodárenia spoločníkom | 596 | cost |
| **Výsledok hospodárenia po zdanení** | result before tax − income tax − transfer of profit shares | |

Every figure is the **movement in the period** (the balance of the period, not
a cumulative balance). Revenue is turned round so that it reads as a positive
number, as do costs, and the subtotals add up the way a reader expects. Lines
in 61 (changes in own inventories) are revenue when they are credit; a decrease
in inventory makes that part of *Ostatné výnosy* negative.

The helper line *(pomocný riadok) trieda 54 a 55 vrátane odpisov* exists only
so that depreciation is not counted twice: 551 lies inside class 55. Its
style (*SK — pomocný (skrytý)*) hides it from the report.

## Running it {#usage}

1. Install the module. It needs the Slovak chart of accounts and
   [module:mis_builder](module:mis_builder).
2. Open *Účtovníctvo → Výkazy → MIS Reporting → MIS Reports* (the MIS Builder
   menus are in English) and click *New*.
3. Choose the template **Manažérska výsledovka (SK)** and the company.
4. Either pick a single period, or tick *Comparison Mode* and add columns on
   the *Columns* tab — for example each month of the year, or this year
   against last year.
5. Click **Preview**, **Print** (PDF) or **Export** (XLSX). Each figure can be
   opened to the journal items behind it.

By default only posted entries are counted (*Target Moves: All Posted
Entries*).

## Adjusting the template {#adjusting}

The template is at *Účtovníctvo → Konfigurácia → MIS Reporting → MIS Report
Templates*. Which accounts belong to which group is a management choice, and
it is meant to be agreed with your accountant — especially what goes into
*Ostatné náklady* rather than an operating group. Change the expressions there.

The template and its styles are loaded only once: your changes survive module
updates. A correction published in a later version of this module is applied
on update only to a line you have not changed.

One trap when adding lines: a line's technical name must not begin with an
accounting-expression prefix such as `bal`, `balp`, `crd` or `deb`. MIS Builder
rewrites those tokens as text, and every expression that refers to such a line
then shows `#ERR`. That is why the helper line is named `trieda_54_55`.

## Limitations {#limitations}

- Account groups are matched by code prefix. Accounts you add to the chart
  with other codes are not picked up until you add them to the template.
- This is not a cash-flow statement or forecast. A treasury forecast is
  provided by the OCA module [module:mis_builder_cash_flow](module:mis_builder_cash_flow); the statutory
  *Prehľad peňažných tokov* by [module:l10n_sk_fs](module:l10n_sk_fs).
