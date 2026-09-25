=========
Changelog
=========

All notable changes to **l10n_cz_intrastat_oca** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- INTRASTAT-CZ Community/OCA adapter: a thin country layer on the OCA ``intrastat_product``
  declaration engine that renders the grouped declaration lines as the official Celní správa
  **InstatOnline CSV** (via ``l10n_cssk_intrastat_base``).
- CSV column layout, constant fields and number formatting reproduce the Odoo EE
  ``l10n_cz_intrastat`` output (validated against its expected file in the shared base's tests).
  The Czech declaration has no XSD — the InstatOnline portal validates on upload.
- Deliberately not named ``l10n_cz_intrastat`` to avoid colliding with Odoo EE's native module;
  one edition installs exactly one of the two. Licensed AGPL-3 (subclasses the AGPL OCA engine).
