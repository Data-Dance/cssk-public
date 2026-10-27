---
title: Czechia — Peněžní deník (cash journal for daňová evidence)
summary: The Czech cash journal for daňová evidence — the categories Czech practice uses, the Czech chart mapped onto them, the peněžní deník PDF, the Příloha č. 1 figures including oddíl D, and the § 7b odst. 4 record.
verified: 19.0.1.0.5
---

## What it is for {#purpose}

The Czech half of the cash-journal family. The engine — how payments become
rows, generating, reviewing, printing — is described in
[the CZ/SK Cash Journal guide](module:l10n_cssk_cash_journal_base). This module
adds what is Czech:

- the **category catalogue** (*členění*) of the peněžní deník;
- the **mapping of the Czech chart of accounts** onto it;
- the **peněžní deník PDF**;
- the **figures for Příloha č. 1** of the personal income-tax return — ř. 101,
  ř. 102 and oddíl D — and the **record of the year-end stock-take** required
  by § 7b odst. 4.

It is meant for a sole trader keeping **daňová evidence** (tax records).

## Legal background {#legal}

- **No prescribed layout.** Daňová evidence contains income and expenses *„v
  členění potřebném pro zjištění základu daně“* and property and debts —
  [§ 7b odst. 1 of the Income Taxes Act](law:cz/1992/586). No regulation
  defines its columns, so the catalogue follows established Czech practice:
  taxable and non-taxable on both sides, průběžné položky, and a separate
  non-cash part for depreciation and tax-base adjustments. The term *peněžní
  deník* comes from single-entry accounting
  ([§ 13b of the Accounting Act](law:cz/1991/563)), which a sole trader cannot
  keep ([§ 1f](law:cz/1991/563)); the Slovak *jednoduché účtovníctvo* option is
  therefore refused for a Czech company.
- **The owner's own insurance is not deductible.** Social-security and
  health-insurance contributions paid by a taxpayer with income from
  self-employment cannot be claimed as an expense —
  [§ 25 odst. 1 písm. g) of the Income Taxes Act](law:cz/1992/586). Account
  526 is therefore mapped to a non-taxable category, unlike in Slovakia.
- **Year-end stock-take.** The taxpayer establishes the actual state of stock,
  tangible property, receivables and debts as at the last day of the tax
  period, makes a written record of it, and adjusts the tax base for any
  differences under §§ 24 and 25 —
  [§ 7b odst. 4 of the Income Taxes Act](law:cz/1992/586).

## Setting it up {#setup}

Install the module. It installs the shared engine, loads the catalogue and maps
the chart of every company whose country is the Czech Republic; a company that
loads the Czech chart later is mapped at that moment. Then continue with the
settings in [the shared guide](module:l10n_cssk_cash_journal_base#setup) — set
the regime to *Tax records (daňová evidence)*, choose the partial payment
allocation and, if you start mid-year, the start date.

The default mapping, by account prefix:

| Accounts | Category |
|---|---|
| 601, 602, 606, 607 | P2 Prodej výrobků a služeb |
| 604 | P1 Prodej zboží |
| 641–648, 661, 663, 665–668 | P3 Ostatní zdanitelný příjem |
| 662 (interest) | PN9 Ostatní nedaňový příjem |
| 501, 112 | V1 Materiál |
| 504, 132 | V2 Zboží |
| 502, 503, 511, 512, 518 | V6 Provozní režie a služby |
| 521–523 | V4 Mzdy |
| 524, 525 | V5 Odvody za zaměstnance |
| 526 | VN5 Pojistné podnikatele — non-deductible |
| 527, 528, 531, 532, 538, 544, 548, 562, 563, 568, 569 | V9 Ostatní daňový výdaj |
| 513, 543, 545, 549 | VN9 Ostatní nedaňový výdaj |
| 01x–04x | VN2 Nákup dlouhodobého majetku — the purchase is not an expense, the depreciation is |
| 551 | Z1 Odpisy (non-cash) |
| 591, 595 | VN4 Daň z příjmů |
| 343 | VN3 Odvod DPH out, PN3 Nadměrný odpočet in |
| 231, 461, 479 | VN6 Splátka úvěru out, PN2 Přijatý úvěr in |
| 491 | VN1 Osobní spotřeba out, PN1 Vklad podnikatele in |
| 261 | C1 Průběžné položky |

**Deliberately not mapped:** 311 and 321 (the engine follows them to the
invoice behind), 314 and 324 (advances — their column depends on what they are
for, so an unmatched advance is flagged for you), and accounts that never stand
behind a payment. *V3 Drobný majetek* and *Z2 Úprava základu daně* are not
mapped to any account; assign them where you need them.

## The categories {#categories}

| Code | Category | Affects the tax base |
|---|---|---|
| P1, P2, P3 | Prodej zboží, prodej výrobků a služeb, ostatní zdanitelný příjem | yes (ř. 101) |
| PN1, PN2, PN3, PN9 | Vklad podnikatele, přijatý úvěr, nadměrný odpočet DPH, ostatní | no |
| V1–V6, V9 | Materiál, zboží, drobný majetek, mzdy, odvody za zaměstnance, provozní režie a služby, ostatní | yes (ř. 102) |
| VN1–VN6, VN9 | Osobní spotřeba, nákup dlouhodobého majetku, odvod DPH, daň z příjmů, pojistné podnikatele, splátka úvěru, ostatní | no |
| C1 | Průběžné položky | — |
| Z1, Z2 | Odpisy, úprava základu daně (non-cash) | yes (ř. 102) |

The names stay in Czech in every language.

## The peněžní deník {#book}

*Accounting → Accounting → Cash Journal → Print*, output **PDF**, for a Czech
company prints the book with:

- **Pokladna**, **Banka**, **Průběžné položky** and **DPH**, each with a
  *příjem* and a *výdej* column, showing the gross amount that moved;
- the breakdown columns — Prodej zboží, Prodej výrobků a služeb, Ostatní
  zdanitelný příjem, Nedaňový příjem, Materiál, Zboží, Drobný majetek, Mzdy,
  Odvody za zaměstnance, Provozní režie a služby, Ostatní daňový výdaj,
  Nedaňový výdaj — net of VAT, a storno negative in its own column;
- **Zůstatek pokladna** and **Zůstatek banka** after every row, starting from
  the ledger balance on the day before the period.

A category of your own falls into *Ostatní zdanitelný příjem* / *Ostatní
daňový výdaj* or the matching non-taxable column; depreciation appears in
*Ostatní daňový výdaj*. The **Spreadsheet** output gives the flat row list and
the totals per category (no Czech grid sheet).

## Příloha č. 1 figures {#priloha}

*Accounting → Accounting → Cash Journal → Příloha č. 1 — údaje z deníku*:
choose the period (the current year by default) and click **Vypočítat**.

| Section | What is shown |
|---|---|
| Příloha č. 1 | **ř. 101** income and **ř. 102** expenses under § 7 — only rows that affect the tax base, depreciation and other non-cash rows included; **ř. 104** = ř. 101 − ř. 102 |
| Oddíl D | balances at the start and end of the period from the ledger: 1 hmotný majetek, 2 hotovost (211), 3 bankovní účty (221), 4 zásoby (class 1), 5 pohledávky (31x), 6 ostatní majetek, 7 dluhy (32x), 8 rezervy (45x), 9 mzdy (331); the last three as positive amounts |
| Kontrola | VAT in received and in paid payments; průběžné položky in − out |

Adjustments under §§ 5 and 23 that you do not post as entries belong on ř. 105
/ ř. 106 and are not computed here. If any row of the period needs review, a
warning says the figures are incomplete.

### Record of the stock-take (§ 7b odst. 4) {#zapis}

The **Zápis podle § 7b odst. 4** button prints *Zápis o zjištění skutečného
stavu*: the company, the date (the end of the chosen period), the oddíl D items
at the start and end of the period, and lines for date and signature. Choose
the period ending on the last day of the tax year.

The figures in it are the **book** balances. The law requires the actual state
to be established — count the stock, check the property, confirm receivables
and debts — and record any differences; use the printout as the form for that.

## Limitations {#limitations}

- The total at the foot of the value column adds unrelated rows; ignore it.
- The menu entry is visible in every company, Slovak ones included.
- Row numbers follow Příloha č. 1 as the module knows it; check them against
  the current year's form.
- The spreadsheet has no Czech grid sheet; use the PDF for the book layout.
