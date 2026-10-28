---
title: CZ Financial Statements (Rozvaha / VZZ)
summary: The Czech rozvaha, výkaz zisku a ztráty, přehled o peněžních tocích and přehled o změnách vlastního kapitálu computed from the ledger, ready to be filed with the corporate income tax return.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

The Czech country layer of the financial statements described in
[module:l10n_cssk_fs_base](module:l10n_cssk_fs_base). It installs six
statement versions, valid from 1 January 2025:

| Version | Statement |
|---|---|
| Rozvaha 2025 (plný rozsah) | balance sheet in full scope; assets in brutto / korekce / netto |
| Rozvaha 2025 (zkrácený rozsah) | balance sheet in abridged scope |
| Výkaz zisku a ztráty 2025 (plný rozsah) | income statement by nature (*druhové členění*), full scope |
| Výkaz zisku a ztráty 2025 (zkrácený rozsah) | the same in abridged scope |
| Přehled o peněžních tocích 2025 | cash flow statement, indirect method |
| Přehled o změnách vlastního kapitálu 2025 | statement of changes in equity |

Every account of the Czech chart of accounts reaches exactly one row, so
*AKTIVA CELKEM* equals *PASIVA CELKEM* and the result in the výkaz zisku a
ztráty equals revenue minus costs. The rozvaha and the výkaz zisku a ztráty
are what [module:l10n_cz_dppo](module:l10n_cz_dppo) files as the výkazy of the
corporate income tax return.

## Legal background {#legal}

- **Components.** The účetní závěrka consists of the rozvaha, the výkaz zisku
  a ztráty and the příloha; a commercial company also includes the přehled o
  peněžních tocích and the přehled o změnách vlastního kapitálu, which small
  and micro entities are not obliged to prepare —
  [§ 18 odst. 1 and 2 of the Accounting Act](law:cz/1991/563).
- **Full or abridged.** The závěrka is prepared in full or abridged scope
  (*plný* / *zkrácený rozsah*); an entity that is not obliged to have it
  audited may use the abridged scope —
  [§ 18 odst. 4 of the Accounting Act](law:cz/1991/563). The implementing
  [vyhláška č. 500/2002 Sb.](law:cz/2002/500) sets the layout: an abridged
  rozvaha of a small entity has the items marked with letters and Roman
  numerals, plus C.II.1–C.II.3; a micro entity's has the lettered items only
  ([§ 3a odst. 2](law:cz/2002/500)). A commercial company always prepares the
  výkaz zisku a ztráty in full scope; the abridged one (items marked with
  Roman numerals, letters and the computed items) is open only to small and
  micro entities that are not commercial companies and are not audited
  ([§ 3a odst. 3 and 4](law:cz/2002/500)). The order of items is in its
  příloha č. 1 (rozvaha) and č. 2 (výkaz zisku a ztráty, druhové členění).
- **Kind of závěrka.** A závěrka drawn up to the last day of the accounting
  period is *řádná*, otherwise *mimořádná* —
  [§ 19 odst. 1 of the Accounting Act](law:cz/1991/563).
- **Publication.** Entities entered in the public register publish the
  závěrka by depositing it in the collection of documents (*sbírka listin*) —
  [§ 21a of the Accounting Act](law:cz/1991/563).

## Setting it up {#setup}

Nothing is specific to this module beyond the
[framework setup](module:l10n_cssk_fs_base#setup). Two company fields are
needed for the export:

- *DIČ* (the company's tax number), required by every export;
- *Tax Authority* (finanční úřad), required as well when the Czech statutory
  module ([module:l10n_cz_statutory](module:l10n_cz_statutory)) is installed.

**Account tags for the full výkaz zisku a ztráty.** A few items of the full
scope cannot be told apart by account number, so they read an account tag
(*Accounting → Configuration → Chart of Accounts*, field *Tags*). Open an
analytic account for the flow and give it the tag:

| Tag | Item | Account |
|---|---|---|
| VZZ IV.1 | income from shares, controlled or controlling person | 665… |
| VZZ V.1 / V.2 | income from other long-term financial assets (bonds, loans), controlled person / other | 665… |
| VZZ VI.1 | interest income, controlled or controlling person | 662…, 666… |
| VZZ J.1 | interest expense, controlled or controlling person | 562… |
| VZZ E.1.2 | temporary impairment of intangible and tangible fixed assets | 559… |
| VZZ E.2 | impairment of inventories | 559… |

Untagged amounts go to IV.2, VI.2, J.2 and E.3 (and 558, the *zákonné
opravné položky*, which the law allows for receivables only, is always
E.3), so an entity without such flows needs no setup. An account can carry
only one of these tags.

## Preparing the statements {#usage}

*Accounting → Reporting → Statutory Reports → Balance sheet* (or *Income
statement*, *Cash flow statement*, *Statement of changes in equity*), *New*.
The matching 2025 version is preselected for a period from 2025 on — for
the rozvaha and the výkaz zisku a ztráty the **full scope**, which every
entity may use and every commercial company must use for the výkaz zisku a
ztráty. To prepare the abridged scope, pick the *(zkrácený rozsah)* version
in the *Version* field before computing. Click
**Compute** and review the tree as described in
[the framework guide](module:l10n_cssk_fs_base#review).

**What the rows contain:**

- **Rozvaha, full scope.** Every item of příloha č. 1, in its order, down to
  B.I.2.1. Software or C.II.2.4.3. Stát – daňové pohledávky. A few accounts
  are reported on the side their own balance dictates: an overdrawn bank
  account (221) under C.II.2. Závazky k úvěrovým institucím, a debit balance
  of 336 or 341–347 under C.II.2.4.2 / C.II.2.4.3, a credit balance of 373
  under C.II.8.7, a deferred tax asset (debit 481) under C.II.1.4. The chart
  has no long-term receivable accounts, so the C.II.1. items other than
  C.II.1.4 — and C.I.4., C.I.9.1., C.I.9.2. and the convertible bonds —
  are *manual* rows: zero until you enter an amount over them (remember to
  lower the short-term item by the same amount).
- **Rozvaha, abridged scope.** The items marked with letters and Roman
  numerals: A., B.I.–B.III.,
  C.I.–C.IV., D. on the assets side; A.I.–A.VI., B., C.I., C.II., D. on the
  liabilities side. Both scopes: assets carry *Brutto* and *Korekce* (oprávky and opravné
  položky). Accrued items are reported in D. Časové rozlišení aktiv / pasiv.
  **A.V. Výsledek hospodaření běžného účetního období** is the movement of
  classes 5 and 6 within the period — the same figure as the result in the
  výkaz zisku a ztráty — so the rozvaha balances before the year's result is
  closed to 431.
- **Výkaz zisku a ztráty, full scope.** Every item of příloha č. 2,
  including D.2.1–D.2.2 (524–526 / 527–528), E.1.1 (551, 557), and the items
  read from account tags described under [Setting it up](#setup).
- **Výkaz zisku a ztráty, abridged scope.** The lettered and Roman-numbered
  items with some of their sub-items (A.1–A.3, D.1–D.2, III.1–III.3, F.1–F.5,
  L.1–L.2), the computed results and *Čistý obrat za účetní období*. Account
  665 is reported entirely under IV.
- **Přehled o peněžních tocích.** Every non-cash account falls into
  operating (A), investing (B) or financing (C) activity, so A + B + C equals
  the change in cash between *P.* (start) and *R.* (end); row *G. Kontrola*
  shows any difference.
- **Přehled o změnách vlastního kapitálu.** Opening and closing equity and
  the year's movements by component; *Kontrola* shows any difference.

## Filing {#filing}

- **With the corporate income tax return.** Link the computed rozvaha and
  výkaz zisku a ztráty on the return in
  [module:l10n_cz_dppo](module:l10n_cz_dppo); it files them as the return's
  výkazy, in the scope of the linked statements. Both must be of the same
  scope.
- **Export XML** on a statement produces a structured file of the module's own
  design. No official schema exists for the Czech statements on their own, so
  the versions declare that and the file is exported without XSD validation.
  It is not a filing format; use the screen and the XLSX export
  ([module:l10n_cssk_fs_xlsx](module:l10n_cssk_fs_xlsx)) as working papers.
- The module produces no PDF of the statements for the *sbírka listin*.

## Limitations {#limitations}

- **Only the D. placement of accruals.** The decree lets an entity report
  accruals either in C.II.3. / C.III. or in D. ([§ 3 odst. 3 and
  4](law:cz/2002/500)); both scopes use D.
- **The abridged and full versions differ on a few accounts.** The abridged
  rozvaha reports 491 under A.IV. (the full one under A.I.1, as § 14 of the
  decree says) and reports 221, 336, 341–347, 373 and 481 net on one side
  only. Totals agree; prefer the full scope where those accounts matter.
- **The micro scope** (lettered items only) is not offered; a micro entity
  may use the abridged scope.
- **Earlier years' results must reach A.IV. through the books.** A.IV. reads
  426, 428, 429 and 431 (and 491 in the abridged scope). If a previous year was never closed — its result
  not carried to 431 by the year-end closing and the opening of the books —
  that result is on no row, and **AKTIVA and PASIVA differ by exactly that
  amount**. Post the closing and opening (or the transfer to 431) for that
  year rather than adjusting a row. Until version 19.0.1.1.1 A.V. read the
  cumulative balance of classes 5 and 6, which kept the totals equal by
  putting earlier years' results into A.V.
- C.II. Pohledávky is not split into long-term and short-term by the ledger
  (the chart has no accounts for it); enter long-term amounts over the manual
  C.II.1. rows of the full scope.
- Collective allowances (*opravné položky*) 091, 092, 095, 096 and 391 are
  shown with B.I.4, B.II.4.3, B.II.5.1, B.III.5 and C.II.2.1. If one relates
  to another item, discuss the presentation with your accountant.
- Statements can be created only from 2025; there is no earlier version.
- Off-balance-sheet accounts of class 7 belong on no statement; if they carry
  balances they can appear under *Unmapped accounts* and can be ignored there.
- The account mapping follows the standard Czech chart and must be reviewed
  with your accountant, especially the split of receivables and payables and
  the allocation of opravné položky.
