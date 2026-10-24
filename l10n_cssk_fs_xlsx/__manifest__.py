# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK: financial statements to XLSX, row by row with accounts",
    "version": "19.0.1.0.0",
    "summary": "Export a financial statement to Excel: every row with its "
               "brutto / korekcia / netto and the analytic accounts behind it.",
    "description": """
Financial statements to XLSX
============================

An accountant checks a statement against the previous system row by row, and
the question each row raises is "which accounts make this figure". The screen
answers it one row at a time (the drill-down groups the row's journal items by
account); this export answers it for the whole statement at once:

* every row of the statement — code, label, indented as on the form, brutto,
  korekcia, netto and the prior-period netto;
* under each row read from the ledger, the accounts that make it, each with its
  own contribution, current and prior — evaluated with the row's own formula,
  so they sum to the row;
* a document that carries two statements (the Slovak Úč POD: súvaha and výkaz
  ziskov a strát) gets one sheet for each part.

Figures are the statement's stored rows, overrides included, so the workbook
shows what was reviewed and what is filed.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_fs_base", "report_xlsx"],
    "data": [
        "report/statement_xlsx.xml",
        "views/cssk_fs_statement_views.xml",
    ],
    "auto_install": True,
    "installable": True,
}
