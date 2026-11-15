---
title: CZ Management P&L (MIS Builder)
summary: A management profit-and-loss statement on the Czech chart of accounts, delivered as an editable MIS Builder template for Odoo Community.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Odoo Enterprise has its own management reports; Community has none. This
module gives a Community database a **manažerská výsledovka** (management
P&L) for companies keeping their books on Odoo's Czech chart of accounts. It
is a template for the OCA engine [module:mis_builder](module:mis_builder), so
periods, comparisons, budgets, PDF and XLSX export all come from that engine,
and the template itself can be changed by your controller.

It is a management view, **not** the statutory *Výkaz zisku a ztráty*. The
statutory statements of the *účetní závěrka* are produced by
[module:l10n_cz_fs](module:l10n_cz_fs). The groupings here are chosen for
readability and do not follow the rows of the official statement, so do not
try to reconcile the two line by line. The two results do agree: *Výsledek
hospodaření před zdaněním* and *po zdanění* are the same figures in both.

## What the report shows {#lines}

The template is called **Manažerská výsledovka (CZ)**. It reads accounts of
classes 5 and 6 by their code prefix, so it needs no account tags:

| Line | Accounts | Sign |
|---|---|---|
| Tržby za zboží | 604 | revenue |
| Tržby z prodeje výrobků a služeb | 601, 602 | revenue |
| Ostatní provozní výnosy | 64, 697, 699 | revenue |
| **Provozní výnosy celkem** | sum of the three above | |
| Prodané zboží | 504 | cost |
| Spotřeba materiálu a energie | 501, 502, 503 | cost |
| Služby | 51 | cost |
| Změna stavu zásob vlastní činnosti a aktivace | 58 | cost |
| Osobní náklady | 52 | cost |
| Daně a poplatky | 53 | cost |
| Odpisy dlouhodobého majetku | 551 | cost |
| (pomocný řádek) skupiny 54 a 55 včetně odpisů a účet 597 | 54, 55, 597 | cost |
| Ostatní provozní náklady | 54, 55 and 597 less 551 | cost |
| **Provozní náklady celkem** | sum of the cost lines (the helper line is not counted) | |
| **Provozní výsledek hospodaření** | Provozní výnosy celkem − Provozní náklady celkem | |
| Finanční výnosy | 66, 698 | revenue |
| Finanční náklady | 56, 57, 598 | cost |
| **Výsledek hospodaření před zdaněním** | operating result + financial revenue − financial costs | |
| Daň z příjmů | 591, 592, 593, 595, 599 | cost |
| Převod podílu na výsledku hospodaření společníkům | 596 | cost |
| **Výsledek hospodaření po zdanění** | result before tax − income tax − transfer of profit shares | |

Every figure is the **movement in the period** (the balance of the period, not
a cumulative balance). Revenue is turned round so that it reads as a positive
number, as do costs, and the subtotals add up the way a reader expects.

*Změna stavu zásob vlastní činnosti a aktivace* is a cost line, because the
Czech chart books both in group 58 as an adjustment of costs. Capitalised
own work (*aktivace*) is a credit there, so the line is normally negative and
lowers the operating costs; a decrease in own inventories makes it positive.

The helper line *(pomocný řádek) skupiny 54 a 55 včetně odpisů a účet 597*
exists only so that depreciation is not counted twice: 551 lies inside group
55. Its style (*CZ — pomocný (skrytý)*) hides it from the report.

## Running it {#usage}

1. Install the module. It needs the Czech chart of accounts and
   [module:mis_builder](module:mis_builder).
2. Open *Účetnictví → Výkazy → Výkaznictví MIS → Výkazy MIS* and click
   *Nové*.
3. Choose the template **Manažerská výsledovka (CZ)** and the company.
4. Either pick a single period, or switch on the comparison mode and add
   columns: for example each month of the year, or this year against last
   year.
5. Preview the report, print it (PDF) or export it (XLSX). Each figure can be
   opened to the journal items behind it.

By default only posted entries are counted.

## Adjusting the template {#adjusting}

The template is under *Účetnictví → Konfigurace → Výkaznictví MIS*. Which
accounts belong to which group is a management choice, and it is meant to be
agreed with your accountant, especially what goes into *Ostatní provozní
náklady* rather than an operating group. Change the expressions there.

The template and its styles are loaded only once: your changes survive module
updates.

One trap when adding lines: a line's technical name must not begin with an
accounting-expression prefix such as `bal`, `balp`, `crd` or `deb`. MIS Builder
rewrites those tokens as text, and every expression that refers to such a line
then shows `#ERR`. That is why the helper line is named `trida_54_55`.

## Limitations {#limitations}

- Account groups are matched by code prefix. Accounts you add to the chart
  with other codes are not picked up until you add them to the template.
- This is not a cash-flow statement or forecast. A treasury forecast is
  provided by the OCA module [module:mis_builder_cash_flow](module:mis_builder_cash_flow); the statutory
  *Přehled o peněžních tocích* by [module:l10n_cz_fs](module:l10n_cz_fs).
