=========
Changelog
=========

All notable changes to **l10n_cssk_account_financial_report** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.1] — 2026-10-27
-------------------------

Fixed
~~~~~

- **The closing-journal box follows the company chosen in the report.** It
  was ticked or not by the company the user was working in, while the
  journals left out were those of the company chosen in the wizard; in a
  multi-company database the two could disagree. It now follows the chosen
  company and is set again when the company changes.

[19.0.1.0.0] — 2026-10-09
-------------------------

Added
~~~~~

- Trial balance, general ledger, open items and aged partner balance leave
  out the company's year-end closing and archive journals
  (``l10n_cssk_closing_journal_ids``) by default, as the statutory statements
  do. A fiscal year's trial balance then shows the opening balance as the
  opening balance instead of as movement on its first day.
