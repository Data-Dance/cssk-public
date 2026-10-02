=========
Changelog
=========

All notable changes to **account_statement_import_kb_best** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Initial release. Komerční banka BEST electronic statements (``*.OKM``) on the
  OCA statement-import framework: balances from the turnover record,
  accounting transactions as lines, VS/KS/SS, counterparty account and name,
  re-import deduplication on KB's posting identifier, journal matched on
  bank code, prefix and number.
