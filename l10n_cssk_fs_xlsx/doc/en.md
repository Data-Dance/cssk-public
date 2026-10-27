---
title: CZ/SK Financial Statements — Excel Export
summary: Exports a financial statement to Excel, every row with its brutto, korekcia and netto and the accounts that make it.
verified: 19.0.1.0.0
family: l10n_cssk_fs_base#xlsx
---

Adds an **Export XLSX** button to every financial statement that is not a draft. The workbook lists each row with brutto, korekcia, netto and the prior-period netto, and under each row computed from accounts, the accounts behind it with their own contributions; the Slovak Úč POD gets one sheet for the súvaha and one for the výkaz ziskov a strát.

It installs itself when the financial statements framework and the Excel reporting module `report_xlsx` are both installed, and has no settings.
