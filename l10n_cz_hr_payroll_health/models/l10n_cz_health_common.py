# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Shared constants and helpers for the CZ health-insurance e-filings.

Both employer filings (PPPZ premium overview + HOZ registration) share the same
VZP-published XML envelope: the ``kodZdravotniPojistovny`` insurer code, the
``identifikaceZamestnavatele`` employer identification block (payer number, name,
address) and the ``string60Typ`` truncation rules. This module keeps that
common material in one place so the two report models stay thin.
"""

# ---------------------------------------------------------------------------
# CZ health insurers (kodZdravotniPojistovnyTyp) — valid to 1.1.2026.
# The SAME PPPZ/HOZ XML format is filed to EACH insurer via that insurer's own
# channel (VZP Point for VZP, the shared "Portál zdravotních pojišťoven" for the
# rest); only this code + the filing channel differ, so the insurer is modelled
# as a selection rather than one module per insurer.
# ---------------------------------------------------------------------------
CZ_HEALTH_INSURERS = [
    ("111", "111 — VZP (Všeobecná zdravotní pojišťovna)"),
    ("201", "201 — VoZP (Vojenská zdravotní pojišťovna)"),
    ("205", "205 — ČPZP (Česká průmyslová zdravotní pojišťovna)"),
    ("207", "207 — OZP (Oborová zdravotní pojišťovna)"),
    ("209", "209 — ZPŠ (Zaměstnanecká pojišťovna Škoda)"),
    ("211", "211 — ZPMV ČR (Zdravotní pojišťovna ministerstva vnitra)"),
    ("213", "213 — RBP (Revírní bratrská pokladna)"),
]


def digits_only(value):
    """Keep only the digits of ``value`` (e.g. strip spaces/slashes from a
    birth number or IČ)."""
    return "".join(ch for ch in (value or "") if ch.isdigit())


def health_payer_number(company):
    """The 10-digit ``identifikacniCisloPlatce`` for ``company``.

    Uses the explicit health payer number if set (validated to 10 digits),
    otherwise derives it from the company IČ (``company_registry``) as
    ``<IČ padded to 8>00`` (single accounting office). Returns "" when neither
    is usable (the caller raises a friendly preflight error)."""
    explicit = digits_only(company.l10n_cz_health_payer_number)
    if len(explicit) == 10:
        return explicit
    ico = digits_only(company.company_registry or company.vat)
    if not ico:
        return ""
    return ico[:8].rjust(8, "0") + "00"


def health_employer_identification(company):
    """Build the shared ``identifikaceZamestnavatele`` attribute/value dict
    (payer number, name, address) used identically by PPPZ and HOZ. Every value
    is pre-truncated to its ``string60Typ`` / ``string80Typ`` XSD limit."""
    street = (company.street or "").strip()
    house = (company.street2 or "").strip()
    if not house:
        # Split a trailing house number off "Street 12" if street2 is empty.
        parts = street.rsplit(" ", 1)
        if len(parts) == 2 and any(c.isdigit() for c in parts[1]):
            street, house = parts[0].strip(), parts[1].strip()
    values = {
        "identifikacniCisloPlatce": health_payer_number(company),
        "nazevPlatce": (company.name or "")[:80],
        "adresaPlatceUlice": (street or company.city or "-")[:60],
        "adresaPlatceCisloPopisneOrientacni": (house or "0")[:60],
        "adresaPlatcePsc": digits_only(company.zip)[:5].rjust(5, "0"),
        "adresaPlatceObec": (company.city or "-")[:60],
    }
    phone = digits_only(company.phone)
    if phone:
        values["adresaPlatceTelefon"] = phone[:30]
    return values
