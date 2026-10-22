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

* Ported to Odoo 18.0. Employee-lifecycle access now reads
  ``employee.contract_id.date_start`` / ``date_end`` (18.0 ``hr.contract``)
  instead of the 19.0 ``version_id.contract_date_*``; test setup adapted.

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: Czech ONZ (Oznámení o nástupu do zaměstnání) employment
  registration, built from the employee + hr.version lifecycle (no payslip
  data), exported as a per-employee event batch and validated against the
  official ``ONZ2022_20230616.xsd`` (+ ``baseTypes2.xsd``).
* Two akce modelled (nástup / skončení); optional insurer/pension/unemployment
  blocks and correction actions are out of scope (documented human-verify
  notes).
