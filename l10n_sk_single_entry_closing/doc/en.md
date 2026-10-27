---
title: SK Single-Entry Financial Statements (Úč FO)
summary: The účtovná závierka of a Slovak self-employed person keeping single-entry books — the výkaz o príjmoch a výdavkoch from the cash journal and the výkaz o majetku a záväzkoch from the ledger, exported as the official UZFOv14 file.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

A Slovak sole trader (*SZČO*) who keeps **jednoduché účtovníctvo**
(single-entry bookkeeping) closes the year with an **účtovná závierka** of two
statements, filed as one electronic document (XML vzor *UZFOv14*):

| Statement | Form | Read from |
|---|---|---|
| Výkaz o príjmoch a výdavkoch (income and expenditure) | Úč FO 1-01, rows 01–12 | the peňažný denník (cash journal) |
| Výkaz o majetku a záväzkoch (assets and liabilities) | Úč FO 2-01, rows 01–21, current and preceding period | account balances at the period end |

The module builds this document on the shared framework described in
[module:l10n_cssk_fs_base](module:l10n_cssk_fs_base), so computing, checking,
entering figures by hand, exporting and recording the filing work the same way
as for any other statement. The income side is read from the cash journal of
[module:l10n_sk_cash_journal](module:l10n_sk_cash_journal), not rebuilt from the
ledger.

A person keeping **daňová evidencia** or claiming flat-rate expenses is not an
accounting entity and files no závierka; this module is not for them.

## Legal background {#legal}

All references are to the [Accounting Act](law:sk/2002/431).

- **Who.** The act applies to natural persons doing business who prove their
  expenses for income tax purposes, except those keeping daňová evidencia —
  [§ 1 ods. 1 písm. a) bod 3](law:sk/2002/431#paragraf-1.odsek-1.pismeno-a.bod-3).
- **Components.** An účtovná závierka in single-entry bookkeeping consists of
  the výkaz o príjmoch a výdavkoch and the výkaz o majetku a záväzkoch —
  [§ 17 ods. 4](law:sk/2002/431#paragraf-17.odsek-4).
- **Form.** The layout is set by opatrenie MF SR č. MF/27076/2007-74 for
  entities in single-entry bookkeeping, as amended; the module produces its
  electronic form *UZFOv14*. The size groups (mikro / malá / veľká) apply only
  to entities in double-entry bookkeeping —
  [§ 2 ods. 5](law:sk/2002/431#paragraf-2.odsek-5) — so there is one form for
  every size.
- **Filing.** The závierka is deposited in the register of financial
  statements — [§ 23a ods. 3](law:sk/2002/431#paragraf-23a.odsek-3) —
  through the portal of the Finančné riaditeľstvo —
  [§ 23b ods. 1](law:sk/2002/431#paragraf-23b.odsek-1).

## Setting it up {#setup}

1. **Keep the cash journal.** The categories of the peňažný denník are what
   Úč FO 1-01 reads; set them up and generate the journal for the year as
   described in [the cash journal guide](module:l10n_cssk_cash_journal_base#usage).
2. **Company data for the header**: the DIČ (the *DIČ* field of
   [module:l10n_sk_base](module:l10n_sk_base); without it the *Tax ID* with
   its `SK` prefix removed — the export refuses to run with neither),
   *Company ID* (IČO), name, address — the house number at the end of
   *Street* (*Hlavná 12*) — phone and e-mail, and the SK NACE code when
   [module:partner_nace](module:partner_nace) is installed.

## Preparing the závierka {#usage}

*Accounting → Accounting → Cash Journal → Účtovná závierka v JÚ (Úč FO)*,
then *New*. The version *Účtovná závierka v jednoduchom účtovníctve
(UZFOv14)* is preselected, the period defaults to the last completed year.

- **First závierka in JÚ** leaves the preceding-period column of Úč FO 2-01
  empty. It is ticked automatically when the books hold no posted entry before
  the period; tick it yourself if you kept double-entry books in the
  preceding period, which the books cannot tell.

Click **Compute**.

**Úč FO 1-01 — from the cash journal.** Each row adds up the journal rows of
its categories for the period, as the categories carry them (a refund reduces
its own category):

| Row | Categories |
|---|---|
| 01 Predaj tovaru | P1 |
| 02 Predaj výrobkov a služieb | P2 |
| 03 Ostatné príjmy | P3 |
| 05 Zásoby | V1 |
| 06 Služby | V2 |
| 07 Mzdy | V3 |
| 08 Platby poistného a príspevkov | V4, V5 |
| 09 Tvorba sociálneho fondu | V6 |
| 10 Ostatné výdavky | V9, Z1 (depreciation), Z2 (tax-base adjustments) |

Depreciation and the other non-cash rows of the cash journal count as well:
they are its year-end closing operations, which § 8 ods. 4 písm. a) of the
opatrenie adds to the expenses, and § 4 ods. 9 names odpisy among the
ostatné výdavky.

Rows 04, 11 and 12 are the totals and the difference. Income and expenses
that do not affect the tax base (the PN and VN categories — owner's deposits,
loan instalments, VAT paid) are not on this statement; they show only in the
balances of Úč FO 2-01.

**Úč FO 2-01 — from the ledger.** Balances at the period end by account group:
long-term assets (rows 01–03), inventories (04–07), receivables (08),
short-term financial assets (09–13), the acquired-asset adjustment (14, 19),
reserves (16), liabilities (17) and loans (18). A bank account in overdraft is
reported as a loan. Row 21 is assets minus liabilities.

Deposits and loans with a long maturity are reported where their account group
puts them; move them with a manual figure (the framework records who entered
it).

The statement also appears in the *Income statement* list under *Statutory
Reports*, showing only its Úč FO 1-01 rows; the Cash Journal menu shows the
whole document.

## Checks and export {#export}

- **Unmapped accounts** lists only asset and liability accounts no row
  claims. Classes 5 and 6 (the result is reported from the cash journal),
  equity (row 21 is the owner's equity), classes 7 and 9 and off-balance
  accounts are left out on purpose.
- **Export XML** produces the UZFOv14 document in **whole euros**, with an
  empty element where a figure is absent, and validates it against the
  official schema `form.300.sk.xsd`. The file is named *Účtovná závierka v JÚ
  (Úč FO) — date*. The signature is not part of the XML; it is given on paper.

Submit the file on the Finančná správa portal and record it with **Mark
Submitted** (see [the framework guide](module:l10n_cssk_fs_base#filing)).

## Limitations {#limitations}

- The kind of závierka (*Druh závierky (Úč FO)* on the statement:
  riadna, mimoriadna or priebežná) is yours to set; it defaults to riadna.
  The date of compilation is the day of the export. Without a NACE code the
  optional SK NACE element is left out.
- Maturity is not read from the accounts: long-term deposits and loans need a
  manual figure.
- Nothing is submitted from Odoo.
