---
title: SK Financial Statements (Úč POD)
summary: The Slovak účtovná závierka of an entrepreneur in double-entry bookkeeping — the súvaha and the výkaz ziskov a strát computed from the ledger and exported as the official UZPODv14 file, plus the cash flow and equity statements and the notes.
verified: 19.0.1.7.2
---

## What it is for {#purpose}

A Slovak company keeping double-entry books (*podvojné účtovníctvo*) closes
every year with an **účtovná závierka**. For small and large entities its
statements are filed as one electronic document, **Účtovná závierka Úč POD**
(XML vzor *UZPODv14*), which holds:

- the **súvaha** (balance sheet, *Úč POD 1-01*, rows 001–145, assets in
  brutto / korekcia / netto columns), and
- the **výkaz ziskov a strát** (income statement by nature, *Úč POD 2-01*,
  rows 01–61).

This module provides that document on the shared framework described in
[module:l10n_cssk_fs_base](module:l10n_cssk_fs_base) — computed from the
journal items, checked, exported and validated against the official schema of
the Finančná správa. It adds:

- a **Prehľad peňažných tokov** (cash flow statement, indirect method) and a
  **Prehľad zmien vlastného imania** (statement of changes in equity), as
  working statements;
- the **Poznámky** (notes), as a form with standard texts that produces a PDF;
- a **filing record** for the Úč POD with its corrective filings.

## Legal background {#legal}

All references are to the [Accounting Act](law:sk/2002/431).

- **Components.** An účtovná závierka in double-entry bookkeeping consists of
  the súvaha, the výkaz ziskov a strát and the poznámky —
  [§ 17 ods. 3](law:sk/2002/431#paragraf-17.odsek-3). Both statements show
  the current and the immediately preceding period —
  [§ 18 ods. 3 and 4](law:sk/2002/431#paragraf-18.odsek-3).
- **Size groups.** Companies are sorted into *mikro*, *malá* and *veľká
  účtovná jednotka* by total assets, net turnover and average headcount —
  [§ 2 ods. 5 to 8](law:sk/2002/431#paragraf-2.odsek-5). The Úč POD header
  states *malá* or *veľká*; a micro entity files a different form
  (*Úč MÚJ*), which this module does not produce.
- **Layout.** The arrangement and content of the statements are set by
  measures (*opatrenia*) of the Ministry of Finance —
  [§ 4 ods. 2](law:sk/2002/431#paragraf-4.odsek-2): for small entities
  opatrenie č. MF/23378/2014-74, for large entities and public-interest
  entities opatrenie č. MF/23377/2014-74. The notes template of this module
  follows the one for small entities.
- **Kind of závierka.** A závierka drawn up when the books are closed on the
  last day of the accounting period is *riadna*, on any other closing
  *mimoriadna* — [§ 17 ods. 6](law:sk/2002/431#paragraf-17.odsek-6); a
  *priebežná* závierka is drawn up during the period where a special
  regulation requires it — [§ 18 ods. 1](law:sk/2002/431#paragraf-18.odsek-1).
- **Filing.** The riadna and mimoriadna závierka are deposited in the register
  of financial statements within six months of the date they are drawn up to,
  unless a special regulation provides otherwise —
  [§ 23a ods. 3](law:sk/2002/431#paragraf-23a.odsek-3) — and are delivered
  electronically through the portal of the Finančné riaditeľstvo —
  [§ 23b ods. 1](law:sk/2002/431#paragraf-23b.odsek-1).

## Setting it up {#setup}

The Úč POD header is read from the company. Check, on the company and its
contact:

| Data | Field |
|---|---|
| DIČ | *DIČ* (with the Slovak base module installed), otherwise the *Tax ID*; an `SK` prefix is removed |
| IČO | *Company ID* |
| SK NACE | *NACE (main activity)* on the company's contact |
| Name, address, phone, e-mail | the company's contact |
| Commercial register entry | *Trade Registry* |

**Related-party split of financial income and costs (optional).** Rows IX, X,
XI and N of the výkaz ziskov a strát separate amounts with *prepojené účtovné
jednotky* and with participating interests from the rest. No account code
tells them apart, so the module installs six account tags
(*VZS IX.1 …*, *VZS IX.2 …*, *VZS X.1 …*, *VZS X.2 …*, *VZS XI.1 …*,
*VZS N.1 …*). Put the tag on the 665 / 666 / 662 / 562 accounts that carry such
amounts. A company that tags nothing has everything reported on the
"ostatné" rows, which is correct for a standalone entity.

The remaining setup — account mapping, versions — is described in
[the framework guide](module:l10n_cssk_fs_base#setup).

## Preparing the Úč POD {#usage}

*Accounting → Reporting → Statutory Reports → Balance sheet* (or *Income
statement* — it is the same document), *New*. The version *Účtovná závierka
podnikateľov (UZPODv14)* is preselected; the statement kind reads *Financial
statements (balance sheet + income statement)*.

Fill in the three header choices shown for this version:

- **Veľkostná trieda** — *Malá* or *Veľká účtovná jednotka*;
- **Druh závierky** — *Riadna*, *Mimoriadna* or *Priebežná*;
- **Poznámky priložené** — tick when the notes are filed with it.

Click **Compute**, then review, drill down and correct as described in
[the framework guide](module:l10n_cssk_fs_base#review). The Balance sheet menu
shows the súvaha rows, the Income statement menu the výkaz ziskov a strát
rows.

**How some rows are computed:**

- **A.VIII. Výsledok hospodárenia za účtovné obdobie** (r. 100) is the
  movement of classes 5 and 6 in the period, so the súvaha balances before the
  year's result is closed and equals r. 61 of the výkaz ziskov a strát.
- **Account 431** (result awaiting approval) is deliberately on no row: in an
  open ledger it stands against the unclosed opening balance of classes 5 and
  6. A balance on it that is a genuine result of earlier years never approved
  and distributed to 428/429 shows up under *Unmapped accounts*; deciding
  where it belongs is the accountant's call, and the module does not
  reclassify it.
- Accounts the form names on both sides — 316, 336, 373, 398 and 481 — go to
  the asset or the liability row by the sign of their balance.
- Off-balance-sheet accounts of class 7 belong on neither statement; if they
  carry balances they can appear under *Unmapped accounts* and can be ignored
  there.

## Exporting the Úč POD {#export}

**Export XML** on the statement produces the UZPODv14 document:

- figures are in **whole euros**: rows computed from accounts are rounded and
  every total is recomputed from the rounded rows, so the totals pass the
  portal's checks (the screen keeps the cents);
- the file is validated against the official `uzpod-2014.xsd`;
- the form's **kontrolné pravidlá** run first: assets (r. 001) equal
  liabilities and equity (r. 079), netto = brutto − korekcia on every asset
  row, and every subtotal equals the sum of its rows. A failed rule blocks the
  export and is named in the message. A statement whose assets and
  liabilities are both zero is refused as well, as a sign that no account
  reached any row. Accounts that carry more than 100 € and reach no row are
  reported as a warning (*Účty nezachytené v žiadnom riadku výkazu*): it does
  not block the export but appears on the record (in its chatter, and as a
  notification where the filing framework shows export warnings), not only
  in the server log. Account 431 appears there whenever it carries a balance.

The date of compilation in the header is the day of the export. The signature
record is not part of the file.

Submit the file on the Finančná správa portal and record it with **Mark
Submitted** and **File it** (see [the framework guide](module:l10n_cssk_fs_base#filing)).

## The filing record and corrective závierka {#filing-record}

*Accounting → Reporting → Účtovná závierka UZPODv14 (SK)* holds a filing
record per závierka, with the same header choices (*Druh závierky*,
*Veľkostná trieda*, *Poznámky priložené*). It does not compute anything
itself:

- **Vygenerovať XML (UZPODv14)** finds the Úč POD statement of the same
  company, period and submission type (creating and computing one if there is
  none, recomputing it if it is still a draft or preview) and renders it with
  the record's header choices. What is filed is therefore what was reviewed,
  figures entered by hand included. The same schema and kontrolné pravidlá
  apply; the file is attached as `UZPODv14-<date>.xml`.
- **Označiť ako podané** locks the record and keeps the filed copy;
  **Späť na návrh** reopens it.
- **Opravná závierka** (on a submitted record) creates a corrective filing
  linked to the original. It is a full restatement of the period, not a list
  of differences. The UZPODv14 schema has no corrective marker, so the file
  itself still says *riadna*; the corrective nature lies with the type of
  submission on the portal and is shown in the file name
  (`UZPODv14-opravna-<date>.xml`).

## Cash flow and changes in equity {#prehlady}

Under *Statutory Reports → Cash flow statement* and *Statement of changes in
equity*, versions *Prehľad peňažných tokov 2025* and *Prehľad zmien vlastného
imania 2025*, valid from 1 January 2025:

- the cash flow statement splits every non-cash account into operating (A),
  investing (B) and financing (C) activity, so that A + B + C equals the change
  in cash; row *G. Kontrola* shows any difference;
- the statement of changes in equity reads the opening and closing balances of
  groups 41–43 and the year's movements; *Kontrola* shows any difference.

They are working statements for the notes. Their XML export is the module's
own structured format — the Finančná správa publishes no separate form for
them — and is not a filing format.

## Notes (Poznámky) {#poznamky}

*Accounting → Reporting → Poznámky k závierke (SK)*. A record per period with
the articles of the notes on tabs:

- **Čl. I — Všeobecné**: activity, approval date of the previous závierka,
  average headcount;
- **Čl. III — Zásady a odpisy**: going concern, valuation methods, changes of
  methods, low-value asset thresholds and the depreciation schedule;
- **Čl. II, IV–VII — Texty**: the remaining articles.

The texts start with standard wording for a small entity with nothing to
report ("nemá náplň"), so only the exceptions need editing.
**Načítať odpisový plán z majetku** fills the depreciation schedule from the
company's assets (Enterprise asset management), grouped by depreciation
period, replacing the lines already there. Without asset management, or
without any asset, it says so and leaves the schedule as it is; enter it by
hand then. **Vygenerovať PDF** produces the notes as a PDF, stores it on the
record and downloads it.

## Limitations {#limitations}

- **Micro entities** (Úč MÚJ) are not supported; only *malá* and *veľká* can be
  chosen.
- The **notes** are a PDF following the small-entity structure; there is no
  XML export of the notes, and the notes of a large entity are not covered.
  Ticking *Poznámky priložené* is up to you.
- The cash flow and equity statements have no version before 2025 and are not
  laid out row for row as an official table.
- Nothing is submitted from Odoo; the file is produced, validated and
  recorded.
- The row mapping follows the official form and the standard Slovak chart;
  watch *Unmapped accounts* and have the mapping confirmed by your accountant
  before the first filing.
