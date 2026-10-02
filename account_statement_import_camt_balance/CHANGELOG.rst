=========
Changelog
=========

All notable changes to **account_statement_import_camt_balance** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-29
-------------------------

Added
~~~~~

- The latest daily ``CLBD`` closes the statement, and the earliest ``OPBD`` / ``PRCD``
  opens it.
- An entry whose detail blocks do not add up to it becomes one line.
