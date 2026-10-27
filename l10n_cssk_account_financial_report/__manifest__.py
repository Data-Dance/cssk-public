# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK: financial reports without the year-end closing journals",
    "version": "19.0.1.0.1",
    "summary": "Trial balance, general ledger, open items and aged partner "
               "balance leave out the company's year-end closing and archive "
               "journals, as the statutory statements already do.",
    "description": """
Financial reports without the year-end closing journals
=======================================================

``l10n_cssk_core`` lets a company name the journals that hold its year-end
closing and reopening entries — and, for a migrated agenda, the archive of
documents from before the cut-over (``l10n_cssk_closing_journal_ids``). The
statutory statements leave those journals out. The OCA reports did not, and
the two disagreed:

* the **trial balance** of a fiscal year showed the 1st-day opening entry as
  movement inside the year, so the opening column read 0 and the debit column
  carried the whole opening balance;
* accounts that the previous system had renumbered years ago kept a balance
  that came only from the archive, so a trial balance listed accounts that no
  longer exist in the company's books;
* **open items** counted a migrated opening balance AND the archived documents
  it summarises.

With this module the four reports exclude those journals by default — the
wizard's *Exclude year-end closing and archive journals* box, ticked unless
the company names none. For the trial balance and the general ledger, which
already filter by journal, it fills the journal filter with every other
journal when the filter is left empty, so what is included stays visible and
an explicit selection is honoured as is. The journal ledger and the VAT
report are not affected: the first is chosen journal by journal, the second
reads taxes, which closing entries do not carry.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account_financial_report", "l10n_cssk_core"],
    "data": ["views/report_wizard_views.xml"],
    "auto_install": True,
    "installable": True,
}
