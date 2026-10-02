# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Komerční banka **BEST** client format: payment files out, statements in.

BEST is KB's own fixed-width format for its direct-banking channels
(MojeBanka Business, Profibanka, Přímý kanál). Specification: *Klientský formát
BEST podporovaný v KB* (valid from 20 June 2026), with KB's published sample
files; URLs in the module README. Every offset below was checked against those
samples.

Three layouts, all CRLF-terminated, CP1250:

* **domestic payments** — 353-byte records: ``HI`` header, ``01`` payments
  (úhrada or inkaso), ``TI`` trailer with the count and the sum of amounts;
* **foreign and SEPA payments** — 884-byte records: ``HI``, ``02`` payment
  followed by an optional ``03`` structured address, ``TI`` (its count covers
  the ``02`` and ``03`` records);
* **electronic statement** (``*.OKM``/``*.KMO``) — 475-byte records: ``HO``,
  per account and day a ``51`` turnover record and its ``52`` transactions
  (``53`` = non-accounting, no effect on balance), ``TO``.

Amounts are ``9(13)V9(2)`` — 15 digits with two implied decimals, no sign;
the sign lives in a separate field (turnover record) or in the accounting code
(``0`` debit, ``1`` credit, ``2`` debit reversal, ``3`` credit reversal).
"""

import re
from datetime import date

from odoo import _
from odoo.exceptions import UserError

from odoo.addons.account_cz_bankfile_base.utils.common import (
    fold_to_ascii,
    parse_cz_account,
)

KB_BANK_CODE = "0100"
DOMESTIC_LENGTH = 351  # data bytes; + CRLF = 353
FOREIGN_LENGTH = 882  # + CRLF = 884
STATEMENT_LENGTH = 473  # + CRLF = 475

# KS the bank refuses in a domestic batch (spec 2.1.1): ???5 corrective
# settlement, ??51 enforcement, 0006 non-existent account, 0007 refund of
# a direct debit.
_FORBIDDEN_KS_RE = re.compile(r"^(\d{3}5|\d{2}51|0006|0007)$")
# Text fields of a foreign payment may carry only the SWIFT character set,
# and must not start with "-" or ":" (spec 2.2.3).
_SWIFT_RE = re.compile(r"[^A-Za-z0-9/\-?:().,'+ ]")

# ISO 20022 charge bearer (account_iso20022 / OCA) -> BEST "Plátce poplatků"
_CHARGE_BEARER = {
    "SHAR": "SHA", "SLEV": "SHA", "SHA": "SHA",
    "DEBT": "OUR", "OUR": "OUR",
    "CRED": "BEN", "BEN": "BEN",
}

# EEA: since PSD2 (13 Jan 2018) KB processes a payment into the EEA only with
# charges SHA (spec 2.2.1).
EEA_COUNTRIES = frozenset(
    "AT BE BG CY CZ DE DK EE ES FI FR GR HR HU IE IS IT LI LT LU LV MT NL NO "
    "PL PT RO SE SI SK".split()
)
# SEPA scheme countries (EPC): the EEA plus these.
SEPA_COUNTRIES = EEA_COUNTRIES | frozenset(
    "AD AL CH GB GI MC MD ME MK RS SM VA".split()
)
_IBAN_RE = re.compile(r"^[A-Z]{2}\d{2}[A-Z0-9]{10,30}$")
_BIC_RE = re.compile(r"^[A-Z]{6}[A-Z0-9]{2}([A-Z0-9]{3})?$")


# ---------------------------------------------------------------------------
# field helpers
# ---------------------------------------------------------------------------
def _x(value, width):
    """``X(n)``: text, left-aligned, space-padded, truncated."""
    return (value or "")[:width].ljust(width)


def _n(value, width):
    """``9(n)``: digits, right-aligned, zero-padded. Refuses what won't fit
    rather than truncating — a truncated account number is another account."""
    digits = str(value or "")
    if not digits.isdigit():
        digits = "0" if not digits.strip() else digits
    if not digits.isdigit() or len(digits) > width:
        raise ValueError("%r does not fit a %d-digit numeric field" % (value, width))
    return digits.rjust(width, "0")


def _amount(amount):
    """``9(13)V9(2)``: the amount in hundredths, 15 digits."""
    return _n(int(round(abs(amount) * 100)), 15)


def _account16(prefix, number):
    """KB account field ``9(16)``: 6-digit prefix + 10-digit number."""
    return _n(prefix or "0", 6) + _n(number, 10)


def _cp1250(text):
    """Domestic records are CP1250 and keep diacritics (KB's own sample does);
    fold only what CP1250 cannot hold."""
    text = re.sub(r"\s+", " ", text or "").strip()
    return "".join(
        char if _encodable(char) else fold_to_ascii(char) for char in text
    )


def _encodable(char):
    try:
        char.encode("cp1250")
    except UnicodeEncodeError:
        return False
    return True


# letters NFKD folding leaves alone (they do not decompose into base + mark)
_LIGATURES = str.maketrans({
    "ß": "ss", "Æ": "AE", "æ": "ae", "Ø": "O", "ø": "o", "Œ": "OE", "œ": "oe",
    "Đ": "D", "đ": "d", "Ł": "L", "ł": "l", "Þ": "TH", "þ": "th",
})


def _swift(text):
    """Foreign records: SWIFT set only, no leading "-" or ":"."""
    text = re.sub(r"\s+", " ", text or "").translate(_LIGATURES)
    text = _SWIFT_RE.sub(" ", fold_to_ascii(text))
    return re.sub(r" +", " ", text).strip().lstrip("-:").strip()


def _lines(text, width, count, clean):
    """Wrap text into ``count`` lines of ``width``, on word boundaries where
    possible, then pad to a ``X(width*count)`` block."""
    words = clean(text).split(" ")
    lines, current = [], ""
    for word in words:
        if not word:
            continue
        while len(word) > width:
            if current:
                lines.append(current)
                current = ""
            lines.append(word[:width])
            word = word[width:]
        if not current:
            current = word
        elif len(current) + 1 + len(word) <= width:
            current += " " + word
        else:
            lines.append(current)
            current = word
    if current:
        lines.append(current)
    lines = lines[:count]
    if clean is _swift:
        # each line of a foreign text block is a field of its own for the
        # "no leading - or :" rule, and wrapping can put one first
        lines = [line.lstrip("-:").lstrip() for line in lines]
    return "".join(_x(line, width) for line in lines).ljust(width * count)


def _symbol(value, width=10):
    digits = re.sub(r"\D", "", value or "")
    return _n(digits or "0", width)


def _check_record(record, length):
    if len(record) != length:  # a programming error, never user input
        raise ValueError("BEST record is %d bytes, expected %d" % (len(record), length))
    return record


def sequence_no(item, index):
    """``Sekv_No``: 5 characters, unique for the client **per creation day**
    across every file sent that day — not just within this one, so a
    per-file counter would collide with the morning's batch. Base-36 of the
    payment line's database id does not; the index is the fallback."""
    number = item.ref_id if isinstance(item.ref_id, int) and item.ref_id else index
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    number %= 36 ** 5
    while True:
        number, rest = divmod(number, 36)
        out = digits[rest] + out
        if not number:
            break
    return out.rjust(5, "0")


def _header(creation, file_id, length):
    record = "HI" + " " * 9 + creation.strftime("%y%m%d") + _x(file_id, 14)
    record += " " * 35 + "   "  # "CAN" would make this a cancelling batch
    return _check_record(record.ljust(length), length)


def _trailer(creation, count, total_cents, length):
    record = "TI" + " " * 9 + creation.strftime("%y%m%d")
    record += _n(count, 6) + _n(total_cents, 18)
    return _check_record(record.ljust(length), length)


def _company_kb_account(company_bank):
    if not company_bank:
        raise UserError(_("The bank journal has no bank account configured."))
    try:
        prefix, number, bank_code = parse_cz_account(company_bank)
    except ValueError as e:
        raise UserError(_("Orderer bank account: %s", str(e))) from None
    if bank_code != KB_BANK_CODE:
        raise UserError(_(
            "BEST is Komerční banka's format: the journal account %(acc)s is "
            "not a KB account (bank code %(kb)s).",
            acc=company_bank.acc_number, kb=KB_BANK_CODE,
        ))
    return prefix, number


# ---------------------------------------------------------------------------
# domestic payments (01)
# ---------------------------------------------------------------------------
def build_best_domestic(company_bank, items, account_currency, creation,
                        file_id="", batch_type="outbound"):
    """Domestic BEST batch: úhrady (``batch_type='outbound'``) or inkasa.

    :param account_currency: ISO code of the KB account being debited (the
        journal's currency) — BEST states the account currency and, when the
        payment is in another one, the counter-account currency with a
        conversion flag.
    :param creation: the file's creation date (the bank rejects one outside
        -31/+364 days of today, and a due date before today).
    """
    if not items:
        raise UserError(_("Cannot generate a BEST file from an empty payment list."))
    prefix, number = _company_kb_account(company_bank)
    operation = "1" if batch_type == "inbound" else "0"
    records = [_header(creation, file_id, DOMESTIC_LENGTH)]
    total = 0
    for index, item in enumerate(items, start=1):
        if not item.partner_bank:
            raise UserError(_("Payment %s is missing a partner bank account.",
                              item.label))
        try:
            p_prefix, p_number, p_bank = parse_cz_account(item.partner_bank)
        except ValueError as e:
            raise UserError(_("Payment %(name)s: %(error)s",
                              name=item.label, error=str(e))) from None
        if item.amount <= 0:
            raise UserError(_("Payment %s: the amount must be positive.", item.label))
        currency = item.currency_name
        if currency == account_currency:
            counter_currency, conversion = currency, " "
        else:
            # the amount is stated in the counter-account currency
            counter_currency, conversion = currency, "P"
        if counter_currency != "CZK" and p_bank != KB_BANK_CODE:
            raise UserError(_(
                "Payment %(name)s: a domestic BEST payment in %(cur)s can only "
                "go to another KB account; to another bank it must be in CZK "
                "or sent as a foreign payment.",
                name=item.label, cur=counter_currency,
            ))
        if operation == "1" and p_bank != KB_BANK_CODE and currency != "CZK":
            raise UserError(_(
                "Payment %s: a direct debit outside KB can only be in CZK.",
                item.label))
        ks = _symbol(item.ks, 4)
        if item.ks and _FORBIDDEN_KS_RE.match(ks):
            raise UserError(_(
                "Payment %(name)s: KB refuses the constant symbol %(ks)s in a "
                "batch (corrective settlement, enforcement, non-existent "
                "account or direct-debit refund).",
                name=item.label, ks=ks,
            ))
        due = max(item.date or creation, creation)
        amount_cents = int(round(item.amount * 100))
        total += amount_cents
        message = _lines(item.message, 35, 4, _cp1250)
        record = (
            "01"
            + _x(sequence_no(item, index), 5)
            + creation.strftime("%Y%m%d")
            + due.strftime("%Y%m%d")
            + _x(account_currency, 3)
            + _amount(item.amount)
            + operation
            + _x(counter_currency, 3)
            + conversion
            + _symbol(item.ks)
            + message
            + "   "
            + KB_BANK_CODE
            + _account16(prefix, number)
            # the orderer's own VS/SS: since the ČNB clearing change the bank
            # overwrites them with the partner's, so zeros say "none of mine"
            + _symbol("")
            + _symbol("")
            + _x(_cp1250(item.message), 30)
            + "   "
            + _n(p_bank, 4)
            + _account16(p_prefix, p_number)
            + _symbol(item.vs)
            + _symbol(item.ss)
            + _x(_cp1250(item.partner.name if item.partner else ""), 30)
            + ("E" if item.iso_priority == "URGP" else "S")
            + "N"  # no FOREX deal
            + " " * 7
        )
        records.append(_check_record(record, DOMESTIC_LENGTH))
    records.append(_trailer(creation, len(items), total, DOMESTIC_LENGTH))
    return _encode(records)


# ---------------------------------------------------------------------------
# foreign / SEPA payments (02 + 03)
# ---------------------------------------------------------------------------
def _country_of(partner_bank):
    acc = (partner_bank.acc_number or "").replace(" ", "").upper()
    if _IBAN_RE.match(acc):
        return acc[:2]
    bank = partner_bank.bank_id
    if bank and bank.country:
        return bank.country.code
    return None


def _party_lines(partner, clean):
    """Four 35-character lines: name, street, "city, zip", ISO country —
    the layout of BEST fields 23 and 27."""
    if not partner:
        return ["", "", "", ""]
    city = ", ".join(filter(None, [partner.city, partner.zip]))
    return [
        clean(partner.name)[:35],
        clean(" ".join(filter(None, [partner.street, partner.street2])))[:35],
        clean(city)[:35],
        (partner.country_id.code or "") if partner.country_id else "",
    ]


def _bank_lines(bank, clean):
    if not bank:
        return ["", "", "", ""]
    city = ", ".join(filter(None, [bank.city, bank.zip]))
    country = bank.country.code if bank.country else ""
    return [
        clean(bank.name)[:35],
        clean(" ".join(filter(None, [bank.street, bank.street2])))[:35],
        clean(city)[:35],
        # "CC" + space + space, then an optional "//NCC" we never hold
        (country + "  ") if country else "",
    ]


def build_best_foreign(company_bank, company_partner, items, account_currency,
                       creation, file_id=""):
    """Foreign and SEPA BEST batch (``02`` payments, ``03`` addresses).

    A payment goes as **SEPA** (flag ``Y``, charges ``SLV``) when it can: EUR,
    an IBAN in a SEPA country, charges shared. Everything else is a standard
    foreign payment (ZPL), which needs the full beneficiary address and either
    a BIC or the bank's name and address.
    """
    if not items:
        raise UserError(_("Cannot generate a BEST file from an empty payment list."))
    prefix, number = _company_kb_account(company_bank)
    payer_account = _account16(prefix, number)
    payer_lines = _party_lines(company_partner, _swift)
    records = [_header(creation, file_id, FOREIGN_LENGTH)]
    total = 0
    count = 0
    for index, item in enumerate(items, start=1):
        partner_bank = item.partner_bank
        if not partner_bank:
            raise UserError(_("Payment %s is missing a partner bank account.",
                              item.label))
        if item.amount <= 0:
            raise UserError(_("Payment %s: the amount must be positive.", item.label))
        account = (partner_bank.acc_number or "").replace(" ", "").upper()
        is_iban = bool(_IBAN_RE.match(account))
        country = _country_of(partner_bank)
        charges = _CHARGE_BEARER.get(item.iso_charge_bearer or "SHAR", "SHA")
        if country in EEA_COUNTRIES and charges != "SHA":
            raise UserError(_(
                "Payment %(name)s: KB processes payments into the EEA only "
                "with shared charges (SHA), not %(chg)s.",
                name=item.label, chg=charges,
            ))
        sepa = (
            item.currency_name == "EUR"
            and is_iban
            and country in SEPA_COUNTRIES
            and charges == "SHA"
        )
        if item.currency_name == "EUR" and country in EEA_COUNTRIES and not is_iban:
            raise UserError(_(
                "Payment %s: a EUR payment into the EEA needs the "
                "beneficiary's IBAN.", item.label))
        bank = partner_bank.bank_id
        bic = (bank.bic or "").replace(" ", "").upper() if bank else ""
        if bic and not _BIC_RE.match(bic):
            raise UserError(_(
                "Payment %(name)s: %(bic)s is not a BIC (8 or 11 letters and "
                "digits).", name=item.label, bic=bic))
        beneficiary = _party_lines(item.partner, _swift)
        bank_lines = _bank_lines(bank, _swift)
        if not sepa:
            if not all(beneficiary[i] for i in (0, 1, 2, 3)):
                raise UserError(_(
                    "Payment %s: a foreign (non-SEPA) payment needs the "
                    "beneficiary's name, street, city and country.", item.label))
            if not bic and not (bank_lines[0] and bank_lines[2] and bank_lines[3]):
                raise UserError(_(
                    "Payment %s: the beneficiary's bank needs a BIC, or its "
                    "name, city and country.", item.label))
        elif not beneficiary[0]:
            raise UserError(_("Payment %s: the beneficiary has no name.", item.label))

        remittance = item.message or ""
        # KB reads "/VS/nnn" and "/KS/nnn" out of the remittance into the
        # transaction history's symbol fields (spec 2.2.2, field 24)
        tokens = []
        if item.vs:
            tokens.append("/VS/%s" % re.sub(r"\D", "", item.vs))
        if item.ks:
            tokens.append("/KS/%s" % re.sub(r"\D", "", item.ks))
        if tokens:
            remittance = " ".join(tokens + [remittance])
        amount_cents = int(round(item.amount * 100))
        total += amount_cents
        seq = sequence_no(item, index)
        due = max(item.date or creation, creation)
        record = (
            "02"
            + " " * 6
            + _x(seq, 5)
            + creation.strftime("%Y%m%d")
            + due.strftime("%Y%m%d")
            + _x(item.currency_name, 3)
            + _amount(item.amount)
            + ("SLV" if sepa else charges)
            + payer_account  # charges account: the payer's own
            + _x(account_currency, 3)
            + ("U" if item.iso_priority == "URGP" else "E")
            + "0" * 10
            + " " * 20
            + "N"  # no FOREX deal
            + " " * 16
            + " " * 3
            + KB_BANK_CODE
            + payer_account
            + _x(account_currency, 3)
            + " " * 105
            # an 8-character BIC is padded with 3 spaces, which KB turns
            # into "XXX"
            + _x(_x(bic, 11) if bic else "", 35)
            + "".join(_x(line, 35) for line in payer_lines)
            + _lines(remittance, 35, 4, _swift)
            + "/"
            + _x(account, 34)
            + "".join(_x(line, 35) for line in beneficiary)
            + "".join(_x(line, 35) for line in bank_lines)
            + "N"  # not by cheque
            + ("Y" if sepa else "N")
            + "  "
        )
        records.append(_check_record(record, FOREIGN_LENGTH))
        count += 1
        address = _address_record(seq, item.partner, bank, sepa)
        if address:
            records.append(address)
            count += 1
    records.append(_trailer(creation, count, total, FOREIGN_LENGTH))
    return _encode(records)


def _address_record(seq, partner, bank, sepa):
    """``03`` structured address (from 20 June 2026). For SEPA it is optional,
    but once any element is given the city and country are mandatory — so it
    is emitted only when both are known."""
    if not partner or not partner.city or not partner.country_id:
        return None
    street = _swift(partner.street)
    building = ""
    if getattr(partner, "street_name", False) and getattr(partner, "street_number", False):
        street = _swift(partner.street_name)
        building = _swift(partner.street_number)
    bank_country = bank.country.code if bank and bank.country else ""
    record = (
        "03"
        + " " * 6
        + _x(seq, 5)
        + _x(_swift(partner.name), 70 if sepa else 140).ljust(140)
        + _x(street, 70)
        + _x(building, 16)
        + _x(_swift(partner.zip), 16)
        + _x(_swift(partner.city), 35)
        + _x(_swift(partner.state_id.name if partner.state_id else ""), 35)
        + _x(partner.country_id.code, 2)
        + _x(_swift(bank.name) if bank else "", 140)
        + _x(_swift(bank.street) if bank else "", 70)
        + " " * 16
        + _x(_swift(bank.zip) if bank else "", 16)
        + _x(_swift(bank.city) if bank else "", 35)
        + " " * 35
        + _x(bank_country, 2)
        + " " * 20  # LEI of the payer: reserved
        + " " * 20  # LEI of the beneficiary: reserved
        + " " * 201
    )
    return _check_record(record, FOREIGN_LENGTH)


def _encode(records):
    return ("\r\n".join(records) + "\r\n").encode("cp1250", errors="replace")


# ---------------------------------------------------------------------------
# electronic statement (HO / 51 / 52 / 53 / TO)
# ---------------------------------------------------------------------------
# accounting code -> sign: 0 debit, 1 credit, 2 debit reversal, 3 credit
# reversal. The spec's own check (2.4.1) is NZ = SZ - OD + OK with
# OD = +KU0 -KU2 and OK = +KU1 -KU3.
_KU_SIGNS = {"0": -1, "1": 1, "2": 1, "3": -1}
# "Použit BIC / SWIFT" flag of a 52 record: 1/2 foreign out/in, 4/5 SEPA out/in
_FOREIGN_FLAGS = ("1", "2", "4", "5")
# SS 9999999999 is an instruction (suppress the partner's name in the
# transaction history), not a specific symbol.
_SUPPRESS_NAME_SS = "9999999999"


def _decode(data_file):
    try:
        return data_file.decode("cp1250")
    except UnicodeDecodeError:
        return data_file.decode("latin-1")


def _date8(value):
    return date(int(value[0:4]), int(value[4:6]), int(value[6:8]))


def _cents(value):
    return int(value) / 100.0


def is_best_statement(data_file):
    """Cheap sniff: the file opens with the ``HO`` header naming BEST."""
    try:
        text = _decode(data_file)
    except AttributeError:
        return False
    first = text.lstrip("\r\n").split("\n", 1)[0]
    return first.startswith("HO") and first[2:6] == "BEST"


def _national(account16, bank_code):
    prefix = account16[:6].lstrip("0")
    number = account16[6:].lstrip("0") or "0"
    head = "%s-%s" % (prefix, number) if prefix else number
    return "%s/%s" % (head, bank_code)


def _normalise_symbol(kind, digits):
    digits = (digits or "").strip().lstrip("0")
    if not digits.isdigit():
        return ""
    if kind == "KS":
        return digits.zfill(4) if len(digits) <= 4 else digits
    return digits


def parse_best_statement(data_file, with_symbols=False):
    """Parse a BEST electronic statement into the import framework's triplets.

    :return: list of ``(currency_code, account_number, stmts_vals)``, one per
        (currency, account); empty when the file is not a BEST statement.
        The account is the IBAN from the turnover record when present, else
        ``prefix-number/0100``.
    """
    text = _decode(data_file)
    # padded back to the record length: a file that passed through an editor
    # or a mail gateway may have lost its trailing spaces, and the last fields
    # of a record are often blank
    lines = [line.rstrip("\r").ljust(STATEMENT_LENGTH) for line in text.split("\n")]
    lines = [line for line in lines if line.strip()]
    if not lines or not (lines[0].startswith("HO") and lines[0][2:6] == "BEST"):
        return []
    groups = {}
    stmt = None
    account = None
    for line in lines:
        kind = line[0:2]
        if kind == "51":
            account16 = line[2:18]
            iban = line[136:160].strip()
            account = iban or _national(account16, KB_BANK_CODE)
            old = _cents(line[42:57]) * (-1 if line[57] == "-" else 1)
            new = _cents(line[58:73]) * (-1 if line[73] == "-" else 1)
            number = line[26:29].lstrip("0") or "0"
            stmt = {
                "name": "BEST %s/%s" % (account, number),
                "date": _date8(line[18:26]),
                "balance_start": old,
                "balance_end_real": new,
                "transactions": [],
                "_account16": account16,
                "_currency": None,
            }
        elif kind == "52" and stmt is not None:
            vals, currency = _statement_line(line, stmt["_account16"], with_symbols)
            if stmt["_currency"] is None:
                stmt["_currency"] = currency
                groups.setdefault((currency, account), []).append(stmt)
            stmt["transactions"].append(vals)
        # 53: non-accounting (loan interest and fee instalments) — no effect
        # on the balance, so not a statement line. HO/TO: nothing to read.
    result = []
    for (currency, account_number), stmts_vals in groups.items():
        for vals in stmts_vals:
            vals.pop("_account16", None)
            vals.pop("_currency", None)
        result.append((currency, account_number, stmts_vals))
    return result


def _statement_line(line, account16, with_symbols):
    code = line[46]
    if code not in _KU_SIGNS:
        raise ValueError("Unknown BEST accounting code %r" % code)
    amount = _KU_SIGNS[code] * _cents(line[50:65])
    currency = line[47:50]
    counter16 = line[23:39]
    counter_bank = line[39:46][-4:]
    foreign = line[471] in _FOREIGN_FLAGS
    description_debit = line[209:239].strip()
    description_credit = line[239:269].strip()
    message = " ".join(
        line[269 + i * 35:269 + (i + 1) * 35].strip() for i in range(4)
    ).strip()
    message = re.sub(r" +", " ", message)
    system = line[409:439].strip()
    name = line[439:469].strip()

    counter_account = None
    if foreign:
        # a foreign payment books against KB's internal account; the partner's
        # own account is in "Popis 1" (spec 2.4.2, field 26)
        candidate = re.sub(r"^(UCET|ÚČET)\s*", "", description_debit.upper())
        candidate = candidate.replace(" ", "")
        if _IBAN_RE.match(candidate):
            counter_account = candidate
    elif counter16.strip("0 "):
        counter_account = _national(counter16, counter_bank)

    symbols = {
        "VS": _normalise_symbol("VS", line[117:127]) or _normalise_symbol("VS", line[127:137]),
        "KS": _normalise_symbol("KS", line[137:147]),
        "SS": "",
    }
    for raw in (line[147:157], line[157:167]):
        if raw.strip() != _SUPPRESS_NAME_SS:
            symbols["SS"] = symbols["SS"] or _normalise_symbol("SS", raw)

    parts = [part for part in (name, message) if part]
    for kind in ("VS", "KS", "SS"):
        if symbols[kind]:
            parts.append("%s:%s" % (kind, symbols[kind]))
    if counter_account:
        parts.append(counter_account)
    if not message and system:
        parts.append(system)
    if not parts:
        parts.append("BEST %s" % line[2:7])

    # our own "popis pro mě" is on the side we are on: debit or credit
    own_description = description_debit if amount < 0 else description_credit
    vals = {
        "date": _date8(line[175:183]),
        "amount": amount,
        "payment_ref": " ".join(parts),
        "transaction_type": line[199:201],
        "raw_data": line,
        # KBI_ID is the central ledger's own identifier of the posting
        "unique_import_id": "%s-%s-%s-%s" % (
            account16, line[175:183], line[2:7], line[86:117].strip(),
        ),
    }
    if name:
        vals["partner_name"] = name
    if counter_account:
        vals["account_number"] = counter_account
    if own_description and not foreign:
        vals["ref"] = own_description
    if with_symbols:
        for field_name, kind in (
            ("variable_symbol", "VS"),
            ("constant_symbol", "KS"),
            ("specific_symbol", "SS"),
        ):
            if symbols[kind]:
                vals[field_name] = symbols[kind]
    return vals, currency
