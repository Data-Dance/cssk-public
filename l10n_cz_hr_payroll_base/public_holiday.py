# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A public holiday that falls inside an absence.

A public holiday on a usual working day costs the employee nothing: a monthly
wage is not reduced for it and an hourly earner is compensated at the average
earnings (§ 115 odst. 3 zákoníku práce). Which of the two the day is, the
holiday or the absence booked over it, depends on the absence:

* in dovolená the holiday is not a day of leave (§ 219 odst. 2), so the day
  is the holiday;
* in a temporary incapacity for work and in an ordered quarantine the day is
  a day of the incapacity: § 192 odst. 1 gives the employer's compensation
  "za dny, které jsou pro zaměstnance pracovními dny, a za svátky, za které
  jinak přísluší zaměstnanci náhrada mzdy nebo se mu plat nebo mzda nekrátí".
  The holiday is paid by that compensation (or, after the first 14 calendar
  days, by the sickness benefit), not by the wage.

The statute settles those two. For the other absences (unpaid leave, nursing,
maternity and parental leave, obstacles in work) the day stays the holiday,
as both engines have always filed it.
"""

# Czech payroll codes of the absences that keep a public holiday.
ABSENCES_OVER_A_PUBLIC_HOLIDAY = ("CZSICK",)


def absence_keeps_public_holiday(code):
    """Whether a public holiday inside an absence of ``code`` is that absence."""
    return code in ABSENCES_OVER_A_PUBLIC_HOLIDAY
