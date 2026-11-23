# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A public holiday that falls inside an absence.

For a monthly wage a public holiday on a usual working day is a worked day
for which the wage is due, when the employee did not work because of the
holiday (§ 122 ods. 3 Zákonníka práce). Which of the two the day is, the
holiday or the absence, depends on the absence:

* in paid leave the holiday is not a day of leave (§ 112 ods. 3), so the day
  is the holiday; an obstacle in work booked over a holiday is the holiday
  too, as no shift was missed;
* in the absences below the employee is away for the absence, not for the
  holiday, and no wage is due: sickness and nursing, for which the
  employer's sick pay and the benefits run by calendar day (§ 7 ods. 2
  zákona 462/2003 Z. z.), maternity, paternity and parental leave, and
  unpaid leave.
"""

# Slovak payroll codes of the absences that keep a public holiday.
ABSENCES_OVER_A_PUBLIC_HOLIDAY = (
    "PN",
    "OCR",
    "NEPLATENE",
    "MATERSKA",
    "RODICOVSKA",
    "OTCOVSKA",
)


def absence_keeps_public_holiday(code):
    """Whether a public holiday inside an absence of ``code`` is that absence."""
    return code in ABSENCES_OVER_A_PUBLIC_HOLIDAY
