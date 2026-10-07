=========
Changelog
=========

All notable changes to **account_edi_isdoc_sale_advance** are documented here.
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

- Maps the Czech advance-payment document chain (``sale_order_advance_invoice``) to
  ISDOC document types:

  - zálohová faktura (``is_advance_invoice`` sale order) → **DocumentType 4**
    (non-VAT proforma), via ``account_edi_isdoc_sale``.
  - daňový doklad k přijaté platbě (``is_advance_invoice_tax_document``) →
    **DocumentType 5** (with VAT); its credit note → **DocumentType 6**.
  - final invoice: ``is_advance_tracking`` deduction lines are reported as
    ``TaxedDeposits`` / already-claimed amounts on a normal **DocumentType 1**
    invoice, each referencing its tax document.

- Auto-installs when both ``account_edi_isdoc_sale`` and ``sale_order_advance_invoice``
  are present.
