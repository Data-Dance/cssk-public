=========
Changelog
=========

All notable changes to **sale_order_advance_invoice_payment_match_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-07-14
-------------------------

Added
~~~~~

- Initial release. Runs the advance-invoice matching pass ahead of the OCA
  ``account_reconcile_oca`` auto-reconcile (reconcile models + invoice
  matching).
