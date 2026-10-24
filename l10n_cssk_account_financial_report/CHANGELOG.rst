=========
Changelog
=========

All notable changes to **l10n_cssk_account_financial_report** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-10-09
-------------------------

Added
~~~~~

- Trial balance, general ledger, open items and aged partner balance leave
  out the company's year-end closing and archive journals
  (``l10n_cssk_closing_journal_ids``) by default, as the statutory statements
  do. A fiscal year's trial balance then shows the opening balance as the
  opening balance instead of as movement on its first day.
