# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""OZN4311v26, domestic resident individual dividends and mandatory Annex A.

This serializer consumes reviewed payment/remittance facts. A journal posting
alone is not proof of payment. Transport and authority acceptance are separate.
"""

from calendar import monthrange
from datetime import date
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
import re

from lxml import etree
from odoo.tools.translate import LazyTranslate
from stdnum.sk import rc as slovak_rc
from stdnum.cz.rc import get_birth_date

SCHEMA_URL = "https://ekr.financnasprava.sk/Formulare/XSD/ozn4311_2026.xsd"
SCHEMA_SHA256 = "c720c75f6158d380d825cc920522035d31df81dee31d7c9d430ccca1a779d352"
GUIDANCE_URL = "https://www.financnasprava.sk/_img/pfsedit/Dokumenty_PFS/Zverejnovanie_dok/Aktualne/DP/DPPO/2026/2026.01.15_006_PO_2026_IM_podiel_zisk.pdf"
_lt = LazyTranslate(__name__, default_lang="en_US")
CENT = Decimal("0.01")


def checked_birth_number(value, paid_on):
    """Formal §2 checks; this does not verify assignment by the ministry.

    The shared library also accepts some historic non-mod11 identifiers.
    Slovakia's §2/§10 require mod11; inconsistencies need §7 verification.
    """
    value = str(value).replace("/", "").replace(" ", "")
    month = (
        int(value[2:4])
        if value.isascii() and value.isdigit() and len(value) in (9, 10)
        else 0
    )
    if (
        not re.fullmatch(r"[0-9]{9,10}", value)
        or month not in {*range(1, 13), *range(51, 63)}
        or not slovak_rc.is_valid(value)
        or len(value) == 10
        and int(value) % 11
    ):
        raise ValueError(
            _lt(
                "Review the assigned Slovak birth number's length, birth date and mod11 checksum; request authority verification of an inconsistent identifier."
            )
        )
    if get_birth_date(value) >= day(paid_on):
        raise ValueError(
            _lt("The recipient's birth date must precede the actual income payment.")
        )
    return value


def day(value):
    if isinstance(value, date):
        return date(value.year, value.month, value.day)
    return date.fromisoformat(value)


def amount(value):
    try:
        result = Decimal(str(value))
    except InvalidOperation as exc:
        raise ValueError(
            _lt("A withholding amount must be a finite nonnegative cent amount")
        ) from exc
    if not result.is_finite() or result < 0 or result != result.quantize(CENT):
        raise ValueError(
            _lt("A withholding amount must be a finite nonnegative cent amount")
        )
    return result


def dividend_tax(gross, profit_period_start):
    """Rate follows the start of the profit's tax period, not payout year."""
    start = day(profit_period_start)
    if start < date(2017, 1, 1):
        raise ValueError(_lt("Review the separate pre-2017 dividend/health regime"))
    rate = Decimal(10 if start.year == 2024 else 7)
    return rate, (amount(gross) * rate / 100).quantize(CENT, rounding=ROUND_HALF_UP)


def income_tax(gross, kind="dividend", profit_period_start=None):
    if kind == "dividend":
        return dividend_tax(gross, profit_period_start)
    if kind == "author":
        return Decimal(19), (amount(gross) * Decimal("0.19")).quantize(
            CENT, rounding=ROUND_HALF_UP
        )
    raise ValueError(_lt("Review the statutory withholding income classification"))


def required(value, label):
    value = str(value or "").strip()
    if not value or any(ord(char) < 32 for char in value):
        raise ValueError(_lt("Missing or unsafe field: %(field)s", field=label))
    return value


def put(parent, tag, value=""):
    node = etree.SubElement(parent, tag)
    node.text = str(value)
    return node


def local_date(value):
    return day(value).strftime("%d.%m.%Y") if value else ""


def address(parent, values, *, coded=False):
    for tag, key in (
        ("ulica", "street"),
        ("supisneOrientacneCislo", "number"),
        ("psc", "zip"),
        ("obec", "city"),
        ("stat", "country_name"),
    ):
        put(parent, tag, values.get(key, ""))
    if coded:
        put(parent, "kodStatu", values.get("country_code", ""))


def render(
    payer, period, prepared_on, events, *, original_filed_on=None, filing_on=None
):
    """Complete replacement correction; never a delta. Two A slots per page.

    Each record is an actual dividend income, including separate profit
    vintages paid on one day. Tax remitted is an independent cash fact.
    The caller must resolve any multi-date partial-remittance presentation
    against the form's guidance before supplying the reviewed remittance date.
    """
    month = day(str(period) + "-01")
    if month.year < 2026:
        raise ValueError(_lt("OZN4311v26 cannot be used before 2026"))
    prepared = day(prepared_on)
    cutoff = day(filing_on) if filing_on else prepared
    if cutoff <= month.replace(day=monthrange(month.year, month.month)[1]):
        raise ValueError(
            _lt("The monthly notice is filed only after the reported month")
        )
    if prepared > cutoff:
        raise ValueError(
            _lt("The preparation date cannot follow the actual filing date")
        )
    if original_filed_on and day(original_filed_on) > prepared:
        raise ValueError(_lt("The original filing cannot be later than its correction"))
    if not re.fullmatch(r"[0-9]{10}", str(payer.get("dic", ""))):
        raise ValueError(_lt("Supply the payer's ten-digit income-tax DIC"))
    if not re.fullmatch(r"[0-9]{8}", str(payer.get("ico", ""))):
        raise ValueError(_lt("Supply the corporate payer's eight-digit ICO"))
    for key in ("name", "city", "zip", "country_name", "prepared_by"):
        required(payer.get(key), "payer " + key)
    if not events:
        raise ValueError(
            _lt("Supply the actual dividend payments, not an empty Annex A")
        )
    facts = []
    for event in events:
        if event.get("tax_residence") != "SK" or event.get("person_type") != "FO":
            raise ValueError(
                _lt(
                    "This adapter covers resident individual dividends; review Annex B/other regimes"
                )
            )
        paid = day(event["paid_on"])
        if (paid.year, paid.month) != (month.year, month.month):
            raise ValueError(
                _lt("The income payment must belong to the reported month")
            )
        kind = event.get("kind", "dividend")
        start = None
        if kind == "dividend":
            start = day(event["profit_period_start"])
            end = day(event["profit_period_end"])
            if not start <= end < paid:
                raise ValueError(_lt("Supply the actual completed profit period"))
        if kind == "author" and event.get("no_withholding_agreement"):
            raise ValueError(
                _lt(
                    "Use the no-withholding agreement notice, not a fictitious author tax deduction"
                )
            )
        gross = amount(event["gross"])
        if not gross:
            raise ValueError(_lt("A dividend income must be positive"))
        rate, expected = income_tax(gross, kind, start)
        withheld, remitted = amount(event["withheld"]), amount(event["remitted"])
        if withheld != expected:
            raise ValueError(_lt("Withheld tax disagrees with the profit-period rate"))
        if remitted > withheld:
            raise ValueError(
                _lt("Do not allocate more tax remittance than was withheld")
            )
        remitted_on = event.get("remitted_on")
        if bool(remitted) != bool(remitted_on):
            raise ValueError(
                _lt("An actual remittance needs its actual date; unpaid tax has none")
            )
        if remitted_on and day(remitted_on) > cutoff:
            raise ValueError(
                _lt("Do not report a remittance after the notice filing date")
            )
        person = event["recipient"]
        for key in (
            "first_name",
            "last_name",
            "city",
            "zip",
            "country_name",
            "country_code",
        ):
            required(person.get(key), "recipient " + key)
        if not re.fullmatch(r"[A-Z]{2}", person["country_code"]):
            raise ValueError(_lt("Supply the recipient address's ISO country code"))
        birth_number = (
            str(person.get("birth_number") or "").replace("/", "").replace(" ", "")
        )
        born = person.get("birth_date")
        if birth_number:
            if born:
                raise ValueError(
                    _lt(
                        "Use the assigned Slovak RC or date of birth when no RC is assigned"
                    )
                )
            birth_number = checked_birth_number(birth_number, paid)
        elif kind == "dividend" and (not born or day(born) >= paid):
            raise ValueError(
                _lt(
                    "A recipient without assigned Slovak RC needs the actual date of birth"
                )
            )
        facts.append((event, gross, rate, withheld, remitted, birth_number, kind))
    total_withheld = sum(row[3] for row in facts)
    total_remitted = sum(row[4] for row in facts)
    dividends = [row for row in facts if row[6] == "dividend"]
    dividend_withheld = sum((row[3] for row in dividends), Decimal(0))
    dividend_remitted = sum((row[4] for row in dividends), Decimal(0))
    pages = (len(dividends) + 1) // 2
    root = etree.Element("dokument")
    head = put(root, "hlavicka")
    put(head, "dic", payer["dic"])
    put(head, "ico", payer["ico"])

    def period_node(parent):
        node = put(parent, "zaObdobie")
        put(node, "mesiac", month.month)
        put(node, "rok", month.year)

    period_node(head)
    put(head, "dovodDoplnenia", int(bool(original_filed_on)))
    put(head, "datumPovodne", local_date(original_filed_on))
    person = put(head, "fyzickaOsoba")
    for key in ("priezvisko", "meno", "titulPred", "titulZa"):
        put(person, key)
    put(put(head, "pravnickaOsoba"), "obchodneMeno").append(etree.Element("riadok"))
    head.find("pravnickaOsoba/obchodneMeno/riadok").text = payer["name"]
    address(put(head, "sidlo"), payer)
    domestic = put(head, "adresaSr")
    for key in ("ulica", "supisneOrientacneCislo", "psc", "obec"):
        put(domestic, key)
    summary = put(head, "suhrnneUdaje")
    for tag in ("zPrijmDan01", "zPrijmDan01a", "zPrijmDan02", "zPrijmDan03", "spolu04"):
        row = put(summary, tag)
        included = tag not in ("zPrijmDan02", "zPrijmDan03")
        withheld = dividend_withheld if tag == "zPrijmDan01a" else total_withheld
        remitted = dividend_remitted if tag == "zPrijmDan01a" else total_remitted
        put(row, "danZrazena", format(withheld if included else Decimal(0), ".2f"))
        put(
            row,
            "danOdvedena",
            format(remitted if included else Decimal(0), ".2f"),
        )
    author = put(head, "vypracoval")
    prepared_date = put(author, "dna")
    for tag, value in (
        ("den", prepared.day),
        ("mesiac", prepared.month),
        ("rok", prepared.year),
    ):
        put(prepared_date, tag, value)
    put(put(author, "tel"), "cislo", payer.get("phone", ""))
    put(author, "vypr", payer["prepared_by"])
    put(head, "pocetStrPrilohyA", pages)
    put(head, "pocetStrPrilohyB", 0)
    put(head, "podpis", 0)
    body = put(root, "telo")
    for page in range(pages):
        annex = put(body, "prilohaA")
        pagination = put(annex, "strana")
        put(pagination, "aktualna", page + 1)
        put(pagination, "celkovo", pages)
        period_node(annex)
        for slot in range(2):
            index = page * 2 + slot
            row = put(annex, "udajeA_" + str(slot + 1))
            fact = dividends[index] if index < len(dividends) else None
            event = fact[0] if fact else {}
            person = event.get("recipient", {})
            put(row, "rodneCislo", fact[5] if fact else "")
            put(row, "datumNarodenia", local_date(person.get("birth_date")))
            put(row, "priezvisko", person.get("last_name", ""))
            put(row, "meno", person.get("first_name", ""))
            address(put(row, "adresa"), person, coded=True)
            details = put(row, "udajeOZrazeniAOdvedeni")
            put(details, "sumaZdanPrijmu", format(fact[1], ".2f") if fact else "")
            put(details, "datumUhrady", local_date(event.get("paid_on")))
            put(details, "sadzbaDane", str(fact[2]) if fact else "")
            put(details, "sumaZrazenejDane", format(fact[3], ".2f") if fact else "")
            put(details, "datumOdvedenia", local_date(event.get("remitted_on")))
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True)
