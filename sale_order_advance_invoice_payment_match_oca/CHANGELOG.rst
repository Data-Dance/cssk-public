=========
Changelog
=========

All notable changes to **sale_order_advance_invoice_payment_match_oca** are documented here.
Versioning follows the Odoo manifest (``18.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.0.0] — 2026-07-14
-------------------------

Added
~~~~~

- Initial release. Runs the advance-invoice matching pass ahead of the OCA
  ``account_reconcile_oca`` auto-reconcile (reconcile models + invoice
  matching).
