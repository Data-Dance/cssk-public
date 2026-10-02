=========
Changelog
=========

All notable changes to **l10n_cssk_recycling_fee_sale** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- CZ/SK recycling fee priced on sale order lines at the order date, filtered to
  the company's market, per piece in the product's unit of measure.
- The product's fixed fee amount is carried from the order to the invoice.
- "Update Recycling Fee" on the order for the on-top presentation: one fee line
  per classification and VAT treatment, never for portable batteries.
