# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Fio movement parsers — Fio XML (primary) and Fio JSON.

Reference: *FIO API BANKOVNICTVÍ* v1.9, §5.3.1.1 (XML) and §5.3.1.6 (JSON).

Both formats carry the same numbered columns, so there is one
:data:`COLUMNS` map and one normalisation step; only the envelope differs.

**Fio XML is the primary format.** Its schema is published
(``https://www.fio.cz/xsd/IBSchema.xsd``) and its dates are unambiguous. The
JSON encoding is supported, but note that the documentation's own table calls
``dateStart`` a ``rrrr-mm-dd+GMT`` string while its own example returns epoch
milliseconds — :func:`_parse_date` therefore accepts both, and that
contradiction is the reason XML is preferred.

Traps encoded here, each covered by a test:

* **Dates carry a UTC offset but are dates, not instants.** ``2012-07-27+02:00``
  converted to UTC becomes the 26th. Only the leading ``YYYY-MM-DD`` is read.
* **Amounts are decimal strings.** Parsed through ``Decimal``; a
  ``float(str)`` round trip loses haléře on long values.
* **A reversal has a new movement id but the original instruction id** (§5.3).
  Nothing here deduplicates on ``instruction_id`` — that would swallow storno
  movements, which is a silent, balance-breaking bug.
"""

import json
from collections import namedtuple
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from zoneinfo import ZoneInfo

from lxml import etree

#: Fio stamps its JSON epoch values at the bank's local midnight, so they must
#: be read back in the bank's own zone — read as UTC, half the year lands on
#: the previous day.
_BANK_TZ = ZoneInfo("Europe/Prague")

#: ``column_NN`` id → canonical key. §5.3.1.1 / §5.3.1.6 use the same numbers.
COLUMNS = {
    0: "date",
    1: "amount",
    2: "counter_account",
    3: "counter_bank_code",
    4: "ks",
    5: "vs",
    6: "ss",
    7: "user_identification",
    8: "transaction_type",
    9: "executed_by",
    10: "counter_account_name",
    12: "counter_bank_name",
    14: "currency",
    16: "message_for_recipient",
    17: "instruction_id",
    18: "specification",
    22: "movement_id",
    25: "comment",
    26: "counter_bic",
    27: "payer_reference",
}

_INFO_FIELDS = (
    "account_id", "bank_id", "currency", "iban", "bic",
    "opening_balance", "closing_balance", "date_start", "date_end",
    "year_list", "id_list", "id_from", "id_to", "id_last_download",
)

#: ``<Info>`` / ``info`` element name → :class:`FioInfo` attribute.
_INFO_KEYS = {
    "accountId": "account_id",
    "bankId": "bank_id",
    "currency": "currency",
    "iban": "iban",
    "bic": "bic",
    "openingBalance": "opening_balance",
    "closingBalance": "closing_balance",
    "dateStart": "date_start",
    "dateEnd": "date_end",
    "yearList": "year_list",
    "idList": "id_list",
    "idFrom": "id_from",
    "idTo": "id_to",
    "idLastDownload": "id_last_download",
}

_DECIMAL_INFO = ("opening_balance", "closing_balance")
_DATE_INFO = ("date_start", "date_end")
_INT_INFO = ("year_list", "id_list", "id_from", "id_to", "id_last_download")

FioInfo = namedtuple("FioInfo", _INFO_FIELDS)
FioInfo.__new__.__defaults__ = (None,) * len(_INFO_FIELDS)

#: ``info`` is a :class:`FioInfo`; ``transactions`` a list of dicts keyed by
#: the canonical names in :data:`COLUMNS`. Absent columns are simply missing.
FioStatement = namedtuple("FioStatement", ["info", "transactions"])


class FioParseError(ValueError):
    """The payload is not a Fio movement list."""


def _parse_date(value):
    """Fio date → ``datetime.date``.

    Accepts ``'2012-07-27+02:00'`` (XML and newer JSON) and epoch milliseconds
    (older JSON). The offset is deliberately discarded: these are booking
    dates, not instants, and normalising them through UTC shifts half the year
    onto the previous day.
    """
    if value in (None, "", False):
        return None
    if isinstance(value, date) and not isinstance(value, datetime):
        return value
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, (int, float)):
        # Epoch milliseconds at the bank's local midnight (§5.3.1.6 example).
        return datetime.fromtimestamp(value / 1000.0, tz=_BANK_TZ).date()
    text = str(value).strip()
    if not text:
        return None
    if text.isdigit() and len(text) > 8:
        return _parse_date(int(text))
    try:
        return date(int(text[0:4]), int(text[5:7]), int(text[8:10]))
    except (ValueError, IndexError):
        raise FioParseError("Unparseable Fio date %r" % value) from None



def _parse_decimal(value):
    if value in (None, "", False):
        return None
    try:
        return Decimal(str(value).replace(",", ".").replace(" ", ""))
    except (InvalidOperation, ValueError):
        raise FioParseError("Unparseable Fio amount %r" % value) from None


def _parse_int(value):
    if value in (None, "", False):
        return None
    try:
        return int(str(value).strip())
    except ValueError:
        return None


def _clean(value):
    """Fio pads empty text columns with a single space."""
    if value is None:
        return None
    text = str(value).strip()
    return text or None


def _finalise_info(values):
    for key in _DECIMAL_INFO:
        values[key] = _parse_decimal(values.get(key))
    for key in _DATE_INFO:
        values[key] = _parse_date(values.get(key))
    for key in _INT_INFO:
        values[key] = _parse_int(values.get(key))
    for key in ("account_id", "bank_id", "currency", "iban", "bic"):
        values[key] = _clean(values.get(key))
    return FioInfo(**values)


def _finalise_transaction(values):
    values["date"] = _parse_date(values.get("date"))
    values["amount"] = _parse_decimal(values.get("amount"))
    for key in ("movement_id", "instruction_id"):
        values[key] = _parse_int(values.get(key))
    for key, value in list(values.items()):
        if key not in ("date", "amount", "movement_id", "instruction_id"):
            values[key] = _clean(value)
    return {k: v for k, v in values.items() if v is not None}


def _xml_parser():
    # Hardened: the payload is a bank response over TLS, but an XML parser that
    # resolves entities or fetches DTDs is a liability whatever the source.
    return etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False,
    )


def parse_fio_xml(data):
    """Parse a Fio XML movement list (§5.3.1.1) into a :class:`FioStatement`."""
    if isinstance(data, str):
        data = data.encode("utf-8")
    try:
        root = etree.fromstring(data, parser=_xml_parser())
    except etree.XMLSyntaxError as exc:
        raise FioParseError("Not valid XML: %s" % exc) from None
    if etree.QName(root).localname != "AccountStatement":
        raise FioParseError(
            "Expected an <AccountStatement> root, got <%s>"
            % etree.QName(root).localname
        )

    info_values = dict.fromkeys(_INFO_FIELDS)
    info_el = root.find("Info")
    if info_el is not None:
        for child in info_el:
            key = _INFO_KEYS.get(etree.QName(child).localname)
            if key:
                info_values[key] = child.text

    transactions = []
    for tx_el in root.iterfind("TransactionList/Transaction"):
        values = {}
        for column in tx_el:
            name = etree.QName(column).localname
            if not name.startswith("column_"):
                continue
            key = COLUMNS.get(_parse_int(name[len("column_"):]))
            if key:
                values[key] = column.text
        if values:
            transactions.append(_finalise_transaction(values))

    return FioStatement(_finalise_info(info_values), transactions)


def parse_fio_json(data):
    """Parse a Fio JSON movement list (§5.3.1.6) into a :class:`FioStatement`."""
    if isinstance(data, bytes):
        data = data.decode("utf-8", "replace")
    try:
        payload = json.loads(data)
    except ValueError as exc:
        raise FioParseError("Not valid JSON: %s" % exc) from None
    statement = (payload or {}).get("accountStatement")
    if not isinstance(statement, dict):
        raise FioParseError("Expected an 'accountStatement' object")

    info_values = dict.fromkeys(_INFO_FIELDS)
    for name, value in (statement.get("info") or {}).items():
        key = _INFO_KEYS.get(name)
        if key:
            info_values[key] = value

    transactions = []
    tx_list = statement.get("transactionList") or {}
    for tx in tx_list.get("transaction") or []:
        values = {}
        for name, cell in (tx or {}).items():
            if not name.startswith("column") or cell is None:
                continue
            key = COLUMNS.get(_parse_int(name[len("column"):]))
            if key:
                values[key] = cell.get("value") if isinstance(cell, dict) else cell
        if values:
            transactions.append(_finalise_transaction(values))

    return FioStatement(_finalise_info(info_values), transactions)


def parse_movements(data, fmt="xml"):
    """Dispatch to the parser for ``fmt``."""
    if fmt == "json":
        return parse_fio_json(data)
    if fmt == "xml":
        return parse_fio_xml(data)
    raise ValueError("No Fio movement parser for format %r" % fmt)
