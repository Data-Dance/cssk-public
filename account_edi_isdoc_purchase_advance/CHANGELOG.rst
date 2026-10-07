=========
Changelog
=========

All notable changes to **account_edi_isdoc_purchase_advance** are documented
here. Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows
Keep a Changelog.

[Unreleased]
------------

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.0] — 2026-07-18
-------------------------

Added
~~~~~

- Initial release. ISDOC DocumentType 4 imports create a received advance
  ``purchase.order`` (a proforma is never posted as a bill); DocumentType
  5/6 imports are routed to the advance journal with
  ``taxable_supply_date`` from ``TaxPointDate``, lines rewritten to the
  paid-advances / clearing accounts, and linked to the matching open
  advance by order reference, variable symbol or unique paid amount.
