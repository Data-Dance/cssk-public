# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""SWIFT MT940 statement parser with the Czech ``?NN`` layout of field :86:.

MultiCash (and X-business, Business 24, …) hands statements to accounting as
``*.STA`` files in SWIFT MT940. The SWIFT part is common to every bank; field
:86: ("information to account owner") is not, and that is where everything a
Czech accountant matches on lives — VS/KS/SS, the counterparty account and name,
the remittance text. Sources this parser is written against (the URLs are also
in the module README):

* Česká spořitelna, *MultiCash 3.2 — Popis formátu výpisu MT940* — file layout,
  CP852, :61: with the optional MMDD entry date and ``RC``/``RD`` reversals,
  :86: subfields ``?20``–``?33`` with ``KS:``/``VS:``/``SS:`` prefixes and ``.``
  for an empty subfield.
* Raiffeisenbank, *Formát MT940 — výpisy verze 4 pro MultiCash a X-business*
  and *MultiCash — struktura dat* (MT940 v2/v3) — the same ``?NN`` scheme with
  ``KS``/``VS``/``SS`` written without a colon and zero-padded, ``-`` for an
  empty subfield, ``?38`` for the counterparty IBAN.

The two banks number the subfields differently (ČS puts VS in ``?21``, RB puts
KS there), so symbols are recognised by their **prefix**, never by subfield
number. What the two do agree on — ``?30`` counterparty bank, ``?31`` account,
``?32``/``?33`` name, ``?00`` posting text, ``?20``–``?29`` and ``?60``–``?63``
remittance — is the German structured-:86: convention both inherited, and that
is what the mapping below relies on. An :86: without ``?NN`` subfields is taken
as free text.

Pure functions, no models: the Community import shim calls ``parse_mt940`` and
hands the triplets to the OCA ``account.statement.import`` framework.
"""

import re
from datetime import date

# A field starts a line: ":20:", ":28C:", ":60F:", ":86:" …
_TAG_RE = re.compile(r"^:(\d{2}[A-Z]?):(.*)$")
# 60a / 62a / 64 / 65: D/C mark, YYMMDD, currency, amount with decimal comma
_BALANCE_RE = re.compile(r"^([CD])(\d{6})([A-Z]{3})(\d+,\d*)$")
# 61: value date, optional MMDD entry date, mark (C, D, RC, RD), optional funds
# code (third letter of the currency), amount, 4-character transaction type,
# customer reference, optional //bank reference.
_LINE61_RE = re.compile(
    r"^(?P<value>\d{6})(?P<entry>\d{4})?"
    r"(?P<mark>RC|RD|C|D)(?P<funds>[A-Z])?"
    r"(?P<amount>\d+,\d*)"
    r"(?P<type>[NSF][A-Z0-9]{3})"
    r"(?P<ref>.*?)(?://(?P<bank_ref>.*))?$"
)
# :86: is ?-structured when it opens with a subfield, optionally after the
# 3-digit business code (RB "020?20…", ČS "020?00…").
_STRUCTURED_86_RE = re.compile(r"^(\d{3})?\?\d{2}")
_SUBFIELD_RE = re.compile(r"\?(\d{2})")
# ČS "VS:23568", RB "VS0009801585". A whole-subfield match on purpose: ČS ?24
# carries the COUNTERPARTY's symbols as "VS2: …/SS2: …", which must not be read
# as the transaction's own.
_SYMBOL_SUBFIELD_RE = re.compile(r"^(VS|KS|SS)\s*:?\s*(\d{1,10})$")
# A symbol label with nothing after it — ČS ?24 "VS2: /SS2: " when the payment
# arrived without counterparty symbols, or "KS:" left blank. Pure clutter.
_EMPTY_SYMBOLS_RE = re.compile(r"^(?:(?:VS2?|KS|SS2?)\s*:?\s*[.\-]?\s*/?\s*)+$")
# Free-text :86: (banks without the ?NN layout): "VS:123", "VS 123", "/VS/123".
_SYMBOL_TEXT_RE = re.compile(r"(?<![A-Z0-9])/?(VS|KS|SS)[:/ ]\s*(\d{1,10})(?!\d)")
# RB fills ?24 with the statement number in the bank system and ?25 with the
# transaction fee, zero for almost every line — the same text on every line of
# every statement, which would only drown the remittance.
_NOISE_RE = re.compile(
    r"^(BANKOVNI VYPIS|BANK STATEMENT|BANKKONTOAUSZUG)\b|^POPL\.TRN\s+0+,00$"
)
# Both banks cut names and remittance into 27-character subfields.
_SUBFIELD_WIDTH = 27
_EMPTY_MARKERS = ("", ".", "-")
_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
_NATIONAL_25_RE = re.compile(r"^(\d{4})/(\d{1,16})$")
_NATIONAL_ACC_RE = re.compile(r"^(?:(\d{1,7})-)?(\d{1,16})$")

_REMITTANCE_KEYS = (
    ["00"] + ["%02d" % n for n in range(20, 30)] + ["60", "61", "62", "63"]
)
# Czech diacritics, for telling CP852 from CP1250 (see _decode).
_CZECH_LETTERS = set("áčďéěíňóřšťúůýžÁČĎÉĚÍŇÓŘŠŤÚŮÝŽ")


def _decode(data_file):
    """Bytes → text. UTF-8 when it decodes; else the likelier of CP852/CP1250.

    Both MultiCash specs say CP852 (Latin 2), but the same MT940 layout is also
    produced by portals that write CP1250, and neither codec ever fails to
    decode — every byte maps to something. So both are tried and the one that
    yields more Czech letters wins; CP852 on a tie, because that is what the
    specifications promise.
    """
    try:
        return data_file.decode("utf-8")
    except UnicodeDecodeError:
        pass
    cp852 = data_file.decode("cp852", errors="replace")
    cp1250 = data_file.decode("cp1250", errors="replace")

    def score(text):
        return sum(1 for char in text if char in _CZECH_LETTERS)

    return cp1250 if score(cp1250) > score(cp852) else cp852


def _swift_date(value):
    """YYMMDD → date. MT940 has two-digit years; the RB spec's own examples
    are from 1998, hence the 80 pivot rather than a flat 2000."""
    year = int(value[0:2])
    year += 1900 if year >= 80 else 2000
    return date(year, int(value[2:4]), int(value[4:6]))


def _entry_date(value_date, mmdd):
    """The optional :61: entry (booking) date carries no year. Take the value
    date's, and step across the year boundary when the two are more than half
    a year apart (booked 31 Dec with value 2 Jan, or the reverse)."""
    month, day = int(mmdd[0:2]), int(mmdd[2:4])
    year = value_date.year
    if month - value_date.month > 6:
        year -= 1
    elif value_date.month - month > 6:
        year += 1
    return date(year, month, day)


def _amount(value):
    """``"1234,5"`` → ``1234.5`` (SWIFT decimal comma, fraction optional)."""
    whole, _sep, fraction = value.partition(",")
    return float("%s.%s" % (whole or "0", fraction or "0"))


def _balance(value):
    match = _BALANCE_RE.match(value.strip())
    if not match:
        raise ValueError("Malformed MT940 balance %r" % value)
    mark, stamp, currency, amount = match.groups()
    amount = _amount(amount)
    return (-amount if mark == "D" else amount), _swift_date(stamp), currency


def _national_account(account, bank_code):
    """``"000019-0032103210"`` + ``"6800"`` → ``"19-32103210/6800"``.

    The Czech account form ``[prefix-]number/bank`` with the zero padding the
    statement adds removed, which is how ``res.partner.bank`` stores it and so
    what partner matching compares against. A 16-digit run with no dash is the
    6-digit prefix and the 10-digit number side by side (ČS ``:25:``).
    """
    match = _NATIONAL_ACC_RE.match(account)
    if not match:
        return None
    prefix, number = match.groups()
    if prefix is None and len(number) > 10:
        prefix, number = number[:-10], number[-10:]
    prefix = (prefix or "").lstrip("0")
    number = number.lstrip("0") or "0"
    head = "%s-%s" % (prefix, number) if prefix else number
    return "%s/%s" % (head, bank_code) if bank_code else head


def statement_account(value):
    """Normalise the :25: account identification.

    ČS writes ``0800/190012345671`` (bank code first, then the prefix and the
    10-digit number run together), RB ``5500/0112233088``; other banks write an
    IBAN, sometimes behind a BIC (``GIBACZPX/CZ65…``). Returns the national
    ``prefix-number/bank`` form for the first two and the bare IBAN for the
    rest, so the caller can look the journal up either way.
    """
    value = value.strip().replace(" ", "")
    match = _NATIONAL_25_RE.match(value)
    if match:
        bank_code, digits = match.groups()
        return _national_account(digits, bank_code)
    tail = value.rsplit("/", 1)[-1]
    if _IBAN_RE.match(tail.upper()):
        return tail.upper()
    return value


def is_mt940(data_file):
    """Cheap sniff: a :20: field followed somewhere by a :60F:/:60M: one."""
    try:
        text = _decode(data_file)
    except (AttributeError, UnicodeDecodeError):
        return False
    return bool(
        re.search(r"^:20:", text, re.M) and re.search(r"^:60[FM]:", text, re.M)
    )


def _tokenize(text):
    """Split the file into messages, each a list of ``[tag, [lines]]``.

    Anything before the first field is ignored — ČS puts the bank's SWIFT
    address, ``940 N2`` and the client number there, other producers a SWIFT
    ``{1:…}{2:…}{4:`` envelope. A message ends at ``-}``/``-`` or at the next
    ``:20:``. A line that is not a field continues the previous one (:61:
    supplementary details, the up-to-six lines of :86:).
    """
    messages = []
    current = None
    for raw_line in text.splitlines():
        line = raw_line.rstrip()
        if "{4:" in line:
            line = line.split("{4:", 1)[1]
        if line.startswith("-}") or line == "-" or line == "}":
            current = None
            continue
        match = _TAG_RE.match(line)
        if match:
            tag, value = match.groups()
            if tag == "20" or current is None:
                current = []
                messages.append(current)
            current.append([tag, [value]])
        elif current:
            current[-1][1].append(line)
    return messages


def parse_86(lines):
    """:86: lines → ``(business_code, subfields)``, or ``None`` for free text.

    ``subfields`` maps the two-digit code to its RAW value (not stripped: a
    27-character value that ends in the middle of a word is how the reader
    knows the next subfield continues it). A repeated code is concatenated.
    """
    joined = "".join(lines).lstrip()
    match = _STRUCTURED_86_RE.match(joined)
    if not match:
        return None
    code = match.group(1) or ""
    parts = _SUBFIELD_RE.split(joined[len(code):])
    subfields = {}
    for key, value in zip(parts[1::2], parts[2::2]):
        subfields[key] = subfields.get(key, "") + value
    return code, subfields


def _clean(value):
    value = (value or "").strip()
    return "" if value in _EMPTY_MARKERS else value


def _normalise_symbol(kind, digits):
    """Leading zeros are padding (RB writes all symbols 10 digits wide); the
    constant symbol is conventionally the 4-digit code, as GPC carries it."""
    digits = digits.lstrip("0")
    if kind == "KS" and digits:
        return digits.zfill(4)[-4:] if len(digits) <= 4 else digits
    return digits


def _structured_details(subfields):
    """Pull symbols, counterparty and remittance out of ?NN subfields."""
    symbols = {}
    texts = []
    for key in sorted(subfields):
        value = _clean(subfields[key])
        if not value:
            continue
        symbol = _SYMBOL_SUBFIELD_RE.match(value)
        if symbol:
            kind, digits = symbol.groups()
            symbols.setdefault(kind, _normalise_symbol(kind, digits))
            continue
        if key not in _REMITTANCE_KEYS or _EMPTY_SYMBOLS_RE.match(value):
            continue
        if key in ("24", "25") and _NOISE_RE.match(value):
            continue
        texts.append(value)

    account_number = None
    iban = _clean(subfields.get("38")).lstrip("/").replace(" ", "")
    account = _clean(subfields.get("31")).lstrip("/").replace(" ", "")
    bank = _clean(subfields.get("30"))
    if iban:
        account_number = iban
    elif account:
        if re.match(r"^\d{4}$", bank):
            account_number = _national_account(account, bank) or account
        else:
            account_number = account
    else:
        # ČS domestic ?23: "bank code/account" of the counterparty
        match = re.match(r"^(\d{4})/((?:\d{1,6}-)?\d{1,10})$",
                         _clean(subfields.get("23")))
        if match:
            account_number = _national_account(match.group(2), match.group(1))

    name_raw = subfields.get("32") or ""
    name = _clean(name_raw)
    continuation = _clean(subfields.get("33"))
    if name and continuation and len(name_raw.rstrip("\r\n")) >= _SUBFIELD_WIDTH:
        # a full-width ?32 was cut mid-name and ?33 carries on with it
        name = name_raw + subfields["33"].rstrip()
        name = name.strip()
    return symbols, account_number, name, texts


def _free_text_details(text):
    symbols = {}
    for kind, digits in _SYMBOL_TEXT_RE.findall(text.upper()):
        symbols.setdefault(kind, _normalise_symbol(kind, digits))
    return symbols, None, "", [text] if text else []


def _transaction_vals(line61, lines86, account, statement_no, index,
                      with_symbols):
    first = line61[0]
    match = _LINE61_RE.match(first)
    if not match:
        raise ValueError("Malformed MT940 :61: line %r" % first)
    value_date = _swift_date(match.group("value"))
    booking = value_date
    if match.group("entry"):
        booking = _entry_date(value_date, match.group("entry"))
    mark = match.group("mark")
    amount = _amount(match.group("amount"))
    # SWIFT: RC = reversal of a credit (money leaves), RD = of a debit
    if mark in ("D", "RC"):
        amount = -amount
    customer_ref = match.group("ref").strip()
    bank_ref = (match.group("bank_ref") or "").strip()
    if customer_ref.upper() == "NONREF":
        customer_ref = ""

    if lines86 is None:
        symbols, counter_account, name, texts = {}, None, "", []
    else:
        parsed = parse_86(lines86)
        if parsed:
            symbols, counter_account, name, texts = _structured_details(parsed[1])
        else:
            symbols, counter_account, name, texts = _free_text_details(
                " ".join(line.strip() for line in lines86).strip()
            )

    # :61: supplementary details (the optional second line, 34x) — ČS puts
    # e.g. the original amount of a converted payment there
    supplementary = " ".join(line.strip() for line in line61[1:]).strip()
    ref_parts = []
    for part in [name] + texts + [supplementary]:
        if part and part not in ref_parts:
            ref_parts.append(part)
    for kind in ("VS", "KS", "SS"):
        token = "%s:%s" % (kind, symbols.get(kind))
        # free text often already says "VS:123"; say it once
        if symbols.get(kind) and token not in " ".join(ref_parts):
            ref_parts.append(token)
    if counter_account:
        ref_parts.append(counter_account)
    if not ref_parts:
        ref_parts.append("MT940 %s" % (customer_ref or bank_ref or index))

    raw = [":61:" + "\n".join(line61)]
    if lines86 is not None:
        raw.append(":86:" + "\n".join(lines86))
    vals = {
        "date": booking,
        "amount": amount,
        "payment_ref": " ".join(ref_parts),
        "transaction_type": match.group("type"),
        "raw_data": "\n".join(raw),
        # The index keeps two identical transactions on one statement (same
        # amount, no reference — a pair of card fees) from colliding; the
        # statement number and account keep a re-download of the same
        # statement from importing twice.
        "unique_import_id": "%s-%s-%s-%s-%s%s-%s" % (
            account,
            statement_no,
            match.group("value"),
            index,
            mark,
            match.group("amount"),
            bank_ref or customer_ref,
        ),
    }
    if name:
        vals["partner_name"] = name
    if counter_account:
        vals["account_number"] = counter_account
    if customer_ref:
        vals["ref"] = customer_ref
    if with_symbols:
        for field_name, kind in (
            ("variable_symbol", "VS"),
            ("constant_symbol", "KS"),
            ("specific_symbol", "SS"),
        ):
            if symbols.get(kind):
                vals[field_name] = symbols[kind]
    return vals


def parse_mt940(data_file, with_symbols=False):
    """Parse an MT940 file into the import framework's triplets.

    :param data_file: raw bytes of the statement file
    :param with_symbols: also emit ``variable_symbol`` / ``constant_symbol`` /
        ``specific_symbol`` — only when a module providing those fields on
        ``account.bank.statement.line`` is installed.
    :return: list of ``(currency_code, account_number, stmts_vals)`` triplets,
        one per (currency, account); empty when the file is not MT940.

    A statement continued over several messages (``:28C:`` page 2, 3 … opening
    with the intermediate balance ``:60M:``) is folded back into one statement
    whose closing balance is the last page's.
    """
    text = _decode(data_file)
    groups = {}  # (currency, account) -> [stmt_vals]
    previous = {}  # (currency, account) -> (statement_no, stmt_vals)
    for message in _tokenize(text):
        fields = {}
        order = []
        for tag, lines in message:
            order.append((tag, lines))
            fields.setdefault(tag, lines)
        account_raw = (fields.get("25") or [""])[0]
        opening_tag = "60F" if "60F" in fields else "60M"
        if not account_raw or opening_tag not in fields:
            continue
        account = statement_account(account_raw)
        opening, opening_date, currency = _balance(fields[opening_tag][0])
        statement_ref = ((fields.get("28C") or fields.get("28") or [""])[0]).strip()
        statement_no = statement_ref.split("/", 1)[0].lstrip("0") or statement_ref

        key = (currency, account)
        continued = previous.get(key)
        # A continuation must pick up exactly where the previous page closed;
        # the same number with a different balance is another statement.
        if (
            opening_tag == "60M"
            and continued
            and continued[0] == statement_no
            and continued[1].get("balance_end_real") == opening
        ):
            stmt = continued[1]
        else:
            stmt = {
                "name": "MT940 %s/%s" % (account, statement_no or "?"),
                "date": opening_date,
                "balance_start": opening,
                "transactions": [],
            }
            groups.setdefault(key, []).append(stmt)
            previous[key] = (statement_no, stmt)

        pending = None
        for tag, lines in order:
            if tag == "61":
                if pending is not None:
                    stmt["transactions"].append(_transaction_vals(
                        pending, None, account, statement_no,
                        len(stmt["transactions"]) + 1, with_symbols,
                    ))
                pending = lines
            elif tag == "86" and pending is not None:
                stmt["transactions"].append(_transaction_vals(
                    pending, lines, account, statement_no,
                    len(stmt["transactions"]) + 1, with_symbols,
                ))
                pending = None
            elif tag in ("62F", "62M"):
                if pending is not None:
                    stmt["transactions"].append(_transaction_vals(
                        pending, None, account, statement_no,
                        len(stmt["transactions"]) + 1, with_symbols,
                    ))
                    pending = None
                closing, closing_date, _currency = _balance(lines[0])
                stmt["balance_end_real"] = closing
                stmt["date"] = closing_date
        if pending is not None:
            stmt["transactions"].append(_transaction_vals(
                pending, None, account, statement_no,
                len(stmt["transactions"]) + 1, with_symbols,
            ))

    result = []
    for (currency, account), stmts_vals in groups.items():
        stmts_vals = [vals for vals in stmts_vals if vals["transactions"]]
        if stmts_vals:
            result.append((currency, account, stmts_vals))
    return result
