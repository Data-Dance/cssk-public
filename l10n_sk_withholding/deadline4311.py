# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Regular §43(11) deadline, including §27(4) days of rest."""

from datetime import date, timedelta

from dateutil.easter import easter


def regular_deadline(period):
    """Only days reachable by moving the following month's 15th are relevant.

    September 15 is not a rest day in 2026 (241/1993 §4b). Other fixed
    holidays cannot fall between a starting 15th and its next working day.
    An authority-granted different deadline is a separate evidenced input.
    """
    year = period.year + (period.month == 12)
    result = date(year, period.month % 12 + 1, 15)
    sunday = easter(year)
    rest = {sunday - timedelta(days=2), sunday + timedelta(days=1)}
    if year != 2026:
        rest.add(date(year, 9, 15))
    while result.weekday() >= 5 or result in rest:
        result += timedelta(days=1)
    return result
