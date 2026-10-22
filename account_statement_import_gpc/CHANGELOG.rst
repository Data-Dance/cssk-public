=========
Changelog
=========

All notable changes to **account_statement_import_gpc** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a
Changelog.

[Unreleased]
------------

[18.0.1.0.0] — 2026-07-18
-------------------------

Added
~~~~~

- Initial release. GPC (ABO electronic statement) import on the OCA
  statement-import framework: 074 headers (balances, statement number,
  date), 075 transactions (debit/credit/reversal codes, counterparty
  account incl. bank code, document number, native VS/KS/SS), AV message
  records appended to the label, multi-statement files, cp1250 decoding,
  re-import deduplication. Symbols land in the statement line's structured
  fields when available and always as ``VS:``-style label tokens.
