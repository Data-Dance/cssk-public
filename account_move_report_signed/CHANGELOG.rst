=========
Changelog
=========

All notable changes to **account_move_report_signed** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Renders negative (signed) amounts in account-move PDF reports, so CZ/SK credit
  notes (dobropis) display their values as negative rather than positive.
- ``account.move._reverse_tax_totals`` recursively negates any ``amount``-keyed value
  in the tax-totals structure for refund documents; a report template override
  feeds the signed totals into the invoice PDF.
