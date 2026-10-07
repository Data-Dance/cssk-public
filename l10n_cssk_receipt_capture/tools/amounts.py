# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Pure money helpers for receipt capture.

Deliberately free of model access so they can be unit-tested without a cursor.
``normalize_vat`` and ``reconciles`` mirror ``account_invoice_ai_extract``'s
resolver so the two pipelines agree on what "the same supplier" and "close
enough" mean; they are duplicated rather than imported because this framework
must install without an LLM provider.
"""
import re

from odoo.tools import float_compare, float_round


def normalize_vat(vat):
    """Upper-case, strip everything but A-Z0-9 ('SK 2020 123 456' == 'SK2020123456')."""
    return re.sub(r"[^A-Z0-9]", "", (vat or "").upper())


def reconciles(a, b, tolerance=0.02):
    """True if two monetary amounts match within an absolute tolerance (cents)."""
    try:
        return abs(float(a) - float(b)) <= tolerance
    except (TypeError, ValueError):
        return False


def split_gross(gross, rate_percent, rounding=0.01):
    """Split a VAT-inclusive amount into (base, tax) at ``rate_percent``.

    Half-up to the currency precision, which is what the tax authorities' own
    recaps do: 57.85 at 23 % gives (47.03, 10.82) and 130.50 at 5 % gives
    (124.29, 6.21), both matching Finančná správa to the cent.
    """
    gross = float(gross or 0.0)
    rate = float(rate_percent or 0.0)
    base = float_round(gross / (1.0 + rate / 100.0), precision_rounding=rounding)
    return base, float_round(gross - base, precision_rounding=rounding)


def same_rate(a, b, rounding=0.01):
    """True when two VAT rates are the same rate (19.0 == 19, 19.00 != 19.5)."""
    return float_compare(float(a or 0.0), float(b or 0.0), precision_rounding=rounding) == 0


def flatten_label(text, limit=None):
    """Collapse a receipt item name to one line.

    Item names arrive with embedded newlines carrying modifiers whose money is
    already inside the parent line ("HOVÄDZÍ BBQ SET\\n1x Vysoký roštenec
    +3EUR"), so they must be flattened for a label but never split into lines.
    """
    one_line = " · ".join(
        part.strip() for part in re.split(r"[\r\n]+", text or "") if part.strip()
    )
    one_line = re.sub(r"\s{2,}", " ", one_line)
    if limit and len(one_line) > limit:
        one_line = one_line[: limit - 1].rstrip() + "…"
    return one_line
