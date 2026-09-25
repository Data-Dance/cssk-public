"""Pure helpers for the deterministic resolution layer.

The trust boundary: Claude returns natural keys; everything here is plain Python
with no model side effects, so it is easy to unit-test. Record creation lives on
the account.invoice.ai.extraction model, which calls these helpers.
"""
import re


def normalize_vat(vat):
    """Upper-case, strip everything but A-Z0-9 (so 'SK 2020 123 456' == 'SK2020123456')."""
    return re.sub(r'[^A-Z0-9]', '', (vat or '').upper())


def vat_country_prefix(vat):
    """Two-letter country prefix of a VAT number, or '' if none."""
    v = normalize_vat(vat)
    return v[:2] if len(v) >= 3 and v[:2].isalpha() else ''


def reconciles(a, b, tolerance=0.02):
    """True if two monetary amounts match within an absolute tolerance (cents)."""
    try:
        return abs(float(a) - float(b)) <= tolerance
    except (TypeError, ValueError):
        return False


def totals_consistent(totals, vat_breakdown, tolerance=0.02):
    """Validate net + vat == gross and that the VAT breakdown sums to the totals.

    Returns (ok: bool, reason: str).
    """
    if not totals:
        return False, "missing totals"
    net, vat, gross = totals.get('net'), totals.get('vat'), totals.get('gross')
    if net is None or vat is None or gross is None:
        return False, "incomplete totals (net/vat/gross)"
    if not reconciles(net + vat, gross, tolerance):
        return False, "net + VAT (%.2f) != gross (%.2f)" % (net + vat, gross)
    if vat_breakdown:
        base_sum = sum((b.get('base') or 0) for b in vat_breakdown)
        vat_sum = sum((b.get('vat_amount') or 0) for b in vat_breakdown)
        if not reconciles(base_sum, net, tolerance):
            return False, "VAT breakdown base sum (%.2f) != net (%.2f)" % (base_sum, net)
        if not reconciles(vat_sum, vat, tolerance):
            return False, "VAT breakdown VAT sum (%.2f) != VAT total (%.2f)" % (vat_sum, vat)
    return True, ""
