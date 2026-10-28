=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

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

19.0.1.0.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: Czech ONZ (Oznámení o nástupu do zaměstnání) employment
  registration, built from the employee + hr.version lifecycle (no payslip
  data), exported as a per-employee event batch and validated against the
  official ``ONZ2022_20230616.xsd`` (+ ``baseTypes2.xsd``).
* Two akce modelled (nástup / skončení); optional insurer/pension/unemployment
  blocks and correction actions are out of scope (documented human-verify
  notes).

[19.0.1.0.2] — 2026-09-13
-------------------------

Fixed
~~~~~

- **Terms the translation catalogue never carried.** Strings that reach the
  user were absent from the template — a field with no ``string=``, a mixin
  field addressed to the abstract model's ``ir.model.fields`` row rather
  than each concrete one, or a whole category the offline exporter never
  emitted. An absent term cannot be translated and shows English in an
  otherwise Czech screen. The template and the catalogues now carry them,
  and the Czech is written.

