---
title: CZ Financial Statements (Rozvaha / VZZ)
summary: The Czech rozvaha, výkaz zisku a ztráty, přehled o peněžních tocích and přehled o změnách vlastního kapitálu computed from the ledger, ready to be filed with the corporate income tax return.
verified: 19.0.1.1.2
---

## What it is for {#purpose}

The Czech country layer of the financial statements described in
[module:l10n_cssk_fs_base](module:l10n_cssk_fs_base). It installs four
statement versions, valid from 1 January 2025:

| Version | Statement |
|---|---|
| Rozvaha 2025 | balance sheet; assets in brutto / korekce / netto |
| Výkaz zisku a ztráty 2025 | income statement by nature (*druhové členění*) |
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

## Preparing the statements {#usage}

*Accounting → Reporting → Statutory Reports → Balance sheet* (or *Income
statement*, *Cash flow statement*, *Statement of changes in equity*), *New*.
The matching 2025 version is preselected for a period from 2025 on. Click
**Compute** and review the tree as described in
[the framework guide](module:l10n_cssk_fs_base#review).

**What the rows contain:**

- **Rozvaha.** The items marked with letters and Roman numerals: A., B.I.–B.III.,
  C.I.–C.IV., D. on the assets side; A.I.–A.VI., B., C.I., C.II., D. on the
  liabilities side. Assets carry *Brutto* and *Korekce* (oprávky and opravné
  položky). Accrued items are reported in D. Časové rozlišení aktiv / pasiv.
  **A.V. Výsledek hospodaření běžného účetního období** is the movement of
  classes 5 and 6 within the period — the same figure as the result in the
  výkaz zisku a ztráty — so the rozvaha balances before the year's result is
  closed to 431.
- **Výkaz zisku a ztráty.** The lettered and Roman-numbered items with some of
  their sub-items (A.1–A.3, D.1–D.2, III.1–III.3, F.1–F.5, L.1–L.2), the
  computed results and *Čistý obrat za účetní období*.
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
  výkazy.
- **Export XML** on a statement produces a structured file of the module's own
  design. No official schema exists for the Czech statements on their own, so
  the versions declare that and the file is exported without XSD validation.
  It is not a filing format; use the screen and the XLSX export
  ([module:l10n_cssk_fs_xlsx](module:l10n_cssk_fs_xlsx)) as working papers.
- The module produces no PDF of the statements for the *sbírka listin*.

## Limitations {#limitations}

- **Scope.** The rozvaha covers the items of the abridged scope; the výkaz
  zisku a ztráty is neither the full nor exactly the abridged scope: it lacks
  item **V. Výnosy z ostatního dlouhodobého finančního majetku** (account 665
  is reported under IV.) and the sub-items D.2.1–D.2.2, E.1–E.3, IV.1–IV.2,
  V.1–V.2, VI.1–VI.2 and J.1–J.2. A commercial company, or an entity obliged to file the full scope,
  has to complete the missing items outside Odoo.
- **Earlier years' results must reach A.IV. through the books.** A.IV. reads
  426, 428, 429, 431 and 491. If a previous year was never closed — its result
  not carried to 431 by the year-end closing and the opening of the books —
  that result is on no row, and **AKTIVA and PASIVA differ by exactly that
  amount**. Post the closing and opening (or the transfer to 431) for that
  year rather than adjusting a row. Until version 19.0.1.1.1 A.V. read the
  cumulative balance of classes 5 and 6, which kept the totals equal by
  putting earlier years' results into A.V.
- C.II. Pohledávky is not split into long-term and short-term.
- Statements can be created only from 2025; there is no earlier version.
- Off-balance-sheet accounts of class 7 belong on no statement; if they carry
  balances they can appear under *Unmapped accounts* and can be ignored there.
- The account mapping follows the standard Czech chart and must be reviewed
  with your accountant, especially the split of receivables and payables and
  the allocation of opravné položky.
