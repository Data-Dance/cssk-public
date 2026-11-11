# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""One engine-neutral record shape for bases actually used by fund rules.

The caller owns the statutory calculation and rounding. This module records
its result; it neither recomputes a premium nor infers a base from a premium.
Decimal strings survive JSON storage without losing a rule's precision.
They can include float artefacts; consumers apply statutory wire-base rounding
before serialization, rather than reporting raw fractional cents.
Bases and charges retain the rule's sign, including negative corrections.
Any additional native refund direction belongs to the engine bridge.
"""

from decimal import Decimal, InvalidOperation
import json
import math
import re

SIDES = frozenset({"employee", "employer"})
RECORD_FIELDS = frozenset({"fund", "base", "rate", "amount", "side", "facts"})
FUND_CODE = re.compile(r"[a-z][a-z0-9_]*\Z")


def _decimal(value):
    if isinstance(value, bool):
        raise ValueError("A fund amount cannot be a boolean")
    try:
        result = Decimal(str(value))
    except (InvalidOperation, TypeError, ValueError) as error:
        raise ValueError("Expected a finite fund amount") from error
    if not result.is_finite():
        raise ValueError("Expected a finite fund amount")
    return result


def _decimal_text(value):
    # Decimal.normalize() depends on the process precision and may round a
    # long value. Formatting and removing fractional zeroes preserves it.
    result = format(value, "f")
    if "." in result:
        result = result.rstrip("0").rstrip(".")
    return "0" if value == 0 else result


def _json_fact(value):
    if isinstance(value, Decimal):
        if not value.is_finite():
            raise ValueError("Fund facts must contain finite JSON values")
        return _decimal_text(value)
    if value is None or isinstance(value, (str, bool, int)):
        return value
    if isinstance(value, float) and math.isfinite(value):
        return value
    if isinstance(value, list):
        return [_json_fact(item) for item in value]
    if isinstance(value, dict) and all(isinstance(key, str) for key in value):
        return {key: _json_fact(item) for key, item in value.items()}
    raise ValueError("Fund facts must contain finite JSON values with string keys")


def fund_assessment(*, fund, side, base, rate, amount, facts=None):
    """Record one fund and side, keeping a charged zero distinct from absence."""
    if not isinstance(fund, str) or not FUND_CODE.fullmatch(fund):
        raise ValueError("Expected a stable lowercase fund identifier")
    if not isinstance(side, str) or side not in SIDES:
        raise ValueError("Expected the employee or employer fund side")
    base, rate, amount = map(_decimal, (base, rate, amount))
    if not 0 <= rate <= 100:
        raise ValueError("A fund percentage must be between zero and 100")
    if facts is not None and not isinstance(facts, dict):
        raise ValueError("Fund facts must be an object")
    return {
        "fund": fund,
        "side": side,
        "base": _decimal_text(base),
        "rate": _decimal_text(rate),
        "amount": _decimal_text(amount),
        "facts": _json_fact(facts or {}),
    }


def index_assessments(records):
    """Validate retained rows; duplicate charges must not overwrite each other."""
    if not isinstance(records, list):
        raise ValueError("Recorded fund assessments must be a list")
    result = {}
    for row in records:
        if not isinstance(row, dict) or set(row) != RECORD_FIELDS:
            raise ValueError("A recorded fund assessment has an incomplete shape")
        normalized = fund_assessment(**row)
        key = (normalized["fund"], normalized["side"])
        if key in result:
            raise ValueError("Duplicate fund and side in recorded assessments")
        result[key] = normalized
    # Assert the storage contract here, rather than allowing a caller to
    # discover an unsupported value only while exporting a statutory file.
    json.dumps(list(result.values()), allow_nan=False)
    return result
