---
title: CZ/SK Financial Statements
summary: The Slovak and Czech financial statements computed from the ledger, row by row, with a comparative period, figures entered by hand where the books cannot supply them, checks that every account reached a row, and the filing record.
verified: 19.0.1.10.3
---

## What it is for {#purpose}

The statutory financial statements in Slovakia and the Czech Republic are
fixed forms: every row has a prescribed label and a prescribed content. This
module is the shared machinery that fills them from Odoo's journal items. It
works the same way in Community and Enterprise and does not use Odoo
Enterprise's accounting reports.

It ships no statement of its own. The rows, the account mapping and the export
format of each form come with a country module:

| Country | Module | Statements |
|---|---|---|
| Slovakia | [module:l10n_sk_fs](module:l10n_sk_fs) | Účtovná závierka Úč POD (súvaha + výkaz ziskov a strát in one document), Prehľad peňažných tokov, Prehľad zmien vlastného imania, Poznámky |
| Slovakia | [module:l10n_sk_single_entry_closing](module:l10n_sk_single_entry_closing) | Účtovná závierka v jednoduchom účtovníctve (Úč FO) |
| Czech Republic | [module:l10n_cz_fs](module:l10n_cz_fs) | Rozvaha, Výkaz zisku a ztráty, Přehled o peněžních tocích, Přehled o změnách vlastního kapitálu |

This page describes what all of them have in common: creating a statement,
computing it, checking it, correcting it and recording the filing. The country
pages describe the forms themselves and the law behind them.

## Setting it up {#setup}

1. **Install the country module.** Without it the menus below are empty.
2. **Check the account mapping.** Rows read accounts by their code in the
   national chart of accounts. If your chart uses codes the form does not know
   (an extra analytic account under a non-standard number, for instance), map
   them under *Accounting → Configuration → CZ/SK Localization → Statement
   account mapping*. The [unmapped-accounts check](#checks) tells you which
   ones need it.
3. **Statement versions** are under *Accounting → Configuration → CZ/SK
   Localization → Financial Statement Versions*, for accounting
   administrators. Each version is one vintage of a form: its rows, the period
   it applies to, its XML template and, where the authority publishes one, its
   XSD. The country modules install them; normally you do not edit them.
   An archived version can still be chosen for a period it covers.

## Creating and computing a statement {#usage}

*Accounting → Reporting → Statutory Reports*, then the kind of statement:
**Balance sheet**, **Income statement**, **Cash flow statement** or
**Statement of changes in equity**. Click *New*.

- **Period.** *Date From* and *Date To* default to the company's last completed
  fiscal year, so a company whose fiscal year does not end in December gets
  the right dates.
- **Version.** The latest version of that statement valid for the period in
  the company's fiscal country is filled in. If none covers the period, the
  field stays empty and the statement cannot be saved.
- **Statement Kind** shows what the document is. The Slovak Úč POD is one
  document holding both the súvaha and the výkaz ziskov a strát, so it shows
  *Financial statements (balance sheet + income statement)* and is listed
  under both menus; each menu shows only its own part of the rows, opened from
  anywhere else the record shows all of them.

Click **Compute**. The module reads the company's posted journal items:

- rows of a balance sheet take the **cumulative balance at the end date**;
- rows of an income statement, a cash flow statement or a statement of changes
  in equity take the **movement within the period**; opening and closing rows
  of the last two take the balance the day before the period and at its end;
- the **prior period** column is computed the same way for the same dates one
  year earlier;
- entries in the company's year-end closing journals are left out, because a
  statement reports the period's activity, not the closing and reopening of the
  books (see [Limitations](#limitations) for how those journals are set).

The statement moves to **Preview**. Compute again whenever the books change; it
can be recomputed in *Draft* and *Preview* only.

## Reviewing the figures {#review}

The *Lines* tab shows the form as a tree: every total is the sum of the rows
beneath it (*Collapse all* / *Expand all* at the top). The columns are
**Current period** and **Prior period**.

- **Drill-down.** The magnifier next to a row computed from accounts opens
  *Source documents*: the journal items behind the figure, grouped by account
  and then by document — the same items the figure was summed from.
- **The ✓ column** marks rows whose journal items add up to the figure. A row
  that does not tie (rounding, a figure entered by hand) is not marked.
- On forms filed in three columns — the Slovak súvaha and the Czech rozvaha
  assets — each row also carries **Brutto** and **Korekcia** (accumulated
  depreciation and allowances), with the figure shown being the net. The
  screen shows the net only; the three columns appear in the
  [XLSX export](#xlsx) and in the exported XML.

## Entering a figure by hand {#overrides}

Some figures the ledger cannot supply. Click the pencil next to a figure,
type the amount and press **Compute** to update the totals above it.

- The figure is **kept on every recompute** and is marked as entered by hand.
  The undo arrow returns the row to the computed figure on the next Compute.
- **Totals cannot be overridden** — override the rows they add up instead.
- The **prior period** has its own override. Use it in the first year kept in
  Odoo, when last year's ledger is in another system, to show last year's
  figures as they were filed.
- Changing a figure returns the statement to **Draft**, so its totals cannot be
  exported until the next Compute brings them back in line.

## Checks {#checks}

Two buttons in the header report what a balanced statement can still hide:

| Button | Meaning | What to do |
|---|---|---|
| **Unreconciled rows** (red) | Rows whose journal items do not add up to the figure. Green **Rows tie out** when there are none. | Normal for rows entered by hand; otherwise open the row's source documents. |
| **Unmapped accounts** (orange) | Accounts carrying a balance at the end date that no row of the statement claims. Their money is in the ledger and not on the form, yet the statement still foots and still balances. The 50 largest balances are listed; amounts under 1 are ignored. | Map the account to the code the form expects under *Statement account mapping*, then *Compute* again. Class 7 (closing and off-balance accounts) and accounts typed off-balance are never listed. Some accounts are listed by design — the country pages say which. |

The country module may add further checks that run on export (the Slovak Úč
POD runs the form's kontrolné pravidlá, for instance).

## Exporting and recording the filing {#filing}

1. **Export XML** renders the statement in the version's XML format. It is
   refused while the statement is a draft, and when the company has neither a
   DIČ (the Slovak *DIČ* field) nor a *Tax ID*: the filer's identification is
   the DIČ, so a unit that is not a VAT payer exports with its DIČ alone.
   The file is validated against the version's XSD; a version that declares
   that the authority publishes no XSD for the form exports without
   validation. The file is attached to the statement, which moves to
   **Exported**.
2. Submit the file on the authority's portal yourself.
3. **Mark Submitted** records it: the filed copy is kept, and the statement is
   locked — it cannot be recomputed, re-exported or deleted.
4. **File it** opens a delivery record for the filing. With only the manual
   channel installed, it records who filed it on the portal and holds the
   receipts the portal returned.

**Corrective statement**, on a submitted statement, copies it into a new
draft flagged *Corrective* (opravná závierka / závěrka) and linked to the
original. Correct the accounting, compute the copy and file it like any
other; there are no difference rows, the corrective statement restates the
whole period.

**Reset to Draft** reopens an exported or submitted statement. Only accounting
administrators may do it; the copy that was filed stays attached and listed in
the filing history.

A statement imported from a previous system as a historical filing is shown
as **Historical filing** and cannot be computed, exported or submitted. Where
filed and computed figures have been compared, the **Comparisons** button
leads to the comparisons of that statement.

## Export to Excel {#xlsx}

With the [module:l10n_cssk_fs_xlsx](module:l10n_cssk_fs_xlsx) add-on (installed
automatically when the Excel reporting module `report_xlsx` is present), an
**Export XLSX** button appears on every statement that is not a draft. The
same report is available as *Statement with accounts (XLSX)* under the print
menu.

The workbook lists every row of the statement — code, label indented as on the
form, brutto, korekcia, netto and the prior-period netto — and under each row
computed from accounts, the accounts that make it, each with its own
contribution for the current and the prior period. A document that holds two
statements, such as the Slovak Úč POD, gets one sheet per part. The row
figures are the statement's stored figures, so the workbook shows exactly what
was reviewed, figures entered by hand included; the account lines below an
overridden row still show what the ledger holds.

**Export warnings.** Checks that do not stop the export are listed in a
yellow banner at the top of the form, and in the chatter, until the next
export.

## Limitations {#limitations}

- **Year-end closing journals have no field on screen.** The setting exists on
  the company (*Year-end closing journals*) and every statement honours it, but
  no form displays it, so it can only be set by technical means. Until it is
  set, closing and reopening entries are counted like any other entry.
- The screen shows the net figure only; brutto and korekcia are visible in the
  XLSX export and the XML.
- A statement can be created only for a period that some version covers. The
  versions the country modules install say from when they apply.
- Nothing is sent to an authority from here: the file is produced, validated
  and recorded, and you submit it yourself.
- The account mapping follows the standard national chart of accounts and must
  be reviewed with your accountant before the first filing.
