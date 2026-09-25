=========
Changelog
=========

All notable changes to **sale_order_advance_invoice_payment_match** are documented here.
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

- Initial release. Matches incoming bank statement lines to open advance
  invoices by advance number, structured variable symbol (duck-typed
  ``variable_symbol`` field — ``l10n_cssk_payment_symbols`` or upstream
  odoo/odoo#275611) or loose digit runs (auto-applied only on an exact
  amount); ambiguity bails out. Applying registers a real payment to the
  advance clearing account, reconciles its outstanding leg with the
  statement suspense leg and links the offline transaction driving the
  advance statuses. Company settings: opt-in cron auto-matching and the
  tax-document mode on matched payments (manual / draft / create-and-post).
  Manual "Match Advance Invoice" wizard on bank statement lines.
