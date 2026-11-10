# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Employee health base shared by the salary rule and the 514 adapter.

z.580/2004 §16(16–18): claimed monthly OP, phase-out on total income,
employment calendar ratio; §16(1): advance floored to a eurocent. OP is
rounded upward (insurer guidance); no employer OP since January2018.
The caller supplies dated rates/parameters and the legal income category.
This function does not infer legal status or reconstruct it from premiums.
"""

from decimal import Decimal, InvalidOperation, ROUND_DOWN, ROUND_UP

CENT = Decimal("0.01")


def _decimal(value):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Expected a finite assessment input") from exc
    if not result.is_finite():
        raise ValueError("Expected a finite assessment input")
    return result


def employee_assessment(
    income,
    op_income,
    *,
    claim,
    employment_ratio,
    rate,
    maximum,
    phaseout_end,
    exempt=False,
):
    """Return explicit bases/OP/premium; never reverse-divide rounded money.

    ``op_income`` is income from an OP-eligible employment, even when the
    employee has not claimed a monthly allowance. Other income affects the
    phase-out but cannot itself receive OP. PN days do not reduce this ratio.
    Whole-period exemptions are distinct from a concurrent-minimum opt-out.
    """
    income, op_income, ratio, rate, maximum, end = map(
        _decimal, (income, op_income, employment_ratio, rate, maximum, phaseout_end)
    )
    if not 0 <= ratio <= 1 or rate < 0 or maximum <= 0 or end <= maximum:
        raise ValueError("Invalid dated health-assessment parameters")
    if income >= 0 and not 0 <= op_income <= income:
        raise ValueError("OP-eligible income must be part of total income")
    if type(claim) is not bool or type(exempt) is not bool:
        raise ValueError("Health claims and exemption must be explicit facts")
    op = Decimal(0)
    if claim and not exempt and income > 0 and op_income > 0:
        slope = maximum / (end - maximum)
        allowance = max(Decimal(0), maximum - slope * max(Decimal(0), income - maximum))
        op = (min(allowance, op_income) * ratio).quantize(CENT, rounding=ROUND_UP)
        op = min(op, op_income)
    base = income - op
    premium = (base * rate / 100).quantize(CENT, rounding=ROUND_DOWN)
    return {
        "income": income,
        "op_income": op_income,
        "other_income": income - op_income,
        "op": op,
        "base": Decimal(0) if exempt else base,
        "employee": Decimal(0) if exempt else premium,
        "rate_employee": rate,
        "exempt": exempt,
    }


def minimum_assessment(
    base,
    employee_rate,
    employer_rate,
    days,
    month_days,
    employee,
    employer,
    *,
    opt_out=False,
):
    """§16a: floor each advance first, then the prorated monthly minimum.

    The caller supplies distinct statutory minimum days, not working days.
    A disability-month exception has zero minimum days; actual premiums
    and the employer's liability are never increased by this calculation.
    """
    base, ee_rate, er_rate, employee, employer = map(
        _decimal, (base, employee_rate, employer_rate, employee, employer)
    )
    if (
        type(days) is not int
        or type(month_days) is not int
        or not 0 <= days <= month_days
        or not 28 <= month_days <= 31
        or base < 0
        or ee_rate < 0
        or er_rate < 0
        or type(opt_out) is not bool
    ):
        raise ValueError("Invalid monthly minimum-assessment facts")
    monthly = sum(
        (base * rate / 100).quantize(CENT, rounding=ROUND_DOWN)
        for rate in (ee_rate, er_rate)
    )
    minimum = (monthly * days / month_days).quantize(CENT, rounding=ROUND_DOWN)
    actual = employee + employer
    topup = Decimal(0) if opt_out else max(Decimal(0), minimum - actual)
    return {
        "monthly_minimum": monthly,
        "minimum": minimum,
        "actual": actual,
        "topup": topup.quantize(CENT),
    }
