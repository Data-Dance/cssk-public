# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""MT940 sample files built to the published bank layouts.

Two dialects of field :86:, because the two specifications this module is
written against disagree on subfield numbering:

* ``cs_message`` — Česká spořitelna MultiCash 3.2: ``KS:``/``VS:``/``SS:`` with a
  colon in ?20/?21/?22, ``.`` for an empty subfield, the ``GIBACZPX 0800`` /
  ``940 N2`` header lines.
* ``rb_message`` — Raiffeisenbank MT940 v4: ``KS``/``VS``/``SS`` zero-padded
  without a colon in ?21/?22/?23, ``-`` for empty, ?38 IBAN, ``:21:``/``:64:``.

:86: is wrapped at 65 characters (SWIFT line width) wherever it falls, so the
tests cover a subfield value split across lines.
"""

import base64

CS_ACCOUNT_25 = "0800/192000145399"
CS_ACCOUNT = "19-2000145399/0800"
CS_IBAN = "CZ6508000000192000145399"
RB_ACCOUNT_25 = "5500/0112233088"
RB_ACCOUNT = "112233088/5500"


def wrap86(text, width=65):
    """:86: as SWIFT lines: the first carries the tag, so it is 4 shorter."""
    first = width - 4
    lines = [text[:first]]
    rest = text[first:]
    while rest:
        lines.append(rest[:width])
        rest = rest[width:]
    return lines


def field86(text):
    lines = wrap86(text)
    return [":86:" + lines[0]] + lines[1:]


def cs_domestic_86(ks="308", vs="20260042", ss="77", bank="0300",
                   account="000000019012333", name="ODBERATEL AS",
                   purpose="FAKTURA 2026/0042"):
    """ČS domestic :86:. An empty symbol is the bare ``.`` the spec prescribes
    for an unfilled subfield."""
    def symbol(kind, value):
        return "%s:%s" % (kind, value) if value else "."

    return (
        "020?00TUZEMSKA PLATBA"
        "?20%s?21%s?22%s?23.?24VS2: /SS2: "
        "?25%s?26.?27.?28.?29.?30%s?31%s?32%s?33."
        % (symbol("KS", ks), symbol("VS", vs), symbol("SS", ss), purpose,
           bank, account, name)
    )


def cs_message(transactions, account=CS_ACCOUNT_25, number="00024/00001",
               opening="C260701CZK10000,00", closing="C260701CZK11234,50",
               opening_tag="60F", closing_tag="62F"):
    """One ČS message. ``transactions`` is a list of ``(line61, text86)``;
    ``text86`` may be None for a :61: without :86:."""
    lines = [":20:%s" % account.replace("/", "")[:16], ":25:%s" % account,
             ":28:%s" % number, ":%s:%s" % (opening_tag, opening)]
    for line61, text86 in transactions:
        lines.append(":61:%s" % line61)
        if text86 is not None:
            lines.extend(field86(text86))
    lines.append(":%s:%s" % (closing_tag, closing))
    lines.append("-}")
    return lines


def rb_message(transactions, account=RB_ACCOUNT_25, number="008/00001",
               opening="C260701CZK22244461,04",
               closing="C260701CZK22244647,67"):
    lines = [":20:260701%s" % account.split("/")[1], ":21:000",
             ":25:%s" % account, ":28:%s" % number, ":60F:%s" % opening]
    for line61, text86 in transactions:
        lines.append(":61:%s" % line61)
        if text86 is not None:
            lines.extend(field86(text86))
    lines.append(":62F:%s" % closing)
    lines.append(":64:%s" % closing)
    lines.append("-")
    return lines


def rb_domestic_86():
    return (
        "010?00HLADKA PLATBA?21KS0000000308?22VS0045135784"
        "?23SS0001234578?24BANKOVNI VYPIS 000?25POPL.TRN 0,00"
        "?26?27UCEL UHRADY?28?306800?31000019-0032103210"
        "?32STAVEBNI FIRMA NOVAK A SYNO?33VE S.R.O.?60?61?62?63"
    )


def rb_sepa_86():
    return (
        "020?21E2EREFERENCE123?22KURZ 26,47589000?23EKV EUR 12,00"
        "?24BANKOVNI VYPIS 000?26POPL.UCET ?27INVOICE 77?28-"
        "?30COBADEFFXXX?31/DE89370400440532013000?32FOREIGN GMBH?33-"
        "?38/DE89370400440532013000?60-?61-?62-?63-"
    )


def mt940_bytes(*messages, header=("GIBACZPX 0800", "940 N2", ""),
                encoding="cp852"):
    lines = list(header)
    for message in messages:
        lines.extend(message)
    return ("\r\n".join(lines) + "\r\n").encode(encoding)


def mt940_file(*messages, **kwargs):
    """Base64 of the file, as the import wizard's binary field holds it."""
    return base64.b64encode(mt940_bytes(*messages, **kwargs))
