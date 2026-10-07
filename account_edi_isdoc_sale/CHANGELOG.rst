=========
Changelog
=========

All notable changes to **account_edi_isdoc_sale** are documented here.
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

- Bridges sale orders to ISDOC: a sale order rendered as a pro-forma can be
  exported as an ISDOC 6.0.2 proforma — **DocumentType 4** (zálohová faktura, a
  request for advance payment).
- Incoming proformas are decoded by the base module (``account_edi_isdoc``) into a
  draft vendor bill, since a proforma is not a bookable tax document.
- Auto-installs when both ``account_edi_isdoc`` and ``sale`` are present.
