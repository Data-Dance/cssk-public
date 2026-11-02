# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""Fio sample-payload builders, shared by every downstream module's tests.

The samples follow the documentation's own examples (§5.3.1.1, §5.3.1.6,
§6.1), with the account numbers replaced. Keeping them here means the puller,
the Community bridge and the Enterprise bridge all assert against byte-
identical payloads.
"""

import json

ACCOUNT_ID = "2111111111"
BANK_ID = "2010"
IBAN = "CZ8020100000002111111111"
BIC = "FIOBCZPPXXX"


def movement(movement_id=1147608196, date="2012-07-27+02:00", amount="-15.00",
             currency="CZK", columns=None):
    """One movement, as a ``{column id: value}`` dict.

    ``columns`` carries the optional columns by their Fio number, which is how
    the documentation identifies them — integer keys, so it is a dict argument
    rather than keyword arguments.
    """
    values = {
        22: movement_id,
        0: date,
        1: amount,
        14: currency,
    }
    values.update(columns or {})
    return values


COLUMN_NAMES = {
    0: "Datum", 1: "Objem", 2: "Protiúčet", 3: "Kód banky", 4: "KS", 5: "VS",
    6: "SS", 7: "Uživatelská identifikace", 8: "Typ", 9: "Provedl",
    10: "Název protiúčtu", 12: "Název banky", 14: "Měna",
    16: "Zpráva pro příjemce", 17: "ID pokynu", 18: "Upřesnění",
    22: "ID pohybu", 25: "Komentář", 26: "BIC", 27: "Reference plátce",
}


def statement_xml(movements=(), info=None):
    """A Fio XML movement list (§5.3.1.1)."""
    info_values = {
        "accountId": ACCOUNT_ID,
        "bankId": BANK_ID,
        "currency": "CZK",
        "iban": IBAN,
        "bic": BIC,
        "openingBalance": "7356.22",
        "closingBalance": "7321.22",
        "dateStart": "2012-07-01+02:00",
        "dateEnd": "2012-07-31+02:00",
    }
    if info is not None:
        info_values = dict(info_values, **info)
        info_values = {k: v for k, v in info_values.items() if v is not None}
    parts = ["<?xml version='1.0' encoding='UTF-8'?>", "<AccountStatement>", "<Info>"]
    for key, value in info_values.items():
        parts.append("<%s>%s</%s>" % (key, value, key))
    parts.append("</Info>")
    parts.append("<TransactionList>")
    for values in movements:
        parts.append("<Transaction>")
        for column_id, value in values.items():
            parts.append(
                '<column_%s id="%s" name="%s">%s</column_%s>'
                % (column_id, column_id, COLUMN_NAMES.get(column_id, ""),
                   "" if value is None else value, column_id)
            )
        parts.append("</Transaction>")
    parts.extend(["</TransactionList>", "</AccountStatement>"])
    return "".join(parts).encode("utf-8")


def statement_json(movements=(), info=None, epoch_dates=True):
    """A Fio JSON movement list (§5.3.1.6).

    ``epoch_dates`` reproduces the documentation's own example, which returns
    milliseconds where its field table promises ``rrrr-mm-dd+GMT``.
    """
    info_values = {
        "accountId": ACCOUNT_ID,
        "bankId": BANK_ID,
        "currency": "CZK",
        "iban": IBAN,
        "bic": BIC,
        "openingBalance": 7356.22,
        "closingBalance": 7321.22,
        "dateStart": 1340661600000 if epoch_dates else "2012-06-26+02:00",
        "dateEnd": 1341007200000 if epoch_dates else "2012-06-30+02:00",
        "yearList": None,
        "idList": None,
        "idFrom": None,
        "idTo": None,
        "idLastDownload": None,
    }
    if info is not None:
        info_values.update(info)
    transactions = []
    for values in movements:
        transaction = {}
        for column_id, value in values.items():
            transaction["column%s" % column_id] = None if value is None else {
                "value": value,
                "name": COLUMN_NAMES.get(column_id, ""),
                "id": column_id,
            }
        transactions.append(transaction)
    payload = {
        "accountStatement": {
            "info": info_values,
            "transactionList": {"transaction": transactions} if transactions else None,
        }
    }
    return json.dumps(payload, ensure_ascii=False).encode("utf-8")


def import_response(error_code=0, id_instruction="1704810070", status="ok",
                    sum_debet="1234.50", sum_credit="0.00", messages=()):
    """The XML answer of ``/import/`` (§6.1)."""
    parts = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        "<responseImport>",
        "<errorCode>%s</errorCode>" % error_code,
        "<idInstruction>%s</idInstruction>" % id_instruction,
        "<status>%s</status>" % status,
        "<sumDebet>%s</sumDebet>" % sum_debet,
        "<sumCredit>%s</sumCredit>" % sum_credit,
        "<ordersDetails>",
    ]
    for index, (message_status, code, text) in enumerate(messages, start=1):
        parts.append('<detail id="%s"><messages>' % index)
        parts.append(
            '<message status="%s" errorCode="%s">%s</message>'
            % (message_status, code, text)
        )
        parts.append("</messages></detail>")
    parts.extend(["</ordersDetails>", "</responseImport>"])
    return "".join(parts).encode("utf-8")
