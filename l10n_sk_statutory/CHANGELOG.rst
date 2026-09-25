=========
Changelog
=========

All notable changes to **l10n_sk_statutory** are documented here.
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

- Baseline: Slovak statutory reference data seeding the country-neutral registries of ``l10n_cssk_core``.
- ``cssk.tax.authority`` — the eight regional daňové úrady plus the Daňový úrad pre vybrané daňové subjekty; ``submission_code`` carries the office name (the SK XSDs declare ``danovyUrad`` as free-text ``xsd:string``, no codelist).
- ``cssk.person.type`` — Slovak taxpayer types (FO / PO).
