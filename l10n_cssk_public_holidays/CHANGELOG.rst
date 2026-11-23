=========
Changelog
=========

All notable changes to **l10n_cssk_public_holidays** are documented here.
Versioning follows the Odoo manifest (``19.0.x.y.z``); format follows Keep a Changelog.

[19.0.1.0.2] — 2026-11-21
-------------------------

Changed
~~~~~~~
- The scheduled action keeps the working calendars from the first day of
  the previous calendar month on, where it used to start at the current
  date. Payroll for a month is computed early in the next one, so the month
  just ended is still open and needs its holidays: run on 5 September the
  action writes 29 August, and leaves 5 July alone. The same start holds at
  installation, at the upgrade and for a company the action reaches for the
  first time. The reach is the constant ``OPEN_MONTHS_BACK`` (1);
  ``cssk_sync_calendar_leaves(date_from=…)`` still covers anything earlier.
- In January the year before is generated as well, so that a database
  installed then has December.
- A public holiday that is new to a company makes Time Off recount the leave
  requests that span it, also in the previous month: an approved week of
  leave over a Friday holiday goes from five days to four, the day returns
  to the allocation, and Time Off notes it for the employee in the request's
  history. That is the right count for the open month. A holiday that is
  already in the calendars is not written again, so a repeated run recounts
  nothing and notifies nobody.
- A country taken off the system parameter, or a company that leaves the
  country, loses the holidays from the previous month on, where it lost the
  coming ones.

Upgrade
~~~~~~~
- The upgrade asks the scheduled action to run at once. It adds the holidays
  of the previous month, and of the current month before the day of the
  upgrade, for the companies that already have the coming ones; the records
  already there are left as they are. Where scheduled actions do not run,
  run *Public holidays: generate next year (SK, CZ)* manually.

[19.0.1.0.1] — 2026-11-21
-------------------------

Added
~~~~~
- The Slovak holidays are kept as public holidays of the working calendars
  (``resource.calendar.leaves`` with no resource and no calendar), one per
  Slovak company and nationwide line, which is the only form in which Time
  Off and both payroll engines know a holiday. A line renamed, moved, made
  regional or removed takes its record along; a day the company already has
  as a public holiday entered by hand is left to that record. The scheduled
  action does the writing, for days from the current date on, so no past
  leave request is recounted unasked;
  ``cssk_sync_calendar_leaves(date_from=…)`` covers an earlier period on
  request. A line added or changed by hand is applied at once.
- System parameter ``l10n_cssk_public_holidays.calendar_leave_countries``
  (default ``SK``): ``SK,CZ`` adds Czech companies, ``none`` switches the
  feature off.
- Installation and the upgrade ask the scheduled action to run at once, so
  that the holidays are written with every module loaded and Time Off
  recounts the leave requests that span them. Where scheduled actions do
  not run, run *Public holidays: generate next year (SK, CZ)* manually.

Changed
~~~~~~~
- The module depends on ``resource``.

[19.0.1.0.0] — 2026-10-27
-------------------------

Added
~~~~~
- Slovak (zákon č. 241/1993 Z. z.) and Czech (zákon č. 245/2000 Sb.) days of
  rest generated into the OCA public holiday calendar per year and country,
  including the Slovak exceptions: 1. 9. up to 2023, 17. 11. up to 2024, and
  8. 5. and 15. 9. as working days in 2026 (§ 4b, zákon č. 261/2025 Z. z.).
- The current and the next year are loaded at install, and a monthly scheduled
  action keeps them present. Generation is idempotent and keeps manual edits.
