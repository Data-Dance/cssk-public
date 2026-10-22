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

* Ported to Odoo 18.0. Insured-period access now reads
  ``employee.contract_id.date_start`` / ``date_end`` (18.0 ``hr.contract``)
  instead of the 19.0 ``version_id.contract_date_*``; test setup adapted.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: annual CZ ELDP (Evidenční list důchodového pojištění)
  per-employee pension record, aggregated over the calendar year from ``GROSS``
  (assessment base) and the employment period (insured days), validated against
  the official ``ELDP09.xsd``.
* Single continuous period per employee; assessment base uncapped; excluded /
  deducted day columns emitted empty (documented human-verify notes).
