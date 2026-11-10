# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Shared assessment arithmetic for salary rules and retained fund evidence.

Act461/2003 §138(1),(5),(6),(9),(10),(13),(14), §138a: apply a
deduction to income before the applicable ceiling. Accident/guarantee do
not use the agreement deduction; accident has no ceiling.
"""

from decimal import Decimal, InvalidOperation, ROUND_DOWN


def assessment_base(gross, ceiling=None, deduction=0):
    try:
        gross = Decimal(str(gross))
        deduction = Decimal(str(deduction))
        ceiling = Decimal(str(ceiling)) if ceiling is not None else None
    except (InvalidOperation, ValueError) as error:
        raise ValueError("Assessment inputs must be finite decimal amounts") from error
    if (
        not gross.is_finite()
        or not deduction.is_finite()
        or deduction < 0
        or (ceiling is not None and (not ceiling.is_finite() or ceiling < 0))
    ):
        raise ValueError("Assessment inputs must be finite decimal amounts")
    # Keep the engine's existing signed adjustment convention. Statutory
    # declarations must handle the original/refund lifecycle separately.
    amount = max(Decimal(0), gross - deduction) if deduction else gross
    if ceiling is not None:
        amount = min(amount, ceiling)
    return float(amount.quantize(Decimal("0.01"), rounding=ROUND_DOWN))


def social_premium(base, rate):
    return float(
        (Decimal(str(base)) * Decimal(str(rate)) / Decimal(100)).quantize(
            Decimal("0.01"), rounding=ROUND_DOWN
        )
    )
