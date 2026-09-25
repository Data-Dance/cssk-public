# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""GPC sample-record builders, shared by the CE and EE import shims so both
assert against byte-identical files."""

import base64

ACCOUNT = "192000145399"


def rec074(
    account=ACCOUNT,
    name="FIRMA SRO",
    old_date="300626",
    old_balance=1000000,  # haléře
    old_sign="+",
    new_balance=1123450,
    new_sign="+",
    number="007",
    date="010726",
):
    rec = (
        "074"
        + account.rjust(16, "0")
        + name.ljust(20)
        + old_date
        + str(abs(old_balance)).rjust(14, "0")
        + old_sign
        + str(abs(new_balance)).rjust(14, "0")
        + new_sign
        + "0" * 14 + "0"
        + "0" * 14 + "0"
        + number
        + date
        + " " * 14
    )
    assert len(rec) == 128, len(rec)
    return rec


def rec075(
    account=ACCOUNT,
    counter_account="19012333",
    doc_number="1234567",
    amount=123450,  # haléře
    code="2",
    vs="20260042",
    bank_code="0300",
    ks="0308",
    ss="",
    client="ODBERATEL AS",
    currency="0203",
    date="010726",
):
    ks_field = (bank_code + ks.rjust(4, "0")).rjust(10, "0") if (
        ks or bank_code
    ) else "0" * 10
    rec = (
        "075"
        + account.rjust(16, "0")
        + counter_account.rjust(16, "0")
        + doc_number.rjust(13, "0")
        + str(abs(amount)).rjust(12, "0")
        + code
        + vs.rjust(10, "0")
        + ks_field
        + ss.rjust(10, "0")
        + "000000"
        + client.ljust(20)
        + "0"
        + currency
        + date
    )
    assert len(rec) == 128, len(rec)
    return rec


def gpc_bytes(*records):
    """Raw file bytes — what the Enterprise framework hands to a parser."""
    return ("\r\n".join(records) + "\r\n").encode("cp1250")


def gpc_file(*records):
    """Base64 payload — what the OCA import wizard takes."""
    return base64.b64encode(gpc_bytes(*records))
