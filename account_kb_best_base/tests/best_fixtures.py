# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""BEST electronic-statement records, built to KB's published layout
(*Klientský formát BEST*, 2.4.2 — 475-byte records) and checked against the
bank's sample statements ``Priklad_20170510_CZK.okm`` / ``…_USD.okm``."""

import base64

ACCOUNT16 = "0900930669910217"
IBAN = "CZ5901000900930669910217"
NATIONAL = "90093-669910217/0100"

# field offsets of a 52 record, for tests that read a built file back
F52 = {
    "txno": (2, 5), "account": (7, 16), "counter": (23, 16), "bank": (39, 7),
    "ku": (46, 1), "currency": (47, 3), "amount": (50, 15), "kbi": (86, 31),
    "vs": (117, 10), "ks": (137, 10), "ss": (147, 10), "booked": (175, 8),
    "code": (199, 2), "desc1": (209, 30), "desc2": (239, 30), "av": (269, 140),
    "system": (409, 30), "name": (439, 30), "flag": (471, 1),
}


def _n(value, width):
    return str(value).rjust(width, "0")


def _x(value, width):
    return (value or "")[:width].ljust(width)


def header(created="260702"):
    return ("HO" + "BEST     " + created + _x("MojeBanka-export trans. hist.", 30)
            + _x("Pouze ucetni transakce", 30)).ljust(473)


def turnover(account16=ACCOUNT16, booked="20260701", number="020",
             previous="20260630", count=1, old=1000000, new=1123450,
             debit=0, credit=123450, name="FIRMA CZK", iban=IBAN):
    def signed(cents):
        return _n(abs(cents), 15) + ("-" if cents < 0 else "+")

    rec = ("51" + account16 + booked + number + previous + _n(count, 5)
           + signed(old) + signed(new) + signed(debit) + signed(credit)
           + _x(name, 30) + _x(iban, 24))
    return rec.ljust(473)


def transaction(txno=1, account16=ACCOUNT16, counter16="0000000019012333",
                bank="0300", ku="1", currency="CZK", cents=123450,
                kbi="001-01072026 1602 602021 005093", vs="20260042",
                ks="0308", ss="", booked="20260701", code="15",
                desc_debit="Dodavatelska faktura", desc_credit="Faktura 42",
                av=("FA 2026/0042",), system="Platba ve prospech vaseho uctu",
                name="ODBERATEL AS", flag=" ", record="52"):
    rec = (record + _n(txno, 5) + account16 + counter16 + _n(bank, 7) + ku
           + currency + _n(cents, 15) + currency + _n(cents, 15) + "0  "
           + _x(kbi, 31) + _n(vs or 0, 10) + _n(vs or 0, 10) + _n(ks or 0, 10)
           + _n(ss or 0, 10) + _n(ss or 0, 10) + booked * 4 + code + "   " + "0"
           + "0000" + _x(desc_debit, 30) + _x(desc_credit, 30)
           + "".join(_x(line, 35) for line in (list(av) + ["", "", "", ""])[:4])
           + _x(system, 30) + _x(name, 30) + "  " + flag + " ")
    assert len(rec) == 473, len(rec)
    return rec


def trailer(created="260702", count=2, cents=123450):
    return ("TO" + " " * 9 + created + _n(count, 6) + _n(cents, 18)).ljust(473)


def best_bytes(*records):
    return ("\r\n".join(records) + "\r\n").encode("cp1250")


def best_file(*records):
    return base64.b64encode(best_bytes(*records))


def statement(*transactions, **turnover_kwargs):
    """A whole file: header, one turnover record, the transactions, trailer."""
    records = [header(), turnover(count=len(transactions), **turnover_kwargs)]
    records.extend(transactions)
    records.append(trailer(count=len(transactions) + 1))
    return best_bytes(*records)
