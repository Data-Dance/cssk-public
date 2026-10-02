=========
Changelog
=========

All notable changes to **account_statement_import_mt940** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a
Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Initial release. MT940 / MultiCash ``*.STA`` statement import on the OCA
  statement-import framework, using the ``account_mt940_base`` parser: several
  statements and accounts per file, VS/KS/SS into the symbol fields when
  available and always into the label, counterparty account and name, raw
  :61:/:86: kept on the line, re-import deduplication.
- The bank journal is matched on bank code, prefix and number, so a :25:
  account in the national form finds a journal holding the IBAN and the
  reverse.
