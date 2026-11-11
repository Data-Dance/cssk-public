# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""OZNDFTv26 arithmetic and XML from reviewed individual transaction facts.

This layer is not a ledger, proof of source completeness or native filing
workflow. Exempt/bank-collected rows remain evidence but are not taxed twice.
"""

from collections import defaultdict
from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from lxml import etree
from odoo.tools.translate import LazyTranslate

_lt = LazyTranslate(__name__, default_lang="en_US")

SCHEMA_SHA256 = "95d02589e13fc175935b86735de9cf1ba3bfb6fb3bbc0d7927e87367f3811c52"
CENT = Decimal("0.01")
KINDS = {
    "transfer": 1,
    "cash": 2,
    "card": 3,
    "recharge_unknown": 4,
    "recharge_known": 5,
}


def number(value, *, signed=False, cents=False):
    try:
        result = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError(_lt("Enter a finite tax amount")) from exc
    if not result.is_finite() or not signed and result < 0:
        raise ValueError(_lt("Enter a finite nonnegative tax amount"))
    if cents and result != result.quantize(CENT):
        raise ValueError(_lt("A tax amount must contain whole cents"))
    return result


def money(value):
    return format(
        number(value, signed=True).quantize(CENT, rounding=ROUND_HALF_UP), ".2f"
    )


def day(value):
    return date.fromisoformat(str(value))


def period_bounds(period, first=None, last=None):
    """OZNDFTv26 retains month/year even with exact partial-month dates."""
    month = day(period + "-01")
    end = month.replace(day=monthrange(month.year, month.month)[1])
    if bool(first) != bool(last):
        raise ValueError(_lt("Enter both exact partial-month dates"))
    if first:
        first, last = day(first), day(last)
        # Match the authority form's strict from-before-to control.
        if not month <= first < last <= end:
            raise ValueError(
                _lt("Partial-month dates must be ordered within the reported month")
            )
        return first, last
    return month, end


def transaction_tax(base, kind):
    """Round TAX, never the converted base; minimum applies per transaction."""
    base = number(base)
    if kind not in KINDS:
        raise ValueError(_lt("Review the transaction tax kind"))
    if kind == "card":
        if base != base.to_integral_value():
            raise ValueError(_lt("The number of used cards must be an integer"))
        return base * 2
    tax = base * Decimal("0.008" if kind == "cash" else "0.004")
    if kind in {"transfer", "recharge_known"}:
        tax = min(tax, Decimal(40))
    tax = tax.quantize(CENT, rounding=ROUND_HALF_UP)
    return max(tax, CENT) if base else Decimal(0)


def calculate(rows, period, adjustments=(), recharge_history=()):
    """Reviewed EUR bases; FX provenance and native source checks live above."""
    month = day(period + "-01")
    if month.year < 2026:
        raise ValueError(
            _lt(
                "Use the historical form for periods before 2026 (April-December 2025 notices, corrections and 2025 card tax require OZNDFTv25)"
            )
        )
    totals = defaultdict(Decimal)
    seen, cards = {}, set()
    previous_base, previous_tax, previous_kind = (
        defaultdict(Decimal),
        defaultdict(Decimal),
        {},
    )
    for record in recharge_history:
        key, kind = record["transaction_key"], record["kind"]
        if kind not in {"recharge_known", "recharge_unknown", "recharge_excluded"}:
            raise ValueError(_lt("Review the retained recharge classification"))
        if key in previous_kind and previous_kind[key] != kind:
            raise ValueError(
                _lt("Correct inconsistent historical recharge classifications first")
            )
        previous_kind[key] = kind
        previous_base[key] += number(record["base_eur"])
        previous_tax[key] += number(record["tax"])
    for key, kind in previous_kind.items():
        if kind == "recharge_known" and previous_tax[key] != transaction_tax(
            previous_base[key], kind
        ):
            raise ValueError(
                _lt(
                    "Correct the previously filed identified recharge tax before applying its remaining cap"
                )
            )
    current_base, current_tax = defaultdict(Decimal), defaultdict(Decimal)
    facts = []
    for row in rows:
        reference = (row.get("source_reference") or "").strip()
        key = row.get("transaction_key")
        if not row.get("reviewed") or not reference or not key:
            raise ValueError(
                _lt("Review each transaction and retain its unique source evidence")
            )
        kind = row["kind"]
        if key in seen and (not kind.startswith("recharge_") or seen[key] != kind):
            raise ValueError(
                _lt(
                    "Reconcile duplicate or split source transactions before calculation"
                )
            )
        seen[key] = kind
        if key in previous_kind and previous_kind[key] != kind:
            raise ValueError(
                _lt(
                    "Correct the historical recharge classification before using the same transaction again"
                )
            )
        actual = day(row["actual_on"])
        if kind == "card":
            if month.month != 12 or actual.year != month.year:
                raise ValueError(
                    _lt("Annual used-card tax belongs to December of its usage year")
                )
            card = row.get("card_reference")
            if not card or card in cards:
                raise ValueError(
                    _lt(
                        "Retain one annual usage fact per unique card, without its full PAN"
                    )
                )
            cards.add(card)
            base = Decimal(1)
        else:
            if actual.strftime("%Y-%m") != period:
                raise ValueError(
                    _lt("Use the actual transaction or recharge-payment month")
                )
            base = number(row["base_eur"])
        if kind in {"excluded", "bank_collected", "recharge_excluded"}:
            if not (row.get("classification_reference") or "").strip():
                raise ValueError(
                    _lt("Retain the exemption or bank-collection classification proof")
                )
            facts.append({**row, "tax": "0.00"})
            continue
        if kind == "recharge_known":
            # One cap per identified original transaction, including split
            # reimbursements. Only the newly accrued tax belongs to this month.
            current_base[key] += base
            accrued = transaction_tax(previous_base[key] + current_base[key], kind)
            tax = accrued - previous_tax[key] - current_tax[key]
            current_tax[key] += tax
        else:
            tax = transaction_tax(base, kind)
        line = KINDS[kind]
        totals[f"r{line}s1"] += base
        totals[f"r{line}s2"] += tax
        facts.append({**row, "tax": money(tax)})
    correction = Decimal(0)
    for adjustment in adjustments:
        if (
            not adjustment.get("reviewed")
            or not (adjustment.get("source_reference") or "").strip()
        ):
            raise ValueError(
                _lt("Retain reviewed evidence for each reduction or other correction")
            )
        correction += number(adjustment["amount"], signed=True, cents=True)
    totals["r6"] = correction
    totals["r7"] = sum(totals[f"r{i}s2"] for i in range(1, 6)) + correction
    return dict(totals), facts


def put(parent, name, value=""):
    result = etree.SubElement(parent, name)
    result.text = str(value) if value is not None else ""
    return result


def local_date(value):
    return day(value).strftime("%d.%m.%Y") if value else ""


def render(
    payer,
    period,
    rows,
    signed_on,
    *,
    grounds,
    filing_type="regular",
    discovered_on=None,
    previous_tax=None,
    adjustments=(),
    representative=None,
    refund=None,
    period_from=None,
    period_to=None,
    recharge_history=(),
):
    first, last = period_bounds(period, period_from, period_to)
    if any(
        row["kind"] != "card" and not first <= day(row["actual_on"]) <= last
        for row in rows
    ):
        raise ValueError(_lt("Use only transactions within the exact reported period"))
    totals, computed_facts = calculate(rows, period, adjustments, recharge_history)
    month = day(period + "-01")
    signed = day(signed_on)
    if signed < month or filing_type not in {"regular", "corrective", "additional"}:
        raise ValueError(_lt("Review the filing date and type"))
    if filing_type == "additional":
        if not discovered_on or day(discovered_on) > signed or previous_tax is None:
            raise ValueError(
                _lt(
                    "An additional notice needs its discovery date and previous known tax"
                )
            )
        totals["r8"] = number(previous_tax, signed=True, cents=True)
        totals["r9"] = totals["r7"] - totals["r8"]
    elif discovered_on or previous_tax is not None:
        raise ValueError(
            _lt("Discovery and previous-tax rows belong only to an additional notice")
        )
    grounds = set(grounds)
    if not grounds or not grounds <= {"c", "d", "e"}:
        raise ValueError(
            _lt("Review the corporate self-assessment grounds under section 3(3)c–e")
        )
    if any(row["kind"].startswith("recharge_") for row in rows) and "d" not in grounds:
        raise ValueError(_lt("Recharged costs require the corresponding payer grounds"))
    if not re.fullmatch(r"[0-9]{8}", payer.get("ico", "")) or not re.fullmatch(
        r"[0-9]{10}", payer.get("dic", "")
    ):
        raise ValueError(_lt("Review the corporate payer ICO and DIC"))
    if any(
        not str(payer.get(key) or "").strip()
        for key in ("name", "city", "zip", "country_name")
    ):
        raise ValueError(_lt("Complete the payer name and registered address"))
    root = etree.Element("dokument")
    head = put(root, "hlavicka")
    put(head, "ico", payer["ico"])
    put(head, "dic", payer["dic"])
    kinds = put(head, "typDP")
    for field, kind in (
        ("rdp", "regular"),
        ("odp", "corrective"),
        ("ddp", "additional"),
    ):
        put(kinds, field, int(filing_type == kind))
    put(kinds, "datumDDP", local_date(discovered_on))
    dates = put(head, "zdanovacieObdobie")
    for field, value in (
        ("mesiac", month.month),
        ("rok", month.year),
        ("od", local_date(period_from) if period_from else ""),
        ("do", local_date(period_to) if period_to else ""),
    ):
        put(dates, field, value)
    roles = put(head, "platitelDane")
    for field, letter in (
        ("poskytovatelOds3_3_a", "a"),
        ("organizcnaZlozkaOds3_3_b", "b"),
        ("danovnikMimoSrOds3_3_c", "c"),
        ("danovnikPreuctovaneOds3_3_d", "d"),
        ("danovnikFinancneTransOds3_3_e", "e"),
    ):
        put(roles, field, int(letter in grounds))
    name = put(head, "poObchodneMeno")
    put(name, "riadok", payer["name"])
    put(name, "riadok")

    def address(parent, person):
        for field, key in (
            ("ulica", "street"),
            ("cislo", "number"),
            ("psc", "zip"),
            ("obec", "city"),
            ("stat", "country_name"),
            ("telefon", "phone"),
            ("email", "email"),
        ):
            put(parent, field, person.get(key, ""))

    address(put(head, "adresaSidlo"), payer)
    representative = representative or {}
    kind = representative.get("kind")
    roles = put(head, "typZastupcu")
    if kind not in {
        "zastupca",
        "spravcaVkonkurznomKonani",
        "likvidator",
        "statutarnyZastupcaPO",
        "pravnyNastupca",
    }:
        raise ValueError(_lt("Review the submitting person's capacity"))
    if not (
        representative.get("first_name")
        and representative.get("last_name")
        or representative.get("company_name")
    ):
        raise ValueError(
            _lt("Identify the actual submitting person or legal representative")
        )
    for field in (
        "zastupca",
        "spravcaVkonkurznomKonani",
        "likvidator",
        "statutarnyZastupcaPO",
        "pravnyNastupca",
    ):
        put(roles, field, int(kind == field))
    person = put(head, "zastupca")
    for field, key in (
        ("priezvisko", "last_name"),
        ("meno", "first_name"),
        ("titul", "title_before"),
        ("titulZa", "title_after"),
        ("rodneCislo", "birth_number"),
        ("datumNarodenia", "birth_date"),
        ("dic", "dic"),
        ("obchodneMeno", "company_name"),
    ):
        value = representative.get(key, "")
        put(person, field, local_date(value) if key == "birth_date" else value)
    address(put(head, "adresaZastupcu"), representative)
    body = put(root, "telo")
    for line in range(1, 6):
        base = totals.get(f"r{line}s1", Decimal(0))
        put(body, f"r{line}s1", int(base) if line == 3 else money(base))
        put(body, f"r{line}s2", money(totals.get(f"r{line}s2", 0)))
    for field in ("r6", "r7", "r8", "r9"):
        put(body, field, money(totals[field]) if field in totals else "")
    put(body, "datumVyhlasenia", local_date(signed_on))
    request = put(body, "vratenieDane")
    refund = refund or {}
    requested = bool(refund.get("requested"))
    if requested and not (totals["r7"] < 0 or totals.get("r9", 0) < 0):
        raise ValueError(
            _lt("A refund request needs a negative total or additional difference")
        )
    if requested and not (refund.get("iban") or refund.get("foreign_account_details")):
        raise ValueError(_lt("Retain an actual refund bank destination"))
    if requested and refund.get("iban") and refund.get("foreign_account_details"):
        raise ValueError(
            _lt("Choose the IBAN or the foreign non-IBAN refund destination, not both")
        )
    if requested and (not refund.get("date") or day(refund["date"]) > signed):
        raise ValueError(_lt("Review the actual refund-request date"))
    put(request, "ziadamVratenie", int(requested))
    put(request, "iban", refund.get("iban", "") if requested else "")
    put(
        request,
        "ucetVedenyVZahranici",
        refund.get("foreign_account_details", "") if requested else "",
    )
    put(request, "datum", local_date(refund.get("date")) if requested else "")
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True)
