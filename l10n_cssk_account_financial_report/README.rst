=======================================================
Financial reports without the year-end closing journals
=======================================================

The OCA trial balance, general ledger, open items and aged partner balance
leave out the journals the company names as year-end closing / reopening and
migration archive journals (*Year-end closing journals* in the Accounting
settings, ``l10n_cssk_core``) — the same set the statutory financial
statements and the income-tax return already exclude.

Usage
=====

Each of the four report wizards has an *Exclude year-end closing and archive
journals* box, ticked by default when the company names any such journal.

* **Trial balance / General ledger**: with the journal filter left empty, the
  report runs over every other journal of the company. An explicit journal
  selection is used exactly as chosen.
* **Open items / Aged partner balance**: the excluded journals' move lines are
  left out of the open balances.

Why
===

A Czech or Slovak ledger closes each fiscal year into a closing account and
reopens it on the first day of the next. Reported as ordinary entries, the
reopening is movement inside the new year — the trial balance's opening column
reads 0 and its debit column carries the whole opening balance — and a
migrated agenda's archive of pre-cut-over documents is counted on top of the
opening balance that summarises it.

Credits
=======

Authors
-------

* Data Dance s.r.o.
