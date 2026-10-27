---
title: Public Holidays: Slovakia and Czech Republic
summary: Generates the Slovak and Czech days of rest into the OCA public holiday calendar, year by year, with the statutory exceptions.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

Leave counting and attendance must not count a day of rest as a working day.
The OCA module `calendar_public_holiday` (used by `hr_holidays_public` and the
OCA attendance and payroll modules) keeps one public holiday record per year
and country, but leaves it empty. This module fills it with the Slovak and
Czech **days of rest** (*dni pracovného pokoja* / *dny pracovního klidu*).

Only days of rest are generated. A holiday that the law makes a working day in
a given year is left out of that year, because leave and attendance must count
it as one. Payroll holiday pay follows its own rules and is not affected.

## Legal background {#legal}

**Slovakia** — [§ 1 and § 2 of Act No. 241/1993](law:sk/1993/241#paragraf-2):
1 January, 6 January, Good Friday, Easter Monday, 1 May, 8 May, 5 July,
29 August, 15 September, 1 November and 24–26 December. The exceptions the
module applies:

- 1 September (*Deň Ústavy*) is a day of rest up to 2023 only, and 17 November
  up to 2024 only. [§ 2 ods. 3](law:sk/1993/241#paragraf-2.odsek-3) keeps them
  (and 28 October) as state holidays that are not days of rest.
- 8 May and 15 September are working days **in 2026 only**: the transitional
  [§ 4b](law:sk/1993/241#paragraf-4b) names that year and no other, so both
  return in 2027 unless the law changes again.

**Czech Republic** — [§ 1 to § 3 of Act No. 245/2000 Coll.](law:cz/2000/245):
1 January, Good Friday (since 2016), Easter Monday, 1 May, 8 May, 5 July,
6 July, 28 September, 28 October, 17 November and 24–26 December.

## How it runs {#usage}

- At installation the current and the next year are generated for both
  countries (if the country exists in the database).
- A monthly scheduled action, *Public holidays: generate next year (SK, CZ)*,
  keeps the current and the next year present, so a new year appears on its
  own.
- The records are under *Calendar → Configuration → Public Holidays*.

Generation only adds what is missing. Lines already present for a date are
kept, including your edits; a regional line (one with states) does not count
as the nationwide day. To force a change, delete the line or the whole year
and run the scheduled action again (*Settings → Technical → Scheduled
Actions*, *Run Manually*).

## Limitations {#limitations}

- The rules are a table in the code. When the law changes, the module must be
  updated; years already generated are not corrected automatically — delete
  the affected year and regenerate it.
- Only Slovakia and the Czech Republic, nationwide days only.
- Sundays are not generated: the calendar lists holidays, and working time is
  defined by the employee's working schedule.
