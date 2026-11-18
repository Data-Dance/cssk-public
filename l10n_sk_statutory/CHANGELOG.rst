=========
Changelog
=========

All notable changes to **l10n_sk_statutory** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

[18.0.1.1.1] — 2026-11-18
-------------------------

Fixed
~~~~~

- The office for selected taxpayers files "Úrad pre vybrané hospodárske
  subjekty", the wording of the tax office's own list in the DPHv25 form. It
  had kept "Daňový úrad pre vybrané daňové subjekty", which that list does not
  contain, so the *Daňový úrad* box loaded empty. A migration rewrites the
  existing record, unless someone changed the code. Ported from 19.0.1.1.1.

[18.0.1.1.0] — 2026-11-18
-------------------------

Fixed
~~~~~

- The eight regional tax offices carry their seat ("Bratislava") as the
  submission code, not the full office name. The tax office's form lists the
  offices by seat and matches the exported ``danovyUrad`` against that list, so
  a return or a súhrnný výkaz loaded with the *Daňový úrad* box empty. Returns
  filed from other software carry the seat alone. The data is ``noupdate``, so
  a migration rewrites the existing records, unless someone changed the code.
  The office for selected taxpayers is unchanged. Ported from 19.0.1.1.0.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: Slovak statutory reference data seeding the country-neutral registries of ``l10n_cssk_core``.
- ``cssk.tax.authority`` — the eight regional daňové úrady plus the Daňový úrad pre vybrané daňové subjekty; ``submission_code`` carries the office name (the SK XSDs declare ``danovyUrad`` as free-text ``xsd:string``, no codelist).
- ``cssk.person.type`` — Slovak taxpayer types (FO / PO).
