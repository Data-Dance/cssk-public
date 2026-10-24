=========
Changelog
=========

All notable changes to **l10n_cssk_fs_xlsx** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-10-09
-------------------------

Added
~~~~~

- *Export XLSX* on a financial statement: every row with brutto, korekcia,
  netto and the prior-period netto, and under each row read from the ledger the
  accounts that make it, current and prior. A combined document (Úč POD) gets
  one sheet for the súvaha and one for the výkaz ziskov a strát.
