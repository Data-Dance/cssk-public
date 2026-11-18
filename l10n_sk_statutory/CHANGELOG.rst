=========
Changelog
=========

All notable changes to **l10n_sk_statutory** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[Unreleased]
------------

Carry-over to 18.0: the selected-taxpayers office code of 19.0.1.1.1. DISCHARGED 2026-11-18 (18.0.1.1.1) — do not port this again.

Carry-over to 18.0: the tax offices' submission codes of 19.0.1.1.0. DISCHARGED 2026-11-18 (18.0.1.1.0) — do not port this again.

Changed
~~~~~~~

- Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.1] — 2026-11-18
-------------------------

Fixed
~~~~~

- The office for selected taxpayers files "Úrad pre vybrané hospodárske
  subjekty", the wording of the tax office's own list in the DPHv25 form. It
  had kept "Daňový úrad pre vybrané daňové subjekty", which that list does not
  contain, so the *Daňový úrad* box loaded empty. A migration rewrites the
  existing record, unless someone changed the code.

[19.0.1.1.0] — 2026-11-17
-------------------------

Fixed
~~~~~

- The eight regional tax offices carry their seat ("Bratislava") as the
  submission code, not the full office name. The tax office's form lists the
  offices by seat and matches the exported ``danovyUrad`` against that list, so
  a return or a súhrnný výkaz loaded with the *Daňový úrad* box empty. Returns
  filed from other software carry the seat alone. The data is ``noupdate``, so
  a migration rewrites the existing records, unless someone changed the code.
  The office for selected taxpayers is unchanged.

[19.0.1.0.1] — 2026-11-06
-------------------------

Fixed
~~~~~

- The person types were seeded with the native name as the English source, so
  an English user saw "Právnická osoba" and the Slovak/Czech catalogue
  translated it into itself. The source is now "Natural person" / "Legal
  entity", with "Fyzická osoba" / "Právnická osoba" in both the Slovak and the
  Czech catalogue. The data is ``noupdate``, so a migration rewrites the
  existing records, unless someone renamed one.

[19.0.1.0.0] — 2026-07-04
-------------------------

Added
~~~~~

- Baseline: Slovak statutory reference data seeding the country-neutral registries of ``l10n_cssk_core``.
- ``cssk.tax.authority`` — the eight regional daňové úrady plus the Daňový úrad pre vybrané daňové subjekty; ``submission_code`` carries the office name (the SK XSDs declare ``danovyUrad`` as free-text ``xsd:string``, no codelist).
- ``cssk.person.type`` — Slovak taxpayer types (FO / PO).
