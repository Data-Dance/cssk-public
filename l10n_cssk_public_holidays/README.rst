=============================================
Public Holidays: Slovakia and Czech Republic
=============================================

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :alt: License: AGPL-3

|badge1|

Fills the OCA public holiday calendar (``calendar_public_holiday``, used by
``hr_holidays_public`` to exclude holidays from leave counts, and by the OCA
attendance and payroll modules) with the Slovak and Czech **days of rest**,
one record per year and country.

.. contents::
   :local:

What is generated
=================

Only days of rest (*dni pracovného pokoja* / *dny pracovního klidu*). A public
holiday that the law makes a working day is left out of that year, because
leave and attendance must count it as one. Payroll holiday pay follows its own
rules and is not affected.

**Slovakia** (zákon č. 241/1993 Z. z.): 1. 1., 6. 1., Veľký piatok,
Veľkonočný pondelok, 1. 5., 8. 5., 5. 7., 29. 8., 15. 9., 1. 11., 24.–26. 12.
Exceptions:

* 1. 9. (Deň Ústavy) is a day of rest up to 2023 only.
* 17. 11. is a day of rest up to 2024 only. § 2 ods. 3, in the wording in
  force from 1. 11. 2025 (zákon č. 261/2025 Z. z.), keeps 1. 9., 28. 10. and
  17. 11. as state holidays that are not days of rest.
* 8. 5. and 15. 9. are working days in **2026 only**: the transitional § 4b
  inserted by zákon č. 261/2025 Z. z. names that year and no other, so both
  return in 2027 unless the law changes again.

**Czech Republic** (zákon č. 245/2000 Sb.): 1. 1., Velký pátek (since 2016),
Velikonoční pondělí, 1. 5., 8. 5., 5. 7., 6. 7., 28. 9., 28. 10., 17. 11.,
24.–26. 12.

How it runs
===========

* At install, the current and the next year are generated for both countries.
* A monthly scheduled action keeps the current and the next year present, so
  a new year appears on its own.
* Generation is idempotent. Lines already present (matched by date) are kept
  with any manual edits, and only missing days are added. To force a change,
  delete the line or the year and run *Public holidays: generate next year
  (SK, CZ)* again, or call
  ``env["calendar.public.holiday"].cssk_generate(years=(2028,))``.

When the law changes
====================

Edit the rule tables in ``models/calendar_public_holiday.py`` (``SK_FIXED``,
``CZ_FIXED`` and the Easter offsets). Each fixed rule carries a first year, a
last year and a set of skipped years. Add a test for the new year.
Lines already generated for a year the change affects are not removed, so
delete that year's record and regenerate it.

Credits
=======

Authors
-------

* Data Dance s.r.o.
