# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Calendar-day split of the employer's sick pay (§ 8 zákona 462/2003 Z. z.).

The first three days of a temporary incapacity are paid at one rate and the
following days up to the employer's limit at another. The days are calendar
days counted from the start of the incapacity, so a sickness that began last
month has already used part of its allowance when this month's payslip runs.
"""

from datetime import timedelta
from decimal import Decimal, ROUND_CEILING, ROUND_DOWN


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
