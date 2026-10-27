---
title: Slovakia — Peňažný denník (cash journal)
summary: The Slovak cash journal — the categories of opatrenie MF/27076/2007-74, the Slovak chart mapped onto them, the peňažný denník in its statutory layout, and the figures for DPFO typ B.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

The Slovak half of the cash-journal family. The engine — how payments become
rows, generating, reviewing, printing — is described in
[the CZ/SK Cash Journal guide](module:l10n_cssk_cash_journal_base). This module
adds what is Slovak:

- the **category catalogue** (*členenie*) of the statutory peňažný denník;
- the **mapping of the Slovak chart of accounts** onto those categories, so
  the first denník is usable without mapping forty accounts by hand;
- the **peňažný denník PDF** in the statutory column layout, and the same grid
  as the first sheet of the spreadsheet export;
- the **figures for the personal income-tax return** (*DPFO typ B*).

It serves both **jednoduché účtovníctvo** (single-entry accounting) and
**daňová evidencia** (tax records under the Income Tax Act).

## Legal background {#legal}

- **The columns.** For single-entry accounting, § 4 ods. 6 of the Ministry of
  Finance measure [MF/27076/2007-74](law:sk/2007/628) lists the overviews the
  peňažný denník contains: cash and bank, each split into income and expense;
  *priebežné položky*; income included in the tax base, broken down *„najmä
  na“* predaj tovaru, predaj výrobkov a služieb and ostatné príjmy; expenses,
  broken down into zásoby, služby, mzdy, poistné a príspevky, tvorba sociálneho
  fondu and ostatné výdavky; and income and expenses that do not affect the tax
  base. Under § 4 ods. 3, transfers between till and bank, between tills and
  between bank accounts are priebežné položky; under § 4 ods. 9 depreciation
  belongs in *ostatné výdavky*; and under § 4 ods. 10 the entries must tie to
  the balances of each bank account and each till.
- **Daňová evidencia.** The form is free, but income and tax expenses must be
  recorded *„v časovom slede v členení potrebnom na zistenie základu dane“* —
  [§ 6 ods. 11 of the Income Tax Act](law:sk/2003/595#paragraf-6.odsek-11).
  The same catalogue serves.
- **The owner's own insurance is a tax expense in Slovakia.** Insurance and
  contributions paid by a taxpayer with income under § 6 ods. 1 and 2 are a tax
  expense —
  [§ 19 ods. 3 písm. i)](law:sk/2003/595#paragraf-19.odsek-3.pismeno-i). This
  is the clearest difference from the Czech catalogue, where the same account
  is non-deductible.
- **Flat-rate expenses.** A taxpayer on paušálne výdavky keeps only the income
  records and the records of stock and receivables —
  [§ 6 ods. 10](law:sk/2003/595#paragraf-6.odsek-10).

## Setting it up {#setup}

Install the module. It installs the shared engine, loads the catalogue and maps
the chart of every company whose country is Slovakia. A company that loads the
Slovak chart later is mapped at that moment. Then continue with the settings
described in [the shared guide](module:l10n_cssk_cash_journal_base#setup) —
bookkeeping regime, partial payment allocation, start date.

The default mapping, by account prefix:

| Accounts | Category |
|---|---|
| 601, 602, 606, 607 | P2 Príjmy z predaja výrobkov a služieb |
| 604 | P1 Príjmy z predaja tovaru |
| 641–648, 661, 663, 665–668 | P3 Ostatné príjmy zahŕňané do základu dane |
| 662 (interest) | PN9 — taxed at source, outside the § 6 base |
| 501, 504, 507, 11x, 13x | V1 Zásoby |
| 502, 503, 511, 512, 518 | V2 Služby |
| 521–523 | V3 Mzdy |
| 524, 525 / 526 | V5 Poistné za zamestnancov / V4 Poistné podnikateľa |
| 527 | V6 Tvorba sociálneho fondu |
| 528, 531, 532, 538, 544, 548, 562, 563, 568, 569 | V9 Ostatné výdavky |
| 513, 543, 545, 549 | VN9 — representation, gifts, penalties, shortages: not a tax expense until you move what qualifies |
| 01x–04x | VN2 Nákup dlhodobého majetku — the purchase is not an expense, the depreciation is |
| 551 | Z1 Odpisy (non-cash) |
| 591, 595 | VN4 Daň z príjmov |
| 343 | VN3 Odvod DPH out, PN3 Nadmerný odpočet in |
| 231, 461, 479 | VN5 Splátka úveru out, PN2 Prijatý úver in |
| 491 | VN1 Osobná spotreba out, PN1 Vklad podnikateľa in |
| 261 | C1 Priebežné položky |

**Deliberately not mapped:** 311 and 321 (the engine follows them to the
invoice behind), 314 and 324 (advances — their column depends on what they are
for, so an unmatched advance is flagged for you), and internal or valuation
accounts that never stand behind a payment. *Z2 Úprava základu dane* is not
mapped to any account; assign it to the account you post tax-base adjustments to.

Check the mapping against your own chart and the accountant's view before the
first year-end; it is a starting point.

## The categories {#categories}

| Code | Category | Affects the tax base |
|---|---|---|
| P1, P2, P3 | Príjmy z predaja tovaru / výrobkov a služieb / ostatné | yes |
| PN1, PN2, PN3, PN9 | Vklad podnikateľa, prijatý úver, nadmerný odpočet DPH, ostatné | no |
| V1–V6, V9 | Zásoby, služby, mzdy, poistné podnikateľa, poistné zamestnávateľa, sociálny fond, ostatné | yes |
| VN1–VN5, VN9 | Osobná spotreba, nákup dlhodobého majetku, odvod DPH, daň z príjmov, splátka úveru, ostatné | no |
| C1 | Priebežné položky | — |
| Z1, Z2 | Odpisy, úprava základu dane (non-cash) | yes |

The names are the statute's own terms and stay in Slovak in every language.

## The peňažný denník {#book}

*Accounting → Accounting → Cash Journal → Print*, output **PDF**, for a Slovak
company prints the book in the statutory grid:

- **Pokladnica**, **Banka**, **Priebežné položky** and **DPH**, each with a
  *príjem* and a *výdaj* column, showing the gross amount that moved;
- the breakdown columns — Predaj tovaru, Predaj výrobkov a služieb, Ostatné
  príjmy, Príjmy neovplyvňujúce ZD, Zásoby, Služby, Mzdy, Poistné a príspevky,
  Sociálny fond, Ostatné výdavky, Výdavky neovplyvňujúce ZD — showing the
  amount net of VAT; a storno is negative in its own column;
- **Zostatok pokladnica** and **Zostatok banka** after every row, starting from
  the opening balance in the ledger the day before the period.

A category of your own falls into *Ostatné príjmy* / *Ostatné výdavky* or into
the matching non-taxable column. Non-cash rows (depreciation) appear only in
*Ostatné výdavky*. The bank balance includes Odoo's outstanding and suspense
accounts, so it is right both before and after bank statements are imported.

Choosing **Spreadsheet** gives the same grid as the first sheet,
*Peňažný denník*, followed by the flat row list and the totals per category.

## DPFO typ B figures {#dpfo}

*Accounting → Accounting → Cash Journal → DPFO typ B — údaje z denníka*:
choose the period (the current year by default) and click **Vypočítať**.

| Table | What is shown |
|---|---|
| Tabuľka 1 | r. 2 (and other § 6 rows if a category carries their code), each as two figures: stĺpec 1 príjmy and stĺpec 2 výdavky; **r. 10** príjmy spolu and výdavky spolu — only rows that affect the tax base, non-cash rows included; *Základ dane* = the difference |
| Tabuľka 1a (tax records) / 1b (flat-rate) | balances at the start and end of the period from the ledger: nehmotný majetok, hmotný majetok (net of accumulated depreciation), zásoby (class 1), pohľadávky (31x), záväzky (32x, as a positive amount), finančný majetok (21x, 22x, 25x, 26x). With the regime set to flat-rate expenses only zásoby and pohľadávky are shown, as tabuľka 1b. |
| Kontrola | VAT in received and in paid payments; priebežné položky in − out, which should be close to zero at year end |

If any row of the period needs review, a warning says the figures are
incomplete. The figures are for checking and typing into the return; no XML is
produced here.

## Limitations {#limitations}

- Every income and expense category is tagged as r. 2 (živnosť). A trader with
  income under another § 6 source cannot retag categories on screen — the tax
  return code is not shown on the category form.
- The total at the foot of the *Value* column adds unrelated rows; ignore it.
- The menu entry is visible in every company, Czech ones included.
- The row numbers and wording of the DPFO tables follow the form as the module
  knows it; check them against the current year's form.
- Kniha pohľadávok and kniha záväzkov required in single-entry accounting
  ([§ 15 ods. 1 of the Accounting Act](law:sk/2002/431#paragraf-15.odsek-1)) are not produced.
