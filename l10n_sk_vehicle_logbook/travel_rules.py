# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Statutory arithmetic of domestic business trips (zákon 283/2002 Z. z.).

Kept free of the ORM so the rules can be read and tested on their own.
"""

import math
from datetime import timedelta

import pytz

from odoo.tools import float_round

def _cents(value):
    """Half-up to the cent; ``round`` would turn 35.995 into 35.99."""
    return float_round(value, precision_digits=2)


TIMEZONE = pytz.timezone("Europe/Bratislava")
BREAKFAST, LUNCH, DINNER = 0.25, 0.40, 0.35


def hours_by_local_day(start_utc, end_utc):
    """Split a naive-UTC interval at Slovak local midnights: ``{date: hours}``."""
    start = pytz.utc.localize(start_utc).astimezone(TIMEZONE)
    end = pytz.utc.localize(end_utc).astimezone(TIMEZONE)
    result = {}
    cursor = start
    while cursor < end:
        next_day = TIMEZONE.localize(
            cursor.replace(tzinfo=None, hour=0, minute=0, second=0, microsecond=0)
            + timedelta(days=1)
        )
        stop = min(next_day, end)
        result[cursor.date()] = (stop - cursor).total_seconds() / 3600.0
        cursor = stop
    return result


def meal_rate(hours, rate_5_12, rate_12_18, rate_18):
    """§ 5 ods. 1: the band of one calendar day; under 5 hours earns nothing."""
    if hours < 5:
        return 0.0
    if hours <= 12:
        return rate_5_12
    if hours <= 18:
        return rate_12_18
    return rate_18


def meal_allowance(rate, rate_18, breakfast=False, lunch=False, dinner=False):
    """§ 5 ods. 6: free meals reduce by a share of the over-18-hour rate."""
    share = BREAKFAST * bool(breakfast) + LUNCH * bool(lunch) + DINNER * bool(dinner)
    return max(0.0, _cents(rate - rate_18 * share))


def kilometre_allowance(kilometres, rate, trailer=False):
    """§ 7 ods. 1 a 2: every started kilometre; a trailer adds 15 %."""
    return _cents(math.ceil(kilometres) * rate * (1.15 if trailer else 1.0))


def fuel_allowance(kilometres, consumption_per_100, unit_price):
    """§ 7 ods. 4: every started kilometre at the documented unit price."""
    return _cents(math.ceil(kilometres) * consumption_per_100 / 100.0 * unit_price)
