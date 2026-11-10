# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""F-511/F-512, MU12/14/2014 published in ÚDZS bulletin1/2026.

Serialise reviewed notices. No eligibility, work-day or payment dates are
invented here. UTF8 XML is distinct from the ISO8859-2 text interface.
"""

from datetime import date
import re

from lxml import etree

SOURCE_URL = "https://www.udzs-sk.sk/wp-content/uploads/2026/01/VE_1_2026_sv.pdf"
SOURCE_SHA256 = "d45710720fed6130842f9f99ae549e92295b7a4c0f7299d69b736cdd535008c6"
SCHEMA_SHA256 = "199eb6d5c55bb442804ed869b67ab1435ff8af1ef545dfacafa41d9950dbb393"


def text(value, maximum, minimum=0):
    value = str(value or "")
    if (
        any(ord(char) < 32 or ord(char) == 127 or char == "|" for char in value)
        or len(value) > maximum
        or (minimum and len(value.strip()) < minimum)
    ):
        raise ValueError("Missing, overlong or unsafe registration text")
    return value


def digits(value, minimum, maximum=None, *, optional=False):
    value = text(value, maximum or minimum)
    if optional and not value:
        return value
    if not re.fullmatch(r"[0-9]+", value) or not minimum <= len(value) <= (
        maximum or minimum
    ):
        raise ValueError("Invalid registration identifier or numeric field")
    return value


def day(value):
    if isinstance(value, date):
        value = value.isoformat()
    if not re.fullmatch(r"[0-9]{4}-[0-9]{2}-[0-9]{2}", str(value)):
        raise ValueError("A registration date must identify an actual ISO calendar day")
    return date.fromisoformat(value)


def integer(value, width):
    if type(value) is not int or value < 1 or len(str(value)) > width:
        raise ValueError("Invalid positive registration sequence")
    return str(value)


def iban(value):
    value = text(value, 34, 15)
    if not re.fullmatch(r"[A-Z]{2}[0-9]{2}[A-Z0-9]+", value):
        raise ValueError("Invalid registration IBAN")
    expanded = "".join(
        str(ord(char) - 55) if char.isalpha() else char
        for char in value[4:] + value[:4]
    )
    if int(expanded) % 97 != 1:
        raise ValueError("Invalid registration IBAN checksum")
    return value


def records(ident, payer, events):
    """Return exactly10/25/9 fields with reviewed identities and dates.

    N/O is a batch characteristic; Z/K/X is a separate event fact. A codec
    cannot establish which past endpoint an X is intended to cancel.
    """
    characteristic = ident["characteristic"]
    if characteristic not in {"N", "O"}:
        raise ValueError("601 supports original N and corrective O batches")
    sent = day(ident["sent_on"])
    insurer = digits(ident["insurer"], 4)
    if insurer[:2] not in {"24", "25", "27"}:
        raise ValueError("Unsupported health insurer")
    if not 1 <= len(events) <= 99999:
        raise ValueError("A single registration batch needs1–99999 events")
    header = [
        characteristic,
        "601",
        digits(ident["sender"], 8, 10),
        digits(ident["receiver"], 8),
        insurer,
        sent.strftime("%Y%m%d"),
        integer(ident["sequence"], 6),
        str(len(events)),
        "1",
        "1",
    ]
    period = day(str(payer["period"]) + "-01")
    identities = [
        digits(payer.get("ico"), 8, optional=True),
        digits(payer.get("birth_number"), 9, 10, optional=True),
        text(payer.get("residence_number"), 10),
    ]
    if sum(bool(value) for value in identities) != 1:
        raise ValueError("Identify the payer by exactly one published identifier")
    form = payer["legal_form"]
    if form not in {"FO", "PO"}:
        raise ValueError("The legal form must be FO or PO")
    country = text(payer.get("country") or "SK", 2, 2)
    if not re.fullmatch(r"[A-Z]{2}", country):
        raise ValueError("Use a two-letter ISO country code")
    postcode = digits(payer["postcode"], 5)
    telephone = text(payer["phone"], 15, 8)
    fax = text(payer.get("fax"), 15)
    if fax and len(fax) < 8:
        raise ValueError("An optional fax must contain8–15 characters")
    address = [
        text(payer["payer"], 10, 1),
        insurer[:2],
        insurer[2:],
        period.strftime("%m"),
        period.strftime("%y"),
        text(payer["name"], 60, 1),
        *identities,
        text(payer.get("tax_id"), 13),
        form,
        text(payer["town"], 25, 1),
        text(payer.get("house_number"), 8),
        text(payer["street"], 35, 1),
        postcode,
        country,
        telephone,
        fax,
        text(payer.get("email"), 75),
        text(payer.get("bank_name"), 60),
        digits(payer.get("account_prefix"), 1, 6, optional=True),
        digits(payer.get("account_number"), 1, 10, optional=True),
        digits(payer.get("bank_code"), 4, optional=True),
        text(payer["responsible_person"], 50, 1),
        iban(payer["iban"]),
    ]
    body, seen = [], set()
    for sequence, event in enumerate(events, 1):
        rc = digits(event.get("birth_number"), 9, 10, optional=True)
        bic = digits(event.get("insurer_identifier"), 10, optional=True)
        if bool(rc) == bool(bic):
            raise ValueError("Use exactly one assigned insured-person identifier")
        code, validity = event["code"], event["validity"]
        if not re.fullmatch(r"1[A-W]|2|2D|2N|2P|2Y|2S", str(code)):
            raise ValueError("Unknown registration code")
        if validity not in {"Z", "K", "X"}:
            raise ValueError("Unknown registration change validity")
        changed = day(event["changed_on"]).strftime("%Y%m%d")
        title = text(event.get("title"), 12)
        if title and len(title.strip()) < 3:
            raise ValueError("A supplied title must contain3–12 characters")
        identity = (rc, bic, code, validity, changed)
        if identity in seen:
            raise ValueError("A registration event is duplicated in the batch")
        seen.add(identity)
        body.append(
            [
                str(sequence),
                rc,
                title,
                text(event["first_name"], 24, 1),
                text(event["last_name"], 36, 1),
                code,
                validity,
                changed,
                bic,
            ]
        )
    return header, address, body


def filename(ident, *, xml=False):
    sender = digits(ident["sender"], 8, 10)
    return (
        sender + day(ident["sent_on"]).strftime("%y%m%d") + (".xml" if xml else ".601")
    )


def render_text(ident, payer, events):
    header, address, body = records(ident, payer, events)
    result = (
        "\r\n".join("|".join(row) + "|" for row in [header, address, *body]) + "\r\n"
    )
    try:
        return result.encode("iso8859-2")
    except UnicodeEncodeError as exc:
        raise ValueError(
            "The601 text charset cannot represent these names; use UTF8 XML"
        ) from exc


def render_xml(ident, payer, events):
    header, address, body = records(ident, payer, events)
    root = etree.Element("davka601")

    def fill(parent, names, values, optional=()):
        for name, value in zip(names, values, strict=True):
            if value or name not in optional:
                etree.SubElement(parent, name).text = value

    fill(
        etree.SubElement(root, "Identification"),
        [
            "PatternOfBatch",
            "TypeOfBatch",
            "IDCode",
            "IDCodeReceiver",
            "CodeOfHealthInsuranceCompanyWithBranch",
            "DateOfSending",
            "SerialNumberOfBatch",
            "NumberOfRecords",
            "NumberOfDataMedium",
            "SerialNumberOfDataMedium",
        ],
        header,
    )
    company = etree.SubElement(root, "CorporateBody")
    fill(
        company,
        [
            "CodeOfPayerSec",
            "CodeOfHealthInsuranceCompany",
            "CodeOfBranchOfHealthInsuranceCompany",
            "MonthOfChange",
            "YearOfChange",
            "CorporateBodyFullName",
        ],
        address[:6],
    )
    for name, value in zip(
        ["CompanyIDCode", "IdentificationNumberOfPayer", "NumberOfResidencePermit"],
        address[6:9],
        strict=True,
    ):
        if value:
            etree.SubElement(company, name).text = value
    fill(
        company, ["CompanyIDTaxCode", "LegalForm"], address[9:11], ("CompanyIDTaxCode",)
    )
    fill(
        etree.SubElement(company, "Address"),
        ["Town", "DescriptiveNumber", "StreetNumber", "PostalCode", "Country"],
        address[11:16],
        ("DescriptiveNumber",),
    )
    fill(company, ["Telephone", "Fax", "Email"], address[16:19], ("Fax", "Email"))
    # The published XML requires the container even when all optional
    # national-bank details are absent; IBAN is a separate mandatory field.
    fill(
        etree.SubElement(company, "BankAccount"),
        ["BankName", "AccountPrefix", "AccountNumber", "BankCode"],
        address[19:23],
        ("BankName", "AccountPrefix", "AccountNumber", "BankCode"),
    )
    fill(company, ["ResponsiblePerson", "IBAN"], address[23:25])
    for row in body:
        person = etree.SubElement(root, "PersonData")
        fill(person, ["SerialNumberOfLine"], row[:1])
        fill(
            person,
            [
                "IdentificationNumberOfInsured"
                if row[1]
                else "NonSemanticIdentificationNumber"
            ],
            [row[1] or row[8]],
        )
        fill(
            person,
            [
                "Title",
                "Name",
                "Surname",
                "CodeOfChange",
                "ValidationOfChange",
                "DateOfChange",
            ],
            row[2:8],
            ("Title",),
        )
    return etree.tostring(root, encoding="UTF-8", xml_declaration=True)
