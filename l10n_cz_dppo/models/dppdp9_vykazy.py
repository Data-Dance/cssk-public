# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""DPPDP9 výkazy: which ``l10n_cz_fs`` row feeds which EPO row.

The účetní závěrka travels INSIDE the DPPDP9 písemnost, as repeatable records
of ``c_radku`` + column attributes (see ``data/dppdp9_epo2.xsd``):

=========  =====================================================  ==========================================
Věta       Výkaz (vyhláška 500/2002 Sb., podnikatelé)             Columns
=========  =====================================================  ==========================================
VetaUA     Rozvaha — tabulka aktiv                                kc_brutto, kc_korekce, kc_netto, kc_netto_min
VetaUD     Rozvaha — tabulka pasiv                                kc_sled, kc_min
VetaUB     Výkaz zisku a ztráty — druhové členění                 kc_sled, kc_min
=========  =====================================================  ==========================================

The XSD says nothing about which ``c_radku`` exist: it is a bare 3-digit
decimal, checked by EPO against an application číselník that the Finanční
správa publishes only as a web page ("Informace o číslech řádků pro věty
účetních výkazů"). That číselník is vendored as ``data/uv_radky_500.csv`` —
row number, statutory designation, the rozsahy (P / Z / M) the row belongs
to, and the label — and pinned in ``data/SCHEMA_VERSION``.

**The figures are not mapped here a second time.** Every EPO row names the
``l10n_cz_fs`` Rozvaha / VZZ row with the same statutory designation (B.I.,
C.II., A.V, III., ** …), and the value is that row's computed figure. One
account → row mapping (in ``l10n_cz_fs``), one place to get it wrong.

**Rozsah.** ``l10n_cz_fs`` carries the statement at the depth of the
ZKRÁCENÝ rozsah (vyhláška 500/2002 Sb., příloha č. 1 and 2, § 18 odst. 3
zákona o účetnictví): the Rozvaha by its groups (B.I., C.II., …), not the
numbered lines below them. So the export files ``uv_rozsah = "Z"``, and every
number that the číselník marks for the zkrácený rozsah is below either MAPPED
or listed in :data:`NOT_APPLICABLE` with the reason — the test
``test_every_vykaz_row_is_mapped_or_declared`` enforces it, because an
unmapped row is not an error anywhere else: EPO reads a missing row as zero.
Rows of the plný rozsah only are not filed at all; an entity obliged to file
the plný rozsah (střední a velké ÚJ, or any ÚJ with a statutory audit) cannot
use this export for its závěrka and attaches it as an E-příloha instead.
"""

#: The rozsah this export files (``VetaD/@uv_rozsah``).
RANGE = "Z"

#: ``VetaD/@uv_vyhl`` — vyhláška 500/2002 Sb., podnikatelé.
DECREE = "500"

#: The výkaz tables filed, and which ``cssk.fs.statement`` kind feeds each.
TABLES = {
    "UA": "balance_sheet",
    "UD": "balance_sheet",
    "UB": "profit_loss",
}

#: (věta, c_radku) -> (statutory designation, l10n_cz_fs row codes summed).
#: The designation repeats the číselník's own so the test can prove each
#: pairing, rather than trusting a row number typed from memory.
ROWS = {
    # --- Rozvaha, aktiva (VetaUA) ------------------------------------------
    ("UA", 1): ("", ("AKTIVA",)),
    ("UA", 2): ("A.", ("A_ZK",)),
    ("UA", 3): ("B.", ("B",)),
    ("UA", 4): ("B.I.", ("BI",)),
    ("UA", 14): ("B.II.", ("BII",)),
    ("UA", 27): ("B.III.", ("BIII",)),
    ("UA", 37): ("C.", ("C",)),
    ("UA", 38): ("C.I.", ("CI",)),
    ("UA", 46): ("C.II.", ("CII",)),
    # All of C.II. is krátkodobé: see NOT_APPLICABLE[("UA", 47)].
    ("UA", 57): ("C.II.2.", ("CII",)),
    ("UA", 68): ("C.III.", ("CIII",)),
    ("UA", 71): ("C.IV.", ("CIV",)),
    ("UA", 74): ("D.", ("D_A",)),
    # --- Rozvaha, pasiva (VetaUD) ------------------------------------------
    ("UD", 1): ("", ("PASIVA",)),
    ("UD", 2): ("A.", ("VK",)),
    ("UD", 3): ("A.I.", ("AI",)),
    ("UD", 7): ("A.II.", ("AII",)),
    ("UD", 15): ("A.III.", ("AIII",)),
    ("UD", 18): ("A.IV.", ("AIV",)),
    ("UD", 22): ("A.V", ("AV",)),
    ("UD", 23): ("A.VI.", ("AVI",)),
    ("UD", 24): ("B.+C.", ("BREZ", "CZAV")),
    ("UD", 25): ("B.", ("BREZ",)),
    ("UD", 30): ("C.", ("CZAV",)),
    ("UD", 31): ("C.I.", ("CIP",)),
    ("UD", 46): ("C.II.", ("CIIP",)),
    ("UD", 64): ("D.", ("D_P",)),
    # --- Výkaz zisku a ztráty, druhové členění (VetaUB) --------------------
    ("UB", 1): ("I.", ("I",)),
    ("UB", 2): ("II.", ("II",)),
    ("UB", 3): ("A.", ("A",)),
    ("UB", 7): ("B.", ("Bzm",)),
    ("UB", 8): ("C.", ("Cakt",)),
    ("UB", 9): ("D.", ("D",)),
    ("UB", 14): ("E.", ("E",)),
    ("UB", 20): ("III.", ("III",)),
    ("UB", 24): ("F.", ("F",)),
    ("UB", 30): ("*", ("PROV",)),
    ("UB", 31): ("IV.", ("IV",)),
    ("UB", 34): ("G.", ("G",)),
    ("UB", 38): ("H.", ("Hfin",)),
    ("UB", 39): ("VI.", ("VI",)),
    ("UB", 42): ("I.", ("Ifin",)),
    ("UB", 43): ("J.", ("J",)),
    ("UB", 46): ("VII.", ("VII",)),
    ("UB", 47): ("K.", ("K",)),
    ("UB", 48): ("*", ("FIN",)),
    ("UB", 49): ("**", ("VHB",)),
    ("UB", 50): ("L.", ("L",)),
    ("UB", 53): ("**", ("VHA",)),
    ("UB", 54): ("M.", ("M",)),
    ("UB", 55): ("***", ("VHU",)),
    ("UB", 56): ("*", ("COBR",)),
}

#: Zkrácený-rozsah rows deliberately NOT filed, and why. Each one reads as zero
#: on the filed return, so each needs a reason a reviewer can check.
NOT_APPLICABLE = {
    ("UA", 47): (
        "C.II.1. Dlouhodobé pohledávky: the směrná účtová osnova has no "
        "long-term receivable account, and l10n_cz_fs files every class-3 "
        "receivable under C.II. by the chart convention its README states, "
        "so all of it is C.II.2. krátkodobé. An entity with receivables due "
        "after more than a year must reclassify them — confirm with the "
        "accountant."),
    ("UA", 78): (
        "C.II.3. Časové rozlišení aktiv: the alternative placement of "
        "prepayments inside C.II. l10n_cz_fs presents them as D. Časové "
        "rozlišení aktiv (381, 382, 385), which is filed on row 74; filing "
        "both would count them twice."),
    ("UD", 67): (
        "C.III. Časové rozlišení pasiv: the alternative placement of accruals "
        "inside C. Závazky. l10n_cz_fs presents them as D. Časové rozlišení "
        "pasiv (383, 384), filed on row 64; filing both would count them "
        "twice."),
    ("UB", 35): (
        "V. Výnosy z ostatního dlouhodobého finančního majetku: both IV. and "
        "V. are booked on účet 665 and l10n_cz_fs does not split it, so the "
        "whole of 665 is filed on IV. (row 31). Row 49 and the result are "
        "unaffected; an entity with income from debt instruments held to "
        "maturity must move it to V. by hand."),
}

#: The other výkaz records of the DPPDP9 XSD (every element carrying a
#: ``c_radku``), and why none of them is filed by this export.
NOT_APPLICABLE_TABLES = {
    "UE": "Výkaz zisku a ztráty — účelové členění (500/2002): l10n_cz_fs "
          "builds the druhové členění, and EPO refuses both in one return.",
    "UF": "Rozvaha — aktiva, vyhláška 501/2002 Sb. (banky).",
    "UG": "Rozvaha — podrozvahové položky, vyhláška 501/2002 Sb. (banky).",
    "UH": "Rozvaha — pasiva, vyhláška 501/2002 Sb. (banky).",
    "UI": "Přehled o změnách VK, vyhláška 501/2002 Sb. (banky).",
    "UJ": "Výkaz zisku a ztráty, vyhláška 501/2002 Sb. (banky).",
    "UK": "Rozvaha — aktiva, vyhláška 502/2002 Sb. (pojišťovny).",
    "UL": "Rozvaha — pasiva, vyhláška 502/2002 Sb. (pojišťovny).",
    "UN": "Výkaz zisku a ztráty, vyhláška 502/2002 Sb. (pojišťovny).",
    "UO": "Rozvaha — aktiva, vyhláška 503/2002 Sb. (zdravotní pojišťovny).",
    "UP": "Rozvaha — pasiva, vyhláška 503/2002 Sb. (zdravotní pojišťovny).",
    "UQ": "Výkaz zisku a ztráty, vyhláška 503/2002 Sb. (zdravotní "
          "pojišťovny).",
    "UU": "Přehled o změnách VK, vyhláška 503/2002 Sb. (zdravotní "
          "pojišťovny).",
    "UV": "Přehled o peněžních tocích, vyhláška 503/2002 Sb. (zdravotní "
          "pojišťovny).",
    "UR": "Rozvaha — aktiva, vyhláška 504/2002 Sb. (nepodnikatelské ÚJ).",
    "US": "Rozvaha — pasiva, vyhláška 504/2002 Sb. (nepodnikatelské ÚJ).",
    "UT": "Výkaz zisku a ztráty, vyhláška 504/2002 Sb. (nepodnikatelské ÚJ).",
    "U1": "Přehled o příjmech a výdajích, vyhláška 325/2015 Sb. (jednoduché "
          "účetnictví).",
    "U2": "Přehled o majetku a závazcích, vyhláška 325/2015 Sb. (jednoduché "
          "účetnictví).",
}


def fs_codes(kind):
    """Every l10n_cz_fs row code the export reads from a statement of ``kind``."""
    return {
        code
        for (veta, _row), (_designation, codes) in ROWS.items()
        if TABLES[veta] == kind
        for code in codes
    }
