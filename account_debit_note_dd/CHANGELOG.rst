=========
Changelog
=========

All notable changes to **account_debit_note_dd** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Extends OCA ``account_debit_note`` with Data Dance customisations to ``account.move``
  posting/handling for debit notes (vrubopis).
- Dedicated debit-note invoice report template (``report/report_invoice.xml``) and
  form-view adjustments (``views/account_move_views.xml``).
