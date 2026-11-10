# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Statutory arithmetic of business trips (zákon 283/2002 Z. z.).

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


def _clip(start, end, lower, upper):
    """The part of ``[start, end)`` inside ``[lower, upper)``, or None."""
    start, end = max(start, lower), min(end, upper)
    return (start, end) if start < end else None


def split_foreign_trip(start_utc, end_utc, border_out, border_in, stays):
    """Hours of each Slovak calendar day, at home and per country abroad.

    ``stays`` is ``[(arrival_utc, key), ...]``: the trip is in country ``key``
    from its arrival until the next arrival, the first from ``border_out``
    and the last until ``border_in`` (§ 16 ods. 2: the border crossing or
    the scheduled flight decides). Returns ``{date: (home_hours, {key: hours})}``.
    """
    days = {day: [hours, {}] for day, hours in hours_by_local_day(start_utc, end_utc).items()}
    stays = sorted(stays, key=lambda stay: stay[0])
    for index, (arrival, key) in enumerate(stays):
        lower = border_out if index == 0 else arrival
        upper = stays[index + 1][0] if index + 1 < len(stays) else border_in
        span = _clip(lower, upper, border_out, border_in)
        if not span:
            continue
        for day, hours in hours_by_local_day(*span).items():
            entry = days.setdefault(day, [0.0, {}])
            entry[1][key] = entry[1].get(key, 0.0) + hours
            entry[0] -= hours
    return {day: (max(0.0, home), abroad) for day, (home, abroad) in days.items()}


def decisive_country(hours_by_country, value_of):
    """§ 13 ods. 5: most hours wins; on a tie, the better rate for the employee."""
    return max(
        hours_by_country,
        key=lambda key: (round(hours_by_country[key], 6), value_of(key)),
    )


def foreign_band_share(hours):
    """§ 13 ods. 4: 25 % up to 6 hours, 50 % up to 12, the full rate above."""
    if hours <= 0:
        return 0.0
    if hours <= 6:
        return 0.25
    if hours <= 12:
        return 0.5
    return 1.0


def foreign_meal_allowance(base, hours, breakfast=False, lunch=False, dinner=False):
    """§ 13 ods. 4 a 7: the band amount less a share of the full base rate."""
    share = BREAKFAST * bool(breakfast) + LUNCH * bool(lunch) + DINNER * bool(dinner)
    return max(0.0, _cents(base * foreign_band_share(hours) - base * share))


def pocket_money(base, hours, percent):
    """§ 14: up to 40 % of the stravné under § 13 ods. 4 a 5, before meal cuts."""
    return _cents(base * foreign_band_share(hours) * percent / 100.0)


def kilometre_allowance(kilometres, rate, trailer=False):
    """§ 7 ods. 1 a 2: every started kilometre; a trailer adds 15 %."""
    return _cents(math.ceil(kilometres) * rate * (1.15 if trailer else 1.0))


def fuel_allowance(kilometres, consumption_per_100, unit_price):
    """§ 7 ods. 4: every started kilometre at the documented unit price."""
    return _cents(math.ceil(kilometres) * consumption_per_100 / 100.0 * unit_price)
