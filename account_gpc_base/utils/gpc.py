# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""GPC (ABO electronic statement) parser.

Fixed 130-character records, no separators, values zero-padded from the
left (spec: "Struktura GPC formátu pro elektronické výpisy", ABO/ČNB,
published e.g. by Fio banka):

* ``074`` statement header — account, old/new balance with signs, debit
  and credit turnovers, statement sequence number, accounting date.
* ``075`` transaction — own account, counterparty account, document
  number, amount in haléře, accounting code (1 debit / 2 credit /
  4 debit reversal / 5 credit reversal), VS, constant-symbol field in
  the form ``BBBBKSYM`` (counterparty bank code + KS), SS, client name,
  currency code (``0`` + ISO 4217 numeric), due date.
* ``076``/``078``/``079`` — bank-specific message (AV) extensions,
  appended to the previous transaction's label.

Pure functions, no models: the Community shim (OCA ``account.statement.import``
wizard) and the Enterprise shim (``account.journal._parse_bank_statement_file``)
both call ``parse_gpc`` and differ only in how they hand the result to their
framework.
"""

from datetime import date

# "0" + ISO 4217 numeric code, e.g. "0203" = CZK
GPC_CURRENCIES = {
    203: "CZK",
    978: "EUR",
    840: "USD",
    826: "GBP",
    985: "PLN",
    348: "HUF",
    756: "CHF",
    208: "DKK",
    752: "SEK",
    578: "NOK",
}

# accounting code (pos 61) → amount sign
GPC_SIGNS = {"1": -1, "2": 1, "4": 1, "5": -1}


def _gpc_date(value):
    """DDMMYY → date (GPC statements are all post-2000)."""
    return date(2000 + int(value[4:6]), int(value[2:4]), int(value[0:2]))


def _gpc_amount(value, sign_char="+"):
    amount = int(value) / 100.0
    return -amount if sign_char == "-" else amount


def _decode(data_file):
    try:
        return data_file.decode("cp1250")
    except UnicodeDecodeError:
        return data_file.decode("latin-1")


def is_gpc(data_file):
    """Cheap sniff: a GPC file opens with a 074 header or a bare 075 item."""
    try:
        text = _decode(data_file)
    except (AttributeError, UnicodeDecodeError):
        return False
    for line in text.splitlines():
        if line.strip():
            return line.startswith(("074", "075"))
    return False


def parse_gpc(data_file, with_symbols=False):
    """Parse a GPC file into the import framework's triplets.

    :param data_file: raw bytes of the statement file
    :param with_symbols: also emit ``variable_symbol`` / ``constant_symbol`` /
        ``specific_symbol`` on each transaction — pass True only when a module
        providing those fields on ``account.bank.statement.line`` is installed.
    :return: list of ``(currency_code, account_number, stmts_vals)`` triplets,
        empty when the file is not GPC. Multi-statement files (one 074 block
        per day) are the norm, hence one triplet per (currency, account) group.
    """
    text = _decode(data_file)
    lines = [line for line in text.splitlines() if line.strip()]
    if not lines or not lines[0].startswith(("074", "075")):
        return []

    groups = {}  # (currency, account) -> [stmt_vals]
    current = None  # stmt_vals of the open 074 block
    current_account = None
    current_registered = False
    last_transaction = None
    for line in lines:
        record = line[0:3]
        if record == "074":
            account = line[3:19].lstrip("0")
            old_balance = _gpc_amount(line[45:59], line[59])
            new_balance = _gpc_amount(line[60:74], line[74])
            number = line[105:108].lstrip("0")
            stmt_date = _gpc_date(line[108:114])
            current = {
                "name": "GPC %s/%s" % (account, number or "?"),
                "date": stmt_date,
                "balance_start": old_balance,
                "balance_end_real": new_balance,
                "transactions": [],
            }
            current_account = account
            current_registered = False
            last_transaction = None
        elif record == "075":
            vals, currency_code, account = _transaction_vals(line, with_symbols)
            if current is None:
                # tolerate header-less files
                current = {
                    "name": "GPC %s" % account,
                    "date": vals["date"],
                    "transactions": [],
                }
                current_account = account
                current_registered = False
            if not current_registered:
                # the first transaction fixes the block's currency
                groups.setdefault(
                    (currency_code, current_account), []
                ).append(current)
                current_registered = True
            current["transactions"].append(vals)
            last_transaction = vals
        elif record in ("076", "078", "079"):
            # bank-specific AV message lines belong to the last item
            message = line[3:].strip()
            if last_transaction is not None and message:
                last_transaction["payment_ref"] = "%s %s" % (
                    last_transaction["payment_ref"],
                    message,
                )
        # anything else: ignore (banks append proprietary records)

    # drop 074 blocks without any transaction: nothing to import, and
    # without a 075 line their currency is unknown
    result = []
    for (currency_code, account_number), stmts_vals in groups.items():
        stmts_vals = [vals for vals in stmts_vals if vals["transactions"]]
        if stmts_vals:
            result.append((currency_code, account_number, stmts_vals))
    return result


def _transaction_vals(line, with_symbols):
    own_account = line[3:19].lstrip("0")
    counter_account = line[19:35].lstrip("0")
    doc_number = line[35:48].lstrip("0")
    sign = GPC_SIGNS.get(line[60], 1)
    amount = sign * int(line[48:60]) / 100.0
    variable_symbol = line[61:71].lstrip("0")
    ks_field = line[71:81]
    counter_bank = ks_field[-8:-4]
    constant_symbol = ks_field[-4:]
    if not constant_symbol.strip("0"):
        constant_symbol = ""
    specific_symbol = line[81:91].lstrip("0")
    client_name = line[97:117].strip()
    currency_code = GPC_CURRENCIES.get(int(line[118:122] or 0))
    due_date = _gpc_date(line[122:128])

    counter_number = ""
    if counter_account:
        counter_number = counter_account
        if counter_bank.strip("0"):
            counter_number = "%s/%s" % (counter_account, counter_bank)
    ref_parts = [client_name or "GPC %s" % (doc_number or "?")]
    for label, value in (
        ("VS", variable_symbol),
        ("KS", constant_symbol),
        ("SS", specific_symbol),
    ):
        if value:
            ref_parts.append("%s:%s" % (label, value))
    if counter_number:
        ref_parts.append(counter_number)
    vals = {
        "date": due_date,
        "amount": amount,
        "payment_ref": " ".join(ref_parts),
        "unique_import_id": "%s-%s-%s-%s%s" % (
            own_account,
            line[122:128],
            doc_number,
            line[48:60],
            line[60],
        ),
    }
    if client_name:
        vals["partner_name"] = client_name
    if counter_number:
        vals["account_number"] = counter_number
    if with_symbols:
        for field_name, value in (
            ("variable_symbol", variable_symbol),
            ("constant_symbol", constant_symbol),
            ("specific_symbol", specific_symbol),
        ):
            if value:
                vals[field_name] = value
    return vals, currency_code, own_account
