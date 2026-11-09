=========
Changelog
=========

18.0.1.1.2 (2026-11-09)
=======================

Back-ported from 19.0: every change below, as released there.

Unreleased
==========

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.1.2] — 2026-11-05
=========================

- Slovak catalogue: translated the strings that were still English.

[19.0.1.1.1] — 2026-10-27
=========================

* **PPPZ / HOZ: Street 2 no longer wins as the číslo popisné.** Whatever
  *Street 2* held (a floor, a c/o line) was filed as
  *adresaPlatceCisloPopisneOrientacni* ahead of the number in the street. The
  address is now read by the shared helper of ``l10n_cssk_core``: the
  trailing number of *Street*, *Street 2* only when it holds nothing but a
  number.

Fixed
~~~~~

- **A corrective PPPZ amends only the overview sent to the same insurer.**
  A submitted overview to one insurer let a corrective overview for the same
  month go out to another insurer that had never received a regular one. The
  same scoping applies to the HOZ.
- **The health fields are on the forms.** The company's *Default health
  insurer* and *Health payer number* are on the company form (tab *Payroll
  Reporting*), the employee's *Health insurer* next to *Identification No*.
  Neither was on any form, so they could be set only by import.

Changed
~~~~~~~

- **Czech translation.** The correction and submission fields every declaration shares (*Correction Type*, *Correction Reference*, *Delivery*, *Submissions*) showed in English; they are translated now.

18.0.1.0.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

18.0.1.0.0 (2026-07-05)
-----------------------

* Ported to Odoo 18.0. HOZ change-date access now reads
  ``employee.contract_id.date_start`` / ``date_end`` (18.0 ``hr.contract``)
  instead of the 19.0 ``version_id.contract_date_*``; test setup adapted.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: Czech health-insurance employer e-filings.
* **PPPZ** (Přehled o platbě pojistného zaměstnavatele) — monthly employer
  health-premium overview, aggregated per insurer from ``HEALTHEE`` / ``HEALTHER``
  and validated against the official ``PPPZ_2025_v8.xsd``.
* **HOZ** (Hromadné oznámení zaměstnavatele) — bulk employee enrol (P) /
  terminate (O) notification, built from the employee + ``hr.version`` lifecycle
  and validated against the official ``HOZ_2025_v8.xsd``.
* Per-insurer modelling: seven CZ health insurers as a selection, with a
  per-employee / company-default insurer assignment.
