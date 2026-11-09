=========
Changelog
=========

18.0.1.0.5 (2026-11-09)
=======================

Back-ported from 19.0: every change below, as released there.

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.5] — 2026-11-05
-------------------------

Fixed
~~~~~

- Slovak catalogue: translated the strings that were still English.

[19.0.1.0.4] — 2026-10-27
-------------------------

**Changed**

- **Czech translation.** The correction and submission fields every declaration shares (*Correction Type*, *Correction Reference*, *Delivery*, *Submissions*) showed in English; they are translated now.

[19.0.1.0.3] — 2026-10-27
-------------------------

Fixed
~~~~~

- **First name and surname were swapped** in the XML. The surname is now the
  last word of the employee's name.

Changed
~~~~~~~

- **ONZ can no longer be generated from 1 April 2026.** From that day the
  start and end of an employment are registered through the JMHZ employee
  registration (REGZEC, Act No. 323/2025 Coll.) — for a new event, and for
  an earlier one not notified by 31 March 2026 (Act No. 360/2025 Coll.,
  Art. XXV point 4). *Generate* now refuses an event dated from 1 April 2026
  and any ONZ made on or after that day.

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
