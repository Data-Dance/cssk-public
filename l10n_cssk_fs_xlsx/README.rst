============================
Financial statements to XLSX
============================

Adds **Export XLSX** to a financial statement (``l10n_cssk_fs_base``): an Excel
workbook with every row of the statement — code, label, brutto, korekcia,
netto, prior-period netto — and, under each row read from the ledger, the
accounts that make it with their own contribution in both periods. The shares
are computed with the row's own formula, so they add up to the row.

A combined document — the Slovak Úč POD carries the súvaha and the výkaz ziskov
a strát together — is written as two sheets.

The figures are the statement's stored rows, overrides included. Recompute
the statement first if the ledger has changed.

Credits
=======

Authors
-------

* Data Dance s.r.o.
