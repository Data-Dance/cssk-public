# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Pure parsing and mapping for Finančná správa's receipt-verification service.

No model access and no network, so every trap below is unit-testable against
the real payloads committed under ``tests/fixtures``.
"""
import re
from datetime import datetime

ENDPOINT = "https://ekasa.financnasprava.sk/mdu/api/v1/opd/receipt/find"

# The service sits behind an application firewall that rejects a default
# ``requests`` user agent with HTTP 499 and an HTML error page. These three
# headers are what make it answer.
BROWSER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/140.0.0.0 Safari/537.36"
    ),
    "Origin": "https://ekasa.financnasprava.sk",
    "Referer": "https://ekasa.financnasprava.sk/mdu/public/",
    "Accept": "application/json, text/plain, */*",
    "Content-Type": "application/json",
}

# ``O-`` for an on-line eKasa receipt, ``V-`` for one from the virtual register.
RECEIPT_ID_RE = re.compile(r"\b([A-Za-z])-([0-9A-Fa-f]{32})\b")
FS_DATETIME = "%d.%m.%Y %H:%M:%S"


class EkasaQrError(ValueError):
    """The QR payload is not something this service can be asked about."""


def parse_qr(qr):
    """Turn a decoded QR payload into the request body the service expects.

    Two shapes, because a receipt printed while the till was off-line has no
    identifier to look up::

        on-line   O-ABCDEF0000000001ABCDEF0000000001
        off-line  OKP:kódPokladnice:YYMMDDHHMMSS:poradovéČíslo:celkováSuma

    ``receiptNumber`` and ``totalAmount`` must be JSON *numbers*; sent as
    strings the service rejects the request.
    """
    raw = (qr or "").strip()
    if not raw:
        raise EkasaQrError("The QR payload is empty.")

    if ":" not in raw:
        match = RECEIPT_ID_RE.search(raw)
        if not match:
            raise EkasaQrError(
                "%r is not a receipt identifier: expected a letter, a hyphen "
                "and 32 hexadecimal characters." % raw[:80])
        return {"receiptId": "%s-%s" % (
            match.group(1).upper(), match.group(2).upper())}

    parts = raw.split(":")
    if len(parts) != 5:
        raise EkasaQrError(
            "An off-line receipt QR code has five colon-separated fields "
            "(OKP, cash-register code, date-time, number, total); this one has "
            "%d." % len(parts))
    okp, register_code, stamp, number, total = (p.strip() for p in parts)
    if not re.fullmatch(r"\d{12}", stamp):
        raise EkasaQrError(
            "%r is not a YYMMDDHHMMSS timestamp." % stamp)
    try:
        number = int(number)
        total = float(total)
    except (TypeError, ValueError) as err:
        raise EkasaQrError(
            "The receipt number and total must be numbers (%s)." % err) from err
    issued = "%s.%s.20%s %s:%s:%s" % (
        stamp[4:6], stamp[2:4], stamp[0:2], stamp[6:8], stamp[8:10], stamp[10:12])
    # Validate rather than trust: a malformed stamp would otherwise be rejected
    # by the service with an opaque error. strptime raises a bare ValueError,
    # which a caller catching EkasaQrError would not see, so it is re-raised.
    try:
        datetime.strptime(issued, FS_DATETIME)
    except ValueError as err:
        raise EkasaQrError(
            "%r is not a valid date and time (%s)." % (stamp, err)) from err
    return {
        "okp": okp,
        "cashRegisterCode": register_code,
        "issueDateFormatted": issued,
        "receiptNumber": number,
        "totalAmount": total,
    }


def is_online_qr(qr):
    """True when the payload is a bare receipt identifier."""
    try:
        return "receiptId" in parse_qr(qr)
    except EkasaQrError:
        return False


def parse_fs_datetime(value):
    """``14.03.2026 19:59:02`` → ``datetime``, or None."""
    if not value:
        return None
    try:
        return datetime.strptime(value.strip(), FS_DATETIME)
    except (TypeError, ValueError):
        return None


def _vat_buckets(receipt):
    """The per-rate VAT recap, and whether it came from a trustworthy field.

    Returns ``(buckets, warning)``. ``vatSummary`` is the only field that can be
    believed:

    * on a restaurant receipt it read 5 / 19 / 23 % while the legacy
      ``vatRateBasic`` / ``vatRateReduced`` pair beside it still said **20 / 10**
      — stale labels from the pre-2025 regime, over amounts that were correct;
    * on a fuel receipt the whole legacy pair was **null** while ``vatSummary``
      was populated.

    It also cannot represent a third rate, which Slovak hospitality produces as
    a matter of routine. The legacy pair is therefore read only when there is no
    summary at all, and doing so raises a warning.
    """
    summary = receipt.get("vatSummary") or []
    buckets = []
    for row in summary:
        rate = ((row.get("vat") or {}).get("vatRate")
                if isinstance(row.get("vat"), dict) else row.get("vatRate"))
        if rate is None:
            continue
        buckets.append({
            "vat_rate": float(rate),
            "amount_untaxed": float(row.get("vatBase") or 0.0),
            "amount_tax": float(row.get("vatAmount") or 0.0),
        })
    if buckets:
        return buckets, None

    legacy = []
    for rate_key, base_key, tax_key in (
            ("vatRateBasic", "taxBaseBasic", "vatAmountBasic"),
            ("vatRateReduced", "taxBaseReduced", "vatAmountReduced")):
        rate, base, tax = (
            receipt.get(rate_key), receipt.get(base_key), receipt.get(tax_key))
        if rate is None and base is None and tax is None:
            continue
        legacy.append({
            "vat_rate": float(rate or 0.0),
            "amount_untaxed": float(base or 0.0),
            "amount_tax": float(tax or 0.0),
        })
    # The legacy pair has two slots and stale labels. The items carry a rate
    # each, so when there is no summary they are the better source: a receipt
    # with three rates would otherwise be silently flattened into two.
    derived = _buckets_from_items(receipt)
    if derived:
        return derived, (
            "This receipt carries no vatSummary, so the VAT recap was derived "
            "from the items' own rates. The legacy basic/reduced fields were "
            "not used: they hold only two rates and their labels have been "
            "observed to be stale (20/10 where the real rates were 23/5). "
            "Check the rates against the paper before posting.")
    if legacy:
        return legacy, (
            "This receipt carries no vatSummary and no items, so the VAT recap "
            "was read from the legacy basic/reduced fields. Their rate labels "
            "have been observed to be stale (20/10 where the real rates were "
            "23/5) — check the rates before posting.")
    return [], None


def _buckets_from_items(receipt, rounding=0.01):
    """Group the items by rate and gross up each group."""
    from odoo.tools import float_round

    grouped = {}
    for item in receipt.get("items") or []:
        rate = item.get("vatRate")
        if rate is None:
            return []
        grouped.setdefault(float(rate), 0.0)
        grouped[float(rate)] += float(item.get("price") or 0.0)
    buckets = []
    for rate in sorted(grouped, reverse=True):
        gross = float_round(grouped[rate], precision_rounding=rounding)
        base = float_round(gross / (1.0 + rate / 100.0),
                           precision_rounding=rounding)
        buckets.append({
            "vat_rate": rate,
            "amount_untaxed": base,
            "amount_tax": float_round(gross - base, precision_rounding=rounding),
        })
    return buckets


def map_receipt(payload, flatten=None):
    """Map a service response onto ``cssk.receipt`` values.

    ``flatten`` collapses an item name to one line; the caller passes the
    framework's helper. Returns a plain dict of scalars plus ``lines`` and
    ``taxes`` lists, leaving ORM commands to the provider.
    """
    receipt = (payload or {}).get("receipt")
    if not receipt:
        return {}
    flatten = flatten or (lambda text, limit=None: (text or "").replace("\n", " "))
    org = receipt.get("organization") or {}
    unit = receipt.get("unit") or {}

    lines = []
    for index, item in enumerate(receipt.get("items") or []):
        item_type = (item.get("itemType") or "").upper()
        lines.append({
            "sequence": (index + 1) * 10,
            "name": flatten(item.get("name") or "", 240) or "—",
            "quantity": float(item.get("quantity") or 0.0),
            "vat_rate": float(item.get("vatRate") or 0.0),
            # 'price' is the VAT-INCLUSIVE LINE TOTAL. On the fuel receipt a
            # single line of 31.17 l reads 57.85, which is the receipt total;
            # on the restaurant bill the twelve item prices sum to exactly the
            # total. Dividing by the quantity to obtain a unit price loses
            # money: 57.85 / 31.17 is 1.855951…, and 1.86 x 31.17 is 57.98.
            "amount_total": float(item.get("price") or 0.0),
            # An off-setting item. The sign convention is not documented and we
            # have never seen one, so it is flagged and left unsigned: the
            # framework's reconciliation gate will then park the receipt rather
            # than let a guessed sign through.
            "is_negative": item_type == "Z",
        })

    taxes, warning = _vat_buckets(receipt)
    return {
        "receipt_uid": receipt.get("receiptId") or None,
        # issueDate, not createDate: they differ, by a second on the fuel
        # receipt, and the issue date is the accounting date.
        "issue_date": parse_fs_datetime(receipt.get("issueDate")),
        "amount_total": float(receipt.get("totalPrice") or 0.0),
        # organization is the legal entity; `unit` is the premises, a different
        # address entirely (a motorway service station against a city seat), so
        # it is kept as a note and never reaches the partner.
        "seller_name": org.get("name") or None,
        # icDph is NOT "SK" + dic: a VAT-group member files under the group's
        # number. On the fuel receipt dic is 2077000002 and icDph is
        # SK7199000006.
        "seller_vat": receipt.get("icDph") or org.get("icDph") or None,
        "seller_tax_id": receipt.get("dic") or org.get("dic") or None,
        "seller_reg_id": receipt.get("ico") or org.get("ico") or None,
        "seller_vat_payer": bool(org.get("vatPayer")),
        "premises_note": _premises_label(unit),
        "okp": (receipt.get("okp") or "").upper() or None,
        "is_paragon": bool(receipt.get("paragon")),
        "lines": lines,
        "taxes": taxes,
        "warning": warning,
    }


def _premises_label(unit):
    """One-line address of the premises, for a note."""
    street = " ".join(p for p in (
        unit.get("streetName"),
        unit.get("propertyRegistrationNumber"),
    ) if p)
    bits = [p for p in (street, unit.get("postalCode"),
                        unit.get("municipality")) if p]
    return ", ".join(bits) or None
