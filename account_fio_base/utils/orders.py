# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Fio payment-order file builder (``importIB.xsd``).

Reference: *FIO API BANKOVNICTVÍ* v1.9, §6.3.

Fio's own XML is the format of choice for CZ/SK because it is the only one
that carries **KS / VS / SS as first-class elements**; ``pain.001`` is EUR-only
(§6.4.1) and ABO is CZK-domestic-only (§6.2).

Three order kinds, and §6.3 is explicit that they must appear in this order or
the whole file is rejected:

1. ``DomesticTransaction`` — CZ account number + bank code (§6.3.1). Also
   usable for a non-CZK transfer between two Fio accounts.
2. ``T2Transaction`` — Europlatba: EUR to a SEPA IBAN (§6.3.2).
3. ``ForeignTransaction`` — everything else (§6.3.3); every beneficiary
   address field, the charge bearer and the platební titul are mandatory here.

The builder takes :class:`FioOrder` tuples, which the Community and Enterprise
bridges produce from the shared ``BankPaymentItem`` of
``account_cz_bankfile_base`` through :func:`order_from_item`. Both editions
therefore emit byte-identical files.
"""

import re
from collections import namedtuple
from decimal import ROUND_HALF_UP, Decimal

from lxml import etree

from odoo.addons.account_cz_bankfile_base.utils.common import (
    fold_to_ascii,
    parse_cz_account,
    parse_national_account,
)

from .payment_reason import is_valid_payment_reason

SCHEMA_LOCATION = "http://www.fio.cz/schema/importIB.xsd"
XSI = "http://www.w3.org/2001/XMLSchema-instance"

KIND_DOMESTIC = "domestic"
KIND_EURO = "euro"
KIND_FOREIGN = "foreign"
#: Emission order — §6.3 rejects the file if it is broken.
KIND_SEQUENCE = (KIND_DOMESTIC, KIND_EURO, KIND_FOREIGN)

ELEMENT_BY_KIND = {
    KIND_DOMESTIC: "DomesticTransaction",
    KIND_EURO: "T2Transaction",
    KIND_FOREIGN: "ForeignTransaction",
}

#: §6.3.1 / §6.3.2 payment types. Standard unless the caller asks otherwise.
PAYMENT_TYPE_DOMESTIC_STANDARD = "431001"
PAYMENT_TYPE_DOMESTIC_PRIORITY = "431005"
PAYMENT_TYPE_DOMESTIC_DIRECT_DEBIT = "431022"
PAYMENT_TYPE_EURO_STANDARD = "431008"
PAYMENT_TYPE_EURO_PRIORITY = "431009"
PAYMENT_TYPE_EURO_INSTANT = "431018"

#: §6.3.3 detailsOfCharges, keyed by the ISO 20022 charge bearer that
#: ``account_iso20022`` stores on the payment.
CHARGE_BEARER_BY_ISO = {
    "DEBT": "470501",  # OUR  — payer bears everything
    "CRED": "470502",  # BEN  — beneficiary bears everything
    "SHAR": "470503",  # SHA  — shared
    "SLEV": "470503",  # service level, treated as shared
}
CHARGE_BEARER_DEFAULT = "470503"

_SEPA_COUNTRIES = frozenset("""
AT BE BG CH CY CZ DE DK EE ES FI FR GB GI GR HR HU IE IS IT LI LT LU LV MC MT
NL NO PL PT RO SE SI SK SM VA AD
""".split())

#: Fio runs one API for two countries — fio.cz and fio.sk share
#: ``fioapi.fio.cz/v1/rest`` and one specification — so the *ordering* account
#: may be Czech or Slovak. Both IBAN forms have to parse into ``accountFrom``.
FIO_COUNTRIES = ("CZ", "SK")

#: §6.3.2: on a Europlatba the platební titul is mandatory "jen u účtů vedených
#: Fio bankou, pobočce zahraniční banky v SR, pouze při platbě nad 50 000 EUR".
#: It is the specification's only rule that turns on where the *payer* banks.
EURO_PAYMENT_REASON_THRESHOLD = Decimal("50000")

#: Fio's own two bank codes, used only to place the **ordering** account when it
#: is configured in the national ``account/bank`` form, which names no country.
#: ``accountFrom`` is by definition a Fio account, so two entries cover it — this
#: is not, and must not become, a general CZ/SK bank-code table.
#: 2010 is stated throughout the specification ("v rámci Fio banky (kód banky
#: 2010)"); 8330 is the code in its own Slovak IBAN example,
#: ``SK6383300000000000000123`` (§6.4.2).
FIO_BANK_CODE_COUNTRY = {"2010": "CZ", "8330": "SK"}

_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{6,30}$")
_DIGITS_RE = re.compile(r"\D")

# The `i` data type (§4): alphanumeric with diacritics, plus these characters.
_ALLOWED_PUNCT = " ,./-"


class FioOrderError(ValueError):
    """A payment cannot be expressed as a Fio order. Carries the line label."""


FioOrder = namedtuple("FioOrder", [
    "kind",              # one of KIND_*
    "amount",            # Decimal / float
    "currency",          # ISO 4217
    "date",              # datetime.date
    "account_to",        # domestic: '2212-2000000699'; otherwise an IBAN
    "bank_code",         # domestic only, 4 digits
    "bic",
    "vs", "ks", "ss",
    "message",           # messageForRecipient (domestic) / remittance (other)
    "comment",
    "benef_name", "benef_street", "benef_city", "benef_country",
    "payment_reason",    # platební titul
    "charge_bearer",     # 470501 / 470502 / 470503
    "payment_type",
    "label",             # human reference, used only in error messages
])
FioOrder.__new__.__defaults__ = (None,) * 18


# ----------------------------------------------------------------------
# text/number formatting per the §4 data types
# ----------------------------------------------------------------------

def _text(value, max_len, ascii_only=False):
    """Render a text field: fold, strip disallowed characters, truncate."""
    if not value:
        return None
    text = str(value)
    if ascii_only:
        text = fold_to_ascii(text)
    text = "".join(
        c for c in text if c.isalnum() or c in _ALLOWED_PUNCT
    )
    text = re.sub(r"\s+", " ", text).strip()
    return text[:max_len] or None


def _digits(value, max_len):
    """Symbols are numeric fields; a non-numeric symbol is dropped, not sent."""
    if not value:
        return None
    text = _DIGITS_RE.sub("", str(value))
    return text[:max_len] or None


def _amount(value):
    """``18d`` — decimal point, two places."""
    return str(Decimal(str(value)).quantize(Decimal("0.01"), ROUND_HALF_UP))


def account_from_country(partner_bank):
    """Country of the ordering account: ``'CZ'``, ``'SK'`` or ``None``.

    ``None`` means "not determinable" — either no account is configured, or it
    is in the national ``account/bank`` form, which carries no country. Callers
    must treat that as "no country-specific rule applies" rather than as CZ.
    """
    try:
        return _account_from(partner_bank)[0]
    except (FioOrderError, ValueError):
        return None


def _account_from(partner_bank):
    """``(country, account)`` — the orderer's ``accountFrom`` (``16n``, digits).

    Accepts a Slovak IBAN as well as a Czech one: Fio operates in both
    countries on this one API, and a Fio SK journal is normally configured with
    its SK IBAN. Restricting this to CZ made every payment order from a Slovak
    Fio account die here, and die badly — ``parse_cz_account`` raises a plain
    ``ValueError``, which the bridges' ``except FioOrderError`` does not catch,
    so it surfaced as a traceback rather than as a message.
    """
    try:
        country, prefix, account, bank = parse_national_account(
            partner_bank, FIO_COUNTRIES,
        )
    except ValueError as exception:
        raise FioOrderError(
            "The ordering account is not usable as Fio's accountFrom: %s"
            % exception
        ) from None
    if country is None:
        # The national ``account/bank`` form names no country, but this is the
        # payer's own Fio account, so its bank code does.
        country = FIO_BANK_CODE_COUNTRY.get(bank)
    if prefix and prefix.strip("0"):
        raise FioOrderError(
            "Fio's accountFrom is a plain number (16n) and cannot carry the "
            "prefix %s- of account %s. Configure the journal with the account "
            "number Fio itself shows." % (prefix, partner_bank.acc_number)
        )
    return country, account


# ----------------------------------------------------------------------
# classification
# ----------------------------------------------------------------------

def _iban(partner_bank):
    acc = (partner_bank.acc_number or "").strip().upper().replace(" ", "")
    return acc if _IBAN_RE.match(acc) else None


def classify(partner_bank, currency_name):
    """Decide which Fio order element a payment belongs in.

    * A **Czech** account — a ``CZ`` IBAN, or the national
      ``[prefix-]account/bank`` form — is domestic, whatever the currency:
      §6.3.1 explicitly allows a foreign-currency transfer between Fio
      accounts through this element.
    * **EUR to a SEPA IBAN** is a Europlatba.
    * Anything else is a foreign payment.

    A Slovak IBAN therefore becomes a Europlatba rather than a domestic order,
    which is what Fio CZ wants — §6.3.1 is titled "platba v rámci ČR", and
    §6.2 states outright that EUR orders to Slovak banks are no longer
    accepted on the domestic path.

    **And it is what a Fio SK account wants too**, which is not obvious and was
    worth checking rather than assuming. Fio runs one API and publishes one
    specification for both countries — fio.sk serves the same Czech document,
    only an older revision — so there is no Slovak domestic order type. The
    specification's single Slovak-specific rule is the conditional
    ``paymentReason`` in §6.3.2, "povinný jen u účtů vedených Fio bankou,
    pobočce zahraniční banky v SR", and it sits in the **Europlatba** table.
    That the rule is written there is the evidence that SK-held accounts pay
    through ``T2Transaction``. ``T2Transaction`` also carries ``ks``/``vs``/
    ``ss`` natively, so nothing is lost by routing a Slovak payment through it.
    """
    iban = _iban(partner_bank)
    if iban:
        country = iban[:2]
        if country == "CZ":
            return KIND_DOMESTIC
        if currency_name == "EUR" and country in _SEPA_COUNTRIES:
            return KIND_EURO
        return KIND_FOREIGN
    # No IBAN: the national BBAN form is the only thing Fio can read here.
    try:
        parse_cz_account(partner_bank)
    except ValueError:
        raise FioOrderError(
            "Account %r is neither an IBAN nor a national account/bank number, "
            "so Fio cannot be told where to send the money."
            % (partner_bank.acc_number or "")
        ) from None
    return KIND_DOMESTIC


def order_from_item(item, kind=None, payment_reason=None, payment_type=None,
                    charge_bearer=None):
    """Turn a shared ``BankPaymentItem`` into a :class:`FioOrder`.

    Called by both the Community and the Enterprise bridge, so the mapping —
    and every validation error message — exists once.
    """
    partner_bank = item.partner_bank
    if not partner_bank:
        raise FioOrderError(
            "%s has no recipient bank account." % (item.label or "A payment")
        )
    kind = kind or classify(partner_bank, item.currency_name)
    partner = item.partner
    country_code = None
    if partner and partner.country_id:
        country_code = partner.country_id.code

    if kind == KIND_DOMESTIC:
        prefix, account, bank_code = parse_cz_account(partner_bank)
        account_to = "%s-%s" % (prefix, account) if prefix else account
    else:
        account_to = _iban(partner_bank)
        bank_code = None
        if not account_to:
            raise FioOrderError(
                "%s needs an IBAN: Fio accepts only IBANs outside domestic "
                "payments." % (item.label or "A payment")
            )

    bearer = charge_bearer or CHARGE_BEARER_BY_ISO.get(
        item.iso_charge_bearer, CHARGE_BEARER_DEFAULT
    )
    if payment_type is None and item.iso_priority == "URGP":
        payment_type = (
            PAYMENT_TYPE_DOMESTIC_PRIORITY if kind == KIND_DOMESTIC
            else PAYMENT_TYPE_EURO_PRIORITY
        )

    return FioOrder(
        kind=kind,
        amount=item.amount,
        currency=item.currency_name,
        date=item.date,
        account_to=account_to,
        bank_code=bank_code,
        bic=getattr(partner_bank, "bank_bic", None) or None,
        vs=item.vs,
        ks=item.ks,
        ss=item.ss,
        message=item.message,
        comment=item.message,
        benef_name=partner.name if partner else None,
        benef_street=partner.street if partner else None,
        benef_city=partner.city if partner else None,
        benef_country=country_code,
        payment_reason=payment_reason,
        charge_bearer=bearer,
        payment_type=payment_type,
        label=item.label,
    )


# ----------------------------------------------------------------------
# validation + rendering
# ----------------------------------------------------------------------

def validate_order(order, home_country=None):
    """Return a list of human-readable problems with ``order``.

    Returned rather than raised so the callers can report every bad payment in
    one pass instead of stopping at the first — the batch-payment framework
    shows a list, and so does the payment order's pre-flight check.

    :param home_country: where the *ordering* account is held (``'CZ'`` /
        ``'SK'`` / ``None``), from :func:`account_from_country`. Only §6.3.2's
        platební-titul threshold depends on it; pass ``None`` and that one rule
        is skipped.
    """
    problems = []
    what = order.label or "payment"
    if not order.amount or Decimal(str(order.amount)) <= 0:
        problems.append("%s: the amount must be positive." % what)
    if not order.currency:
        problems.append("%s: no currency." % what)
    if not order.date:
        problems.append("%s: no execution date." % what)
    if not order.account_to:
        problems.append("%s: no recipient account." % what)

    if order.kind == KIND_DOMESTIC:
        if not order.bank_code:
            problems.append("%s: no recipient bank code." % what)
    else:
        if not _text(order.benef_name, 35, ascii_only=True):
            problems.append(
                "%s: Fio requires the beneficiary's name (benefName) on "
                "Europlatba and foreign payments." % what
            )
    if (
        order.kind == KIND_EURO
        and home_country == "SK"
        and order.amount
        and Decimal(str(order.amount)) > EURO_PAYMENT_REASON_THRESHOLD
        and not is_valid_payment_reason(order.payment_reason)
    ):
        # §6.3.2 — mandatory only for accounts held at Fio's Slovak branch, and
        # only above 50 000 EUR. Everywhere else the field stays optional.
        problems.append(
            "%s: a Europlatba over %s EUR from an account held at Fio's Slovak "
            "branch needs a valid platební titul (3 digits, ČNB code list); "
            "got %r."
            % (what, EURO_PAYMENT_REASON_THRESHOLD, order.payment_reason)
        )
    if order.kind == KIND_FOREIGN:
        if not order.bic:
            problems.append("%s: a foreign payment needs the recipient BIC." % what)
        for value, field in (
            (order.benef_street, "street"),
            (order.benef_city, "city"),
            (order.benef_country, "country"),
        ):
            if not value:
                problems.append(
                    "%s: Fio requires the beneficiary's %s on a foreign "
                    "payment." % (what, field)
                )
        if not _text(order.message, 35, ascii_only=True):
            problems.append(
                "%s: a foreign payment needs a payment reference "
                "(remittanceInfo1)." % what
            )
        if not is_valid_payment_reason(order.payment_reason):
            problems.append(
                "%s: a foreign payment needs a valid platební titul "
                "(3 digits, ČNB code list); got %r."
                % (what, order.payment_reason)
            )
    return problems


def _append(parent, tag, value):
    if value in (None, "", False):
        return
    etree.SubElement(parent, tag).text = str(value)


def _build_domestic(parent, order, account_from):
    el = etree.SubElement(parent, "DomesticTransaction")
    _append(el, "accountFrom", account_from)
    _append(el, "currency", order.currency)
    _append(el, "amount", _amount(order.amount))
    _append(el, "accountTo", order.account_to)
    _append(el, "bankCode", order.bank_code)
    _append(el, "ks", _digits(order.ks, 4))
    _append(el, "vs", _digits(order.vs, 10))
    _append(el, "ss", _digits(order.ss, 10))
    _append(el, "date", order.date.strftime("%Y-%m-%d"))
    _append(el, "messageForRecipient", _text(order.message, 140))
    _append(el, "comment", _text(order.comment, 255))
    _append(el, "paymentReason", _digits(order.payment_reason, 3))
    _append(el, "paymentType", order.payment_type)


def _build_euro(parent, order, account_from):
    el = etree.SubElement(parent, "T2Transaction")
    _append(el, "accountFrom", account_from)
    _append(el, "currency", order.currency)
    _append(el, "amount", _amount(order.amount))
    _append(el, "accountTo", order.account_to)
    _append(el, "ks", _digits(order.ks, 4))
    _append(el, "vs", _digits(order.vs, 10))
    _append(el, "ss", _digits(order.ss, 10))
    _append(el, "bic", order.bic)
    _append(el, "date", order.date.strftime("%Y-%m-%d"))
    _append(el, "comment", _text(order.comment, 140, ascii_only=True))
    _append(el, "benefName", _text(order.benef_name, 35, ascii_only=True))
    _append(el, "benefStreet", _text(order.benef_street, 35, ascii_only=True))
    _append(el, "benefCity", _text(order.benef_city, 35, ascii_only=True))
    _append(el, "benefCountry", order.benef_country)
    for index, chunk in enumerate(_remittance(order.message, 3), start=1):
        _append(el, "remittanceInfo%s" % index, chunk)
    _append(el, "paymentReason", _digits(order.payment_reason, 3))
    _append(el, "paymentType", order.payment_type)


def _build_foreign(parent, order, account_from):
    el = etree.SubElement(parent, "ForeignTransaction")
    _append(el, "accountFrom", account_from)
    _append(el, "currency", order.currency)
    _append(el, "amount", _amount(order.amount))
    _append(el, "accountTo", order.account_to)
    _append(el, "bic", order.bic)
    _append(el, "date", order.date.strftime("%Y-%m-%d"))
    _append(el, "comment", _text(order.comment, 140, ascii_only=True))
    _append(el, "benefName", _text(order.benef_name, 35, ascii_only=True))
    _append(el, "benefStreet", _text(order.benef_street, 35, ascii_only=True))
    _append(el, "benefCity", _text(order.benef_city, 35, ascii_only=True))
    _append(el, "benefCountry", order.benef_country)
    for index, chunk in enumerate(_remittance(order.message, 4), start=1):
        _append(el, "remittanceInfo%s" % index, chunk)
    _append(el, "detailsOfCharges", order.charge_bearer or CHARGE_BEARER_DEFAULT)
    _append(el, "paymentReason", _digits(order.payment_reason, 3))


def _remittance(message, slots):
    """Split the payment reference into the 35-character remittance slots."""
    text = _text(message, 35 * slots, ascii_only=True)
    if not text:
        return []
    return [text[i:i + 35] for i in range(0, len(text), 35)][:slots]


_BUILDERS = {
    KIND_DOMESTIC: _build_domestic,
    KIND_EURO: _build_euro,
    KIND_FOREIGN: _build_foreign,
}


def build_fio_import_xml(orders, account_from_bank, validate=True):
    """Render ``orders`` as an ``importIB.xsd`` payload.

    :param account_from_bank: the ``res.partner.bank`` of the ordering journal.
    :raises FioOrderError: if ``validate`` and any order is incomplete; the
        message lists every problem, not just the first.
    """
    orders = list(orders)
    if not orders:
        raise FioOrderError("There is nothing to send.")
    home_country, account_from = _account_from(account_from_bank)

    if validate:
        problems = []
        for order in orders:
            problems.extend(validate_order(order, home_country))
        if problems:
            raise FioOrderError("\n".join(problems))

    root = etree.Element("Import", nsmap={"xsi": XSI})
    root.set("{%s}noNamespaceSchemaLocation" % XSI, SCHEMA_LOCATION)
    container = etree.SubElement(root, "Orders")
    for kind in KIND_SEQUENCE:
        for order in orders:
            if order.kind == kind:
                _BUILDERS[kind](container, order, account_from)
    return etree.tostring(
        root, xml_declaration=True, encoding="UTF-8", pretty_print=True,
    )
