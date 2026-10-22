=========
Changelog
=========

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
