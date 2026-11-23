# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Calendar-day split of the employer's sick pay (§ 8 zákona 462/2003 Z. z.).

The first three days of a temporary incapacity are paid at one rate and the
following days up to the employer's limit at another. The days are calendar
days counted from the start of the incapacity, so a sickness that began last
month has already used part of its allowance when this month's payslip runs.
"""

from calendar import monthrange
from datetime import date, timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN

# § 54 ods. 2 zákona 461/2003 Z. z.: the insured days that decide which
# decisive period a recent employment gets.
DECISIVE_MIN_INSURED_DAYS = 90
# § 54 ods. 10 písm. a) prvý bod: an incapacity is excluded for 52 weeks at most.
EXCLUDED_INCAPACITY_MAX_DAYS = 52 * 7


def sick_pay_amount(daily_base, tier1, tier2, rate1, rate2):
    """Unrounded compensation with the employer DVZ truncated to four places."""
    values = [Decimal(str(value)) for value in (daily_base, tier1, tier2, rate1, rate2)]
    if any(not value.is_finite() or value < 0 for value in values):
        raise ValueError("Use finite nonnegative sick-pay inputs")
    base, first_days, later_days, first_rate, later_rate = values
    base = base.quantize(Decimal("0.0001"), rounding=ROUND_DOWN)
    return base * (first_days * first_rate + later_days * later_rate)


def round_sick_pay(amount):
    """Section 10(2): round the resulting compensation upward to eurocents."""
    return float(Decimal(str(amount)).quantize(Decimal("0.01"), rounding=ROUND_CEILING))


def merge_spans(spans):
    """Join overlapping or adjoining ``(start, end)`` date pairs."""
    merged = []
    for start, end in sorted(spans):
        if merged and start <= merged[-1][1] + timedelta(days=1):
            merged[-1] = (merged[-1][0], max(merged[-1][1], end))
        else:
            merged.append((start, end))
    return merged


def split_sick_days(spans, date_from, date_to, tier1_days, employer_days):
    """Return ``(tier1, tier2, calendar_days)`` for one payslip period.

    ``tier1`` and ``tier2`` count the period's days paid at each employer rate.
    ``calendar_days`` is every sick day inside the period, including those
    after the employer's limit, when the Social Insurance Agency pays.
    """
    tier1 = tier2 = calendar_days = 0
    for start, end in merge_spans(spans):
        first = max(start, date_from)
        last = min(end, date_to)
        if first > last:
            continue
        calendar_days += (last - first).days + 1
        for offset in range((first - start).days, (last - start).days + 1):
            sick_day = offset + 1
            if sick_day <= tier1_days:
                tier1 += 1
            elif sick_day <= employer_days:
                tier2 += 1
    return tier1, tier2, calendar_days


def decisive_period(insured_from, onset):
    """The decisive period for the employer's daily assessment base.

    § 8 ods. 4 zákona 462/2003 Z. z. with § 54 ods. 1 and 2 zákona 461/2003:

    * insured without a break since 1 January of the year before the
      incapacity began: that previous calendar year;
    * insured for at least 90 days: from the start of the insurance to the end
      of the month before the one in which the incapacity began;
    * insured for less: from the start of the insurance to the day before the
      incapacity.

    Returns ``(first, last)``, or ``None`` when the incapacity begins on the
    first insured day: there is no period, and the base is the one of § 8
    ods. 6 (``probable_daily_base``). The 90 days are counted as calendar
    days of the employment; days on which no premium was due are not
    subtracted here.
    """
    previous_year_start = date(onset.year - 1, 1, 1)
    if insured_from <= previous_year_start:
        return previous_year_start, date(onset.year - 1, 12, 31)
    if insured_from >= onset:
        return None
    if (onset - insured_from).days >= DECISIVE_MIN_INSURED_DAYS:
        return insured_from, onset.replace(day=1) - timedelta(days=1)
    return insured_from, onset - timedelta(days=1)


def period_months(first, last):
    """The ``(year, month)`` pairs a period touches, in order."""
    months, year, month = [], first.year, first.month
    while (year, month) <= (last.year, last.month):
        months.append((year, month))
        year, month = (year + 1, 1) if month == 12 else (year, month + 1)
    return months


def month_bounds(year, month):
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def days_in_spans(spans, first, last):
    """Calendar days of ``spans`` that fall within ``first``..``last``."""
    days = 0
    for start, end in merge_spans(spans):
        start, end = max(start, first), min(end, last)
        if start <= end:
            days += (end - start).days + 1
    return days


def daily_assessment_base(total_base, period, excluded_spans):
    """§ 8 ods. 5 and 8: the bases over the days, four places, rounded DOWN.

    ``excluded_spans`` are the periods § 54 ods. 10 takes out of the decisive
    period. Returns ``None`` when no day or no base is left, which is the
    case of § 8 ods. 6 (``probable_daily_base``).
    """
    first, last = period
    days = (last - first).days + 1 - days_in_spans(excluded_spans, first, last)
    total = Decimal(str(total_base))
    if days <= 0 or total <= 0:
        return None
    return float((total / days).quantize(Decimal("0.0001"), rounding=ROUND_DOWN))


def probable_daily_base(month_base, year, month):
    """§ 8 ods. 6 and 8: the base of the month the incapacity began in.

    For an employee with no assessment base in the decisive period the Act
    takes "the daily assessment base from which premium would be paid in the
    calendar month in which the incapacity arose". ``month_base`` is the
    base premium would be paid on for that whole month; it is divided by the
    days of the month, as ods. 5 divides the bases of a period by its days,
    and cut to four places. A month insured only in part is not handled
    here: the Act names no divisor for it.

    Returns ``None`` when there is no base.
    """
    total = Decimal(str(month_base))
    if total <= 0:
        return None
    days = monthrange(year, month)[1]
    return float((total / days).quantize(Decimal("0.0001"), rounding=ROUND_DOWN))
