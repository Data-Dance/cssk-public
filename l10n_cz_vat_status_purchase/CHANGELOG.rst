=========
Changelog
=========

All notable changes to **l10n_cz_vat_status_purchase** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-09-28
-------------------------

Added
~~~~~

- Purchase order lines propose the taxes the company's VAT status allows on the
  order date (``l10n_cz_vat_status``). The document the order produces is
  decided again by its own DUZP.
