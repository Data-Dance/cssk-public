# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Rate knowledge the OSS return needs and core ``l10n_eu_oss`` does not hold.

Two things live here, both data rather than logic:

* ``EU_STANDARD_RATES`` — each member state's STANDARD rate with the date it
  took effect. Both OSS forms ask for the rate TYPE of every row (CZ OSSEI1
  ``vat_rate_type_code`` Z/S, the EU schema's ``VATRate/@type``
  STANDARD/REDUCED), and core's map only knows rates, not which of them is
  the standard one. A rate is typed by comparing it with the standard rate in
  force on the last day of the period, so a 20 % Slovak row in 2024 reads
  standard and a 20 % row in 2025 would read reduced — which is why the table
  carries dates instead of one number per country. Only changes since the
  Union scheme began (1. 7. 2021) matter.
* ``sk_five_percent_overlay`` — the Slovak 5 % rate that core's
  ``EU_TAX_MAP`` lacks in both directions (see the function).
"""

from datetime import date

#: The OSS scheme's first day; nothing earlier can be filed or corrected on
#: these forms (CZ OSSEI1: "Musí být větší než Q2 2021").
OSS_UNION_SCHEME_START = date(2021, 7, 1)

#: country code -> [(valid_from, standard rate %)], oldest first.
EU_STANDARD_RATES = {
    "AT": [(date(2021, 7, 1), 20.0)],
    "BE": [(date(2021, 7, 1), 21.0)],
    "BG": [(date(2021, 7, 1), 20.0)],
    "CY": [(date(2021, 7, 1), 19.0)],
    "CZ": [(date(2021, 7, 1), 21.0)],
    "DE": [(date(2021, 7, 1), 19.0)],
    "DK": [(date(2021, 7, 1), 25.0)],
    "EE": [(date(2021, 7, 1), 20.0), (date(2024, 1, 1), 22.0),
           (date(2025, 7, 1), 24.0)],
    "ES": [(date(2021, 7, 1), 21.0)],
    "FI": [(date(2021, 7, 1), 24.0), (date(2024, 9, 1), 25.5)],
    "FR": [(date(2021, 7, 1), 20.0)],
    "GR": [(date(2021, 7, 1), 24.0)],
    "HR": [(date(2021, 7, 1), 25.0)],
    "HU": [(date(2021, 7, 1), 27.0)],
    "IE": [(date(2021, 7, 1), 23.0)],
    "IT": [(date(2021, 7, 1), 22.0)],
    "LT": [(date(2021, 7, 1), 21.0)],
    # Luxembourg cut every rate by one point for 2023 only.
    "LU": [(date(2021, 7, 1), 17.0), (date(2023, 1, 1), 16.0),
           (date(2024, 1, 1), 17.0)],
    "LV": [(date(2021, 7, 1), 21.0)],
    "MT": [(date(2021, 7, 1), 18.0)],
    "NL": [(date(2021, 7, 1), 21.0)],
    "PL": [(date(2021, 7, 1), 23.0)],
    "PT": [(date(2021, 7, 1), 23.0)],
    "RO": [(date(2021, 7, 1), 19.0), (date(2025, 8, 1), 21.0)],
    "SE": [(date(2021, 7, 1), 25.0)],
    "SI": [(date(2021, 7, 1), 22.0)],
    "SK": [(date(2021, 7, 1), 20.0), (date(2025, 1, 1), 23.0)],
}


def standard_rate(country_code, on_date):
    """Standard rate of ``country_code`` on ``on_date``, or None if unknown."""
    history = EU_STANDARD_RATES.get(country_code)
    if not history:
        return None
    rate = None
    for valid_from, value in history:
        if valid_from <= on_date:
            rate = value
    return rate


def rate_type(country_code, rate, on_date):
    """``'standard'`` / ``'reduced'`` for a row, or None when it cannot tell.

    None rather than a guess: a row typed wrongly validates perfectly against
    both schemas, so the caller turns None into a named kontrola instead.
    """
    std = standard_rate(country_code, on_date)
    if std is None:
        return None
    return "standard" if abs(rate - std) < 0.001 else "reduced"


def oss_country_code(code):
    """The code the OSS forms use for a member state.

    Greece is ``EL`` on both the EPO code list (``kod2_eu``) and the EU
    schema's ``MSCountryCode_Type``, where Odoo's ``res.country`` says ``GR``.
    Emitting GR fails the SK schema's enumeration and is rejected by EPO.
    """
    return "EL" if code == "GR" else code


#: Source countries whose 5 % tier is not their lowest rate in core's map.
#: Czechia merged its 10 % and 15 % reduced rates into one 12 % rate on
#: 1. 1. 2024; core still lists 10 and 15, so "the lowest reduced rate" picks
#: the abolished 10 %, and a CZ seller's live 12 % tax (food, medicines,
#: accommodation — all 5 % in Slovakia) would stay on 19 %.
_SK_FIVE_EXTRA_SOURCES = {("CZ", 12.0)}


def sk_five_percent_overlay(base_map):
    """The entries core's ``EU_TAX_MAP`` lacks for the Slovak 5 % rate.

    Slovakia has three rates since 1. 1. 2025 (§ 27 zákona č. 222/2004 Z. z.:
    23 %, 19 %, 5 %). Core's map has no key with a Slovak 5 % SOURCE and no
    value of 5.0 for a Slovak DESTINATION, so neither direction is ever mapped:

    * **SK 5 % → another state.** The 5 % band holds what the old 10 % band
      held (books, medicines, basic foodstuffs) plus more. Its counterpart in
      each destination is therefore whatever core already chose for SK 10 %,
      copied rather than restated so that it follows core when core is
      corrected.
    * **Another state → SK 5 %.** Core sends every reduced rate to SK 19 %.
      The 5 % tier is the one the goods typically sold B2C at a reduced rate
      fall into (books, food, medicines), so each source's LOWEST rate that
      core maps to SK 19 % goes to 5 % instead, plus the explicit exceptions
      in ``_SK_FIVE_EXTRA_SOURCES``. A mapping is a PROPOSAL either way —
      core's own description says to check it against what is sold — and it
      is only ever applied to a fiscal position that does not map the tax
      yet, so an accountant's existing choice is never overwritten.
    """
    overlay = {}
    for (src, rate, dest), value in base_map.items():
        if src == "SK" and rate == 10.0 and dest != "SK":
            overlay[("SK", 5.0, dest)] = value
    lowest = {}
    for (src, rate, dest), value in base_map.items():
        if dest == "SK" and src != "SK" and value == 19.0:
            if src not in lowest or rate < lowest[src]:
                lowest[src] = rate
    for src, rate in lowest.items():
        overlay[(src, rate, "SK")] = 5.0
    for src, rate in _SK_FIVE_EXTRA_SOURCES:
        if (src, rate, "SK") in base_map:
            overlay[(src, rate, "SK")] = 5.0
    return overlay
