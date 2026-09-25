=========
Changelog
=========

All notable changes to **advance_invoice_saldo_xlsx** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a
Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-09-17
-------------------------

Fixed
~~~~~

- **An Administrator could not open it.** An accounting **Administrator**
  could reach the advance-invoice saldo report and hit *not allowed to
  access*. On Community, ``account.group_account_manager`` does not imply
  ``account.group_account_user`` (and on Enterprise ``account_accountant``
  only adds ``group_account_basic``), so a model granted to
  ``group_account_user`` alone is closed to an Administrator who lacks "Show
  Full Accounting Features". It sits under Reporting, which core opens to
  Invoicing users. ``group_account_manager`` now has the same access as
  ``group_account_user`` on the report wizard. Takes effect on module update.

[19.0.1.0.0] — 2026-07-18
-------------------------

Added
~~~~~

- Initial release. XLSX saldo workbook of issued and received advance
  invoices — per advance: total, paid, paid date, tax-documented amount,
  deducted amount, open saldo (paid − deducted) and statuses; settled
  advances hidden by default. Menu under Accounting → Reporting.
