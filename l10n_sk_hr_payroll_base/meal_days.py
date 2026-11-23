# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""The days of a payslip that earn a meal.

§ 152 ods. 2 Zákonníka práce: „Nárok na zabezpečenie stravovania alebo
poskytnutie finančného príspevku na stravovanie má zamestnanec, ktorý v rámci
pracovnej zmeny vykonáva prácu viac ako štyri hodiny.“ The financial
contribution of ods. 8 follows the same condition.

The meal belongs to a shift, not to hours added up over the month. A meal day
is therefore a day on which more than that many hours were worked: a
four-hour morning earns none, a day with five hours worked earns one, and two
half days do not add up to one. The further meal for a shift longer than 11
hours is the employer's option (the same paragraph: „môže“) and is not
counted.

The number of hours is the dated parameter ``l10n_sk_meal_min_hours`` of both
engines; these functions take it as an argument.

An employer may give more. § 152 ods. 9: „Zamestnávateľ môže po prerokovaní
so zástupcami zamestnancov ... c) rozšíriť okruh fyzických osôb, ktorým
zabezpečí stravovanie, a ktorým bude prispievať na stravovanie podľa odseku
3.“ For a contract of such an employer (``l10n_sk_meal_short_shift``) the
functions are called with ``any_work``: a day then earns the meal when any
work was done on it.
"""

import math

# Two lengths of work closer than this are the same length: a millionth of an
# hour is under four thousandths of a second, far below anything a schedule
# or a time sheet records and far above the noise of adding hours as binary
# fractions. Four hours that arrive as 4.0000000001 are still four hours.
HOURS_TOLERANCE = 0.000001


def shift_earns_meal(hours_worked, min_hours, any_work=False):
    """Whether a day with ``hours_worked`` earns a meal.

    More than ``min_hours``, not that many: exactly four hours earn none.
    With ``any_work`` the employer provides the meal on a shorter shift too
    (§ 152 ods. 9) and the hours to exceed are none: any work earns it, a
    day without work still does not.
    """
    if any_work:
        min_hours = 0.0
    return hours_worked - min_hours > HOURS_TOLERANCE


def count_meal_days(hours_by_day, min_hours, any_work=False):
    """Count the days that earn a meal.

    ``hours_by_day`` holds the hours worked on each day, one number a day.
    Each day is decided alone, so parts of days are never added together.
    ``any_work`` is passed on to ``shift_earns_meal``.
    """
    return float(
        sum(
            1
            for hours in hours_by_day
            if shift_earns_meal(hours, min_hours, any_work=any_work)
        )
    )


def whole_days(days):
    """The whole days in a number of days worked taken from worked-day lines.

    For a payslip whose worked-day lines were typed by hand: they hold a
    total, the days cannot be placed in the calendar, and a part of a day
    left over is not known to be a shift of more than four hours.
    """
    return float(max(0, math.floor(days + HOURS_TOLERANCE)))
