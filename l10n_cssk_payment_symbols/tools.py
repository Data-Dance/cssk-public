# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

"""The payment symbols in the text of an outgoing bank payment.

Shared by every exporter that writes them (the Enterprise ISO 20022 bridge
and the OCA SEPA bridge), so the two can never write different formats.
``symbols`` is a dict with any of the keys ``VS``, ``KS`` and ``SS``.
"""


def end_to_end_id(symbols):
    """``/VS123/SS456/KS0308`` — the Slovak placement of the symbols.

    Slovak banks read the symbols out of ``EndToEndId`` in exactly this
    shape, value glued to its tag (VÚB, "SEPA Credit Transfer — formát pre
    klientov": "v dohodnutej štruktúre napr. /VS123/SS456/KS0308", example
    ``<EndToEndId>/VS1234567890/SS1234567890/KS0308``). At most 10+10+4
    digits and 9 marker characters, so it always fits the 35-character field.
    """
    return "".join(
        "/%s%s" % (key, symbols[key]) for key in ("VS", "SS", "KS") if symbols.get(key)
    )[:35]


def remittance_suffix(symbols):
    """``/VS/123/KS/0308/SS/456`` — the symbols as the remittance information
    of a payment carries them (the ČBA-documented placement)."""
    return "".join(
        "/%s/%s" % (key, symbols[key]) for key in ("VS", "KS", "SS") if symbols.get(key)
    )
