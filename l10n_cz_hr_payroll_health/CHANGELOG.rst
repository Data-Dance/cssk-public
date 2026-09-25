=========
Changelog
=========

Unreleased
==========

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

19.0.1.1.0 (2026-08-06)
=======================

* The overview's own ``report_type`` selection is replaced by the shared
  ``correction_type``, so "is this an amendment?" means one thing across all
  twelve forms and the guard against amending a period never filed applies
  here too. ``<typPrehledu>`` still emits the Czech spelling.

19.0.1.0.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

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
