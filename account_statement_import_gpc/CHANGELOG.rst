=========
Changelog
=========

All notable changes to **account_statement_import_gpc** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a
Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.2.0.0] — 2026-08-11
-------------------------

Changed
~~~~~~~

- The GPC parser moved to the new ``account_gpc_base`` module, which this
  module now depends on, so the Enterprise shim
  (``account_statement_import_gpc_ee``) shares it rather than reimplementing
  the record layout. No change in behaviour or output; the wizard hook is
  unchanged and the test suite asserts against the same sample records, now
  built by ``account_gpc_base.tests.gpc_fixtures``.
- The fall-through for a file that is not GPC now catches only the exceptions a
  wrong-format file actually raises (``ValueError`` / ``IndexError`` /
  ``KeyError``) instead of every ``Exception``, so a genuine parser defect is
  no longer reported to the user as an unsupported file format.

[19.0.1.0.0] — 2026-07-18
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
