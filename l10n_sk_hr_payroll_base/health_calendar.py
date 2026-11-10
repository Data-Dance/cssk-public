# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Calendar facts shared by health payroll, 514 and registration adapters.

Intervals are reviewed legal facts, not guessed from a salary or a working
schedule. 2D intervals already include any qualifying weekly rest days. 2Y
facts identify the single statutory day; this function never invents a
payment date. Callers scope identities, insurer and evidence before calling.
"""

from calendar import monthrange
from datetime import date, timedelta

KINDS = frozenset(
    {
        "2",
        "2D",
        "2Y",
        "2N",
        "benefit",
        "state",
        "disabled",
        "self_employed",
        "missing",
        "other_employment",
    }
)


def _date(value):
    if isinstance(value, date):
        return value
    return date.fromisoformat(value)


def month_context(intervals, month):
    """Return distinct statutory day counts and month-wide status facts.

    A PN/benefit day reduces report/minimum days, but does not shorten PP OP
    employment. A no-income 2N day does shorten it. Disability on one day
    changes the monthly rate (§12(3)); insurer minimum-advance guidance
    exempts this whole month. Other minimum exceptions are daily unions.
    No monetary rate/minimum formula is duplicated here.
    """
    month = _date(month).replace(day=1)
    last = month.replace(day=monthrange(month.year, month.month)[1])
    days = {kind: set() for kind in KINDS}
    for row in intervals:
        if set(row) != {"kind", "start", "end"} or row["kind"] not in KINDS:
            raise ValueError("Unknown or incomplete health-calendar interval")
        start = _date(row["start"])
        end = _date(row["end"]) if row["end"] else None
        if end and end < start:
            raise ValueError("A health-calendar interval ends before it starts")
        if row["kind"] == "2Y" and end != start:
            raise ValueError("A 2Y source must identify its single calendar day")
        lo, hi = max(start, month), min(end or last, last)
        if lo <= hi:
            days[row["kind"]].update(
                lo + timedelta(days=n) for n in range((hi - lo).days + 1)
            )
    role = days["2"] | days["2D"] | days["2Y"]
    employed = role - days["2N"]
    op_employment = days["2"] - days["2N"]
    insured = employed - days["benefit"]
    minimum = (
        employed
        - days["benefit"]
        - days["state"]
        - days["disabled"]
        - days["self_employed"]
        - days["missing"]
    )
    if days["disabled"]:
        minimum.clear()
    return {
        "month_start": month.isoformat(),
        "month_end": last.isoformat(),
        "calendar_days": last.day,
        "employment_days": len(employed),
        "op_employment_days": len(op_employment),
        "insured_days": len(insured),
        "minimum_days": len(minimum),
        "disability_in_month": bool(days["disabled"]),
        "concurrent_self_employment": bool(op_employment & days["self_employed"]),
        "concurrent_other_employment": bool(op_employment & days["other_employment"]),
        "insured_dates": sorted(value.isoformat() for value in insured),
        "minimum_dates": sorted(value.isoformat() for value in minimum),
    }
