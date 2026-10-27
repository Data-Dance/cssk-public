---
title: CZ/SK Financial Reports Without Year-End Closing Journals
summary: The OCA trial balance, general ledger, open items and aged partner balance leave out the year-end closing, reopening and archive journals, as the statutory statements do.
verified: 19.0.1.0.1
---

## What it is for {#purpose}

A Czech or Slovak ledger closes its books at the end of each fiscal year
and reopens them on the first day of the next. Our localization lets the company
name the journals that hold those closing and reopening entries — and, for an
agenda migrated from another system, the archive of documents from before the
cut-over — as **year-end closing journals** (*Denníky koncoročnej uzávierky* /
*Deníky závěrky roku*, a setting of [module:l10n_cssk_core](module:l10n_cssk_core)).
The statutory financial statements and the income-tax return leave those
journals out.

The OCA reports of [module:account_financial_report](module:account_financial_report)
did not, and so they disagreed with the statements:

- the **trial balance** of a year showed the 1 January reopening entry as
  movement within the year: the opening-balance column read 0 and the debit
  column carried the whole opening balance;
- accounts renumbered in a previous system kept a balance coming only from the
  archive, so the trial balance listed accounts the company no longer uses;
- **open items** counted both a migrated opening balance and the archived
  documents it summarises.

This module makes the four reports leave those journals out by default. It
installs itself when both `account_financial_report` and
[module:l10n_cssk_core](module:l10n_cssk_core) are installed.

## Using it {#usage}

Each of these wizards under *Accounting → Reporting → OCA accounting reports*
gets a box **Exclude year-end closing and archive journals**, under *Target
Moves*:

| Report | What the box does |
|---|---|
| Trial Balance | With the journal filter left empty, the report runs over every other journal of the company. If you pick journals yourself, exactly those are used, closing journals included. |
| General Ledger | The report runs over every journal of the company except the closing journals. |
| Open Items | Journal items of the closing journals are left out of the open balances. |
| Aged Partner Balance | As for open items. |

The box is ticked by default when the company chosen in the wizard has at
least one year-end closing journal, and unticked when it has none — then it
changes nothing. Changing the company sets it again.
Untick it to get the plain OCA behaviour for one run.

The *Journal Ledger* and the *VAT Report* are not affected: the first is run
journal by journal, and the second reads taxes, which closing entries do not
carry.

## Limitations {#limitations}

- **Nothing happens until the year-end closing journals are set**, and in this
  version no form in the user interface shows that company setting
  (`l10n_cssk_closing_journal_ids`). The field's help refers to the
  Accounting settings, but it is not there; ask your administrator to set it.
- A journal named there disappears from these four reports entirely. If the
  first opening balance of a migrated company is posted in such a journal, it
  disappears from them too; post it in an ordinary journal.
