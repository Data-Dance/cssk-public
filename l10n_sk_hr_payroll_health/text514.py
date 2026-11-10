# Copyright 2026 Data Dance s.r.o., votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Dávka514 text wire format, VšZP published 2023+ specification.

This module serialises reviewed assessment facts; it never calculates a
second payroll. The report adapter supplies both disability groups, OP,
minimum opt-out and actual premium values from their original source.
"""

from datetime import date
from calendar import monthrange
from decimal import Decimal, InvalidOperation
import re


SOURCE_URL = (
    "https://www.vszp.sk/files/platitelia/tlaciva-platitelov/"
    "vykaz-preddavkov-zamestnavatela/struktura-vykazu-1.rtf"
)
SOURCE_SHA256 = "b96e53a21f1cf4f8c47f0dac35558fc3df33aa0f3b0fc75f147d74b7f6bfa789"


def text(value, maximum, required=False):
    value = str(value or "")
    if any(char in value for char in "|\r\n\x00"):
        raise ValueError("A text field contains a record separator")
    if len(value) > maximum or (required and not value.strip()):
        raise ValueError("Missing or overlong text field")
    return value


def integer(value, maximum, minimum=0):
    if isinstance(value, bool) or not re.fullmatch(r"[0-9]+", str(value)):
        raise ValueError("Expected a nonnegative integer")
    number = int(value)
    if number < minimum or len(str(number)) > maximum:
        raise ValueError("Integer is outside the published field limits")
    return str(number)


def money(value, maximum=12):
    try:
        number = Decimal(str(value))
        valid = number.is_finite() and number == number.quantize(Decimal(".01"))
    except (InvalidOperation, ValueError) as exc:
        raise ValueError("Money must be finite and already rounded to cents") from exc
    if not valid:
        raise ValueError("Money must be finite and already rounded to cents")
    if number == 0:
        number = abs(number)
    result = format(number, ".2f")
    if len(result.replace(".", "").replace("-", "")) > maximum:
        raise ValueError("Money exceeds the published precision")
    return result.replace(".", ",")


def checked_period(value):
    value = str(value)
    if not re.fullmatch(r"20[0-9]{2}(0[1-9]|1[0-2])", value) or int(value) < 202301:
        raise ValueError("The text edition applies from January2023")
    return value


def aggregate(rows, registered, registered_all_insurers):
    """Sum source facts, keeping ZP groups and employee top-up separate.

    ``disabled`` is an assessment fact, not inferred from rounded premiums.
    Registered counts come from registration evidence: a whole-month PN row
    may be registered even though no premium is payable. This function never
    calculates a base, OP, premium, insured days or registration count.
    """
    result = {
        "registered": registered,
        "registered_all_insurers": registered_all_insurers,
        "total": Decimal(0),
    }
    for group in ("standard", "disabled"):
        for key in ("count", "days", "income", "base", "er", "ee"):
            result[key + "_" + group] = 0 if key in ("count", "days") else Decimal(0)
        result["rate_er_" + group] = result["rate_ee_" + group] = None
    for row in rows:
        if type(row["disabled"]) is not bool:
            raise ValueError("The disability group must be an explicit assessment fact")
        group = "disabled" if row["disabled"] else "standard"
        # The wire header has only one rate per group. Do not hide two
        # different historical rates behind whichever row happens to be last.
        for side, key in (("er", "rate_employer"), ("ee", "rate_employee")):
            previous = result["rate_" + side + "_" + group]
            rate = Decimal(str(row[key]))
            money(rate, 4)
            if previous is not None and previous != rate:
                raise ValueError("Conflicting rates within one disability group")
            result["rate_" + side + "_" + group] = rate
        days = int(integer(row["days"], 2))
        if days > 31:
            raise ValueError("Invalid insured days")
        # Header6/7 is not simply the number of paid rows or registered
        # people. Keep the source's assessment status, including zero OP.
        if type(row["premium_assessed"]) is not bool:
            raise ValueError("Premium-assessed status must be an explicit fact")
        result["count_" + group] += int(row["premium_assessed"])
        result["days_" + group] += days
        er_base = (
            row["shorttime_base"]
            if row["shorttime_base"] is not None
            else row["income"]
        )
        for target, value in (
            ("income", er_base),
            ("base", row["base"]),
            ("er", row["employer"]),
            ("ee", Decimal(str(row["employee"])) + Decimal(str(row["topup"]))),
        ):
            money(value)
            result[target + "_" + group] += Decimal(str(value))
        result["total"] += Decimal(str(row["total"]))
    return result


def render(ident, employer, summary, rows):
    """Emit UTF8, four header/body record types, decimal commas and final |."""
    characteristic = ident["characteristic"]
    if characteristic not in {"N", "O", "A"}:
        raise ValueError("Unknown declaration characteristic")
    period = checked_period(employer["period"])
    sent = date.fromisoformat(ident["sent_on"])
    payer = text(ident["payer"], 10, required=True)
    ico = text(ident["ico"], 10, required=True)
    if not re.fullmatch(r"[0-9]{8,10}", ico) or not re.fullmatch(r"[0-9]{10}", payer):
        raise ValueError("Invalid employer or insurer payer identifier")
    insurer = str(ident["insurer"])
    if insurer not in {"2400", "2500", "2700"}:
        raise ValueError("Unsupported health insurer code")
    sequence = integer(ident["sequence"], 6, minimum=1)
    if int(sequence) > 999:
        raise ValueError(
            "A single-file batch sequence must fit its three-digit extension"
        )
    header = [
        characteristic,
        "514",
        ico,
        payer,
        insurer,
        sent.strftime("%Y%m%d"),
        sequence,
        integer(len(rows), 6),
        "1",
        "1",
    ]
    address = [
        period,
        integer(employer["payment_day"], 2, minimum=1),
        text(employer["name"], 80, required=True),
        ico,
        payer,
        text(employer["dic"], 12),
        text(employer.get("phone"), 13),
        text(employer.get("fax"), 13),
        text(employer.get("email"), 75),
        text(employer.get("bank_code"), 4),
        text(employer.get("bank_prefix"), 6),
        text(employer.get("bank_account"), 10),
        text(employer["iban"], 34, required=True),
    ]
    if int(address[1]) > 31:
        raise ValueError("Invalid payment day")
    iban = address[-1]
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]{11,30}", iban):
        raise ValueError("Invalid IBAN syntax")
    check = "".join(
        str(ord(char) - 55) if char.isalpha() else char for char in iban[4:] + iban[:4]
    )
    if int(check) % 97 != 1:
        raise ValueError("Invalid IBAN checksum")
    count_fields = (
        "registered",
        "count_standard",
        "count_disabled",
        "days_standard",
        "days_disabled",
    )
    counts = {
        key: integer(summary[key], 8 if key.startswith("days") else 7)
        for key in count_fields
    }
    aggregate = [counts["registered"]] + [
        money(summary[key], 4) if summary.get(key) is not None else ""
        for key in (
            "rate_er_standard",
            "rate_ee_standard",
            "rate_er_disabled",
            "rate_ee_disabled",
        )
    ]
    aggregate += [
        counts[key]
        for key in (
            "count_standard",
            "count_disabled",
            "days_standard",
            "days_disabled",
        )
    ]
    aggregate += [
        money(summary[key])
        for key in (
            "income_standard",
            "income_disabled",
            "base_standard",
            "base_disabled",
            "er_standard",
            "ee_standard",
            "er_disabled",
            "ee_disabled",
            "total",
        )
    ]
    aggregate += [
        text(employer["legal_form"], 20, required=True),
        integer(summary["registered_all_insurers"], 7),
    ]
    records = [header, address, aggregate]
    total = Decimal(0)
    insured_identifiers = set()
    for index, row in enumerate(rows, 1):
        rc = str(row["birth_number"])
        if not re.fullmatch(r"[0-9]{9,10}", rc):
            raise ValueError(
                "A birth number must retain its original nine or ten digits"
            )
        if rc in insured_identifiers:
            raise ValueError(
                "Consolidate all rows of the same insured person before serialising514"
            )
        insured_identifiers.add(rc)
        days = integer(row["days"], 2)
        if (
            int(days) > monthrange(int(period[:4]), int(period[4:]))[1]
            or type(row["minimum_opt_out"]) is not int
            or row["minimum_opt_out"] not in (0, 1)
        ):
            raise ValueError("Invalid insured days or minimum opt-out")
        er, ee, topup = (
            Decimal(str(row[key])) for key in ("employer", "employee", "topup")
        )
        if Decimal(str(row["total"])) != er + ee + topup or (
            row["minimum_opt_out"] and topup
        ):
            raise ValueError("Premium components do not match the reported total")
        total += er + ee + topup
        records.append(
            [
                integer(index, 6),
                rc,
                days,
                money(row["rate_employer"], 4),
                money(row["rate_employee"], 4),
            ]
            + [
                money(row[key])
                for key in (
                    "income",
                    "base",
                    "employer",
                    "employee",
                    "total",
                    "op_income",
                    "other_income",
                    "op",
                )
            ]
            + [
                money(row["exempt_income"], 5),
                money(row["shorttime_base"])
                if row["shorttime_base"] is not None
                else "",
                str(row["minimum_opt_out"]),
                money(row["topup"]),
            ]
        )
    if total != Decimal(str(summary["total"])):
        raise ValueError("Employee rows do not match the employer premium total")
    return ("\r\n".join("|".join(record) + "|" for record in records) + "\r\n").encode(
        "utf-8"
    )


def filename(characteristic, period, sequence):
    sequence = int(integer(sequence, 3, minimum=1))
    period = checked_period(period)
    if characteristic not in {"N", "O", "A"}:
        raise ValueError("Invalid batch filename inputs")
    return characteristic + "514" + str(period)[2:] + ".%03d" % int(sequence)
