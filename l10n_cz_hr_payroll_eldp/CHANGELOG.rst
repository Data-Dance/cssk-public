=========
Changelog
=========

Unreleased
----------

* Relicensed to **AGPL-3**. Part of a repository-wide move to a single licence:
  everything Data Dance authors is AGPL-3 except the modules that depend on Odoo
  Enterprise, which OEEL forbids from carrying it. What differs between modules
  is now whether they are published, not how they are licensed.

[19.0.1.0.5] — 2026-10-27
-------------------------

**Changed**

- **Czech translation.** The correction and submission fields every declaration shares (*Correction Type*, *Correction Reference*, *Delivery*, *Submissions*) showed in English; they are translated now.

[19.0.1.0.4] — 2026-10-27
-------------------------

Fixed
~~~~~

- **Employment periods from every contract, not today's.** Days, dates and
  the type of the record were read from the employee's current contract
  version, so an employee who left and came back, or whose contract was
  replaced during the year, was reported with the wrong period. Each
  employment period in the year now gets its own row (up to the three one
  ELDP holds; more is refused with a message).
- **The assessment base is capped and insured-only.** The base was the sum of
  the gross wage — over the annual maximum assessment base (§ 15a zák.
  589/1992 Sb.) for high earners, and including months that were not insured.
  It is now the sum of the monthly bases from the social-insurance line, each
  rounded up (§ 5d), split by period.
- Draft payslips are no longer counted.

[19.0.1.0.3] — 2026-10-27
-------------------------

Fixed
~~~~~

- **First name and surname were swapped** in the XML: "Pavel Novák" was filed
  as first name *Novák*, surname *Pavel*. The surname is now the last word of
  the employee's name.

Changed
~~~~~~~

- **ELDP follows the JMHZ transition.** From 2026 the ČSSZ compiles the
  ELDP from the unified monthly employer report (JMHZ, Act No. 323/2025
  Coll.). Under Act No. 360/2025 Coll., Art. V, the employer still files it
  for years before 2026 and, for 2026, only for an employee whose pension
  insurance ended before 1 April 2026. An ELDP for 2026 now contains only
  those employees and is refused when there are none; 2027 and later are
  refused. The record's period is now the whole calendar year.

19.0.1.0.1 (2026-07-06)
-----------------------

* Normalized user-facing strings to clean English (form name, selection labels,
  field labels/help and error messages; authority codes kept as tokens). Added
  a Czech translation (``i18n/cs.po``).

19.0.1.0.0 (2026-07-05)
-----------------------

* Initial release: annual CZ ELDP (Evidenční list důchodového pojištění)
  per-employee pension record, aggregated over the calendar year from ``GROSS``
  (assessment base) and the employment period (insured days), validated against
  the official ``ELDP09.xsd``.
* Single continuous period per employee; assessment base uncapped; excluded /
  deducted day columns emitted empty (documented human-verify notes).

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

