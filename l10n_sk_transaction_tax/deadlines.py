# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Monthly DFT deadline: 279/2024 § 10; 563/2009 § 27(4); 241/1993 § 2."""

from calendar import monthrange
from datetime import date, timedelta

from dateutil.easter import easter


def monthly_deadline(period):
    """December includes annual card tax. This is not an extension mechanism."""
    month = period.month % 12 + 1
    year = period.year + (period.month == 12)
    deadline = date(year, month, monthrange(year, month)[1])
    fixed = {
        (1, 1),
        (1, 6),
        (5, 1),
        (7, 5),
        (8, 29),
        (11, 1),
        (12, 24),
        (12, 25),
        (12, 26),
    }
    if year != 2026:
        fixed |= {(5, 8), (9, 15)}
    sunday = easter(year)
    movable = {sunday - timedelta(days=2), sunday + timedelta(days=1)}
    while (
        deadline.weekday() >= 5
        or (deadline.month, deadline.day) in fixed
        or deadline in movable
    ):
        deadline += timedelta(days=1)
    return deadline
