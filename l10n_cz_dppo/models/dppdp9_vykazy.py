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

**Rozsah.** ``l10n_cz_fs`` carries each statement in both rozsahy of
vyhláška 500/2002 Sb., § 3a — a plný-rozsah version with every item of
přílohy 1 and 2, and a zkrácený-rozsah version by its groups (B.I., C.II., …)
— and the export files the rozsah of the LINKED statements as
``uv_rozsah``: ``"P"`` where both are plný, ``"Z"`` where both are zkrácený.
The attribute covers both výkazy at once, so a mixed pair is refused rather
than filed half in one rozsah and half in the other; the plný-rozsah Rozvaha is
always a permitted choice (§ 3a odst. 1), so the remedy is one recompute.

Every number that the číselník marks for the filed rozsah is below either
MAPPED or listed as not applicable with the reason — the test
``test_every_vykaz_row_is_mapped_or_declared`` enforces it for both rozsahy,
because an unmapped row is not an error anywhere else: EPO reads a missing row
as zero. The mikro rozsah (``"M"``, letters only) is not offered: a mikro
účetní jednotka may file the zkrácený rozsah instead.
"""

#: The rozsahy this export files (``VetaD/@uv_rozsah``).
FULL, ABRIDGED = "P", "Z"
RANGES = (FULL, ABRIDGED)

#: ``VetaD/@uv_vyhl`` — vyhláška 500/2002 Sb., podnikatelé.
DECREE = "500"

#: The výkaz tables filed, and which ``cssk.fs.statement`` kind feeds each.
TABLES = {
    "UA": "balance_sheet",
    "UD": "balance_sheet",
    "UB": "profit_loss",
}

#: (věta, c_radku) -> (statutory designation, l10n_cz_fs row codes summed),
#: for the ZKRÁCENÝ rozsah. The designation repeats the číselník's own so the
#: test can prove each pairing, rather than trusting a row number typed from
#: memory.
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
        "V. are booked on účet 665 and the zkrácený-rozsah VZZ does not split "
        "it, so the whole of 665 is filed on IV. (row 31). Row 49 and the "
        "result are unaffected. The plný-rozsah VZZ does split it, by account "
        "tag: an entity with such income files that one instead."),
}

#: The same for the PLNÝ rozsah: every row of the číselník marked P, filed
#: from the ``l10n_cz_fs`` plný-rozsah row with the same designation. Rows
#: the chart cannot feed (C.II.1.1 dlouhodobé pohledávky z obchodních vztahů,
#: C.I.1.1 vyměnitelné dluhopisy, …) are MANUAL rows there, mapped all the
#: same: zero until an accountant enters a figure, filed when they do.
ROWS_FULL = {
    ('UA', 1): ('', ('AKTIVA',)),
    ('UA', 2): ('A.', ('A_ZK',)),
    ('UA', 3): ('B.', ('B',)),
    ('UA', 4): ('B.I.', ('BI',)),
    ('UA', 5): ('B.I.1.', ('BI1',)),
    ('UA', 6): ('B.I.2.', ('BI2',)),
    ('UA', 7): ('B.I.2.1.', ('BI2_1',)),
    ('UA', 8): ('B.I.2.2.', ('BI2_2',)),
    ('UA', 9): ('B.I.3.', ('BI3',)),
    ('UA', 10): ('B.I.4', ('BI4',)),
    ('UA', 11): ('B.I.5.', ('BI5',)),
    ('UA', 12): ('B.I.5.1.', ('BI5_1',)),
    ('UA', 13): ('B.I.5.2.', ('BI5_2',)),
    ('UA', 14): ('B.II.', ('BII',)),
    ('UA', 15): ('B.II.1.', ('BII1',)),
    ('UA', 16): ('B.II.1.1.', ('BII1_1',)),
    ('UA', 17): ('B.II.1.2.', ('BII1_2',)),
    ('UA', 18): ('B.II.2.', ('BII2',)),
    ('UA', 19): ('B.II.3.', ('BII3',)),
    ('UA', 20): ('B.II.4.', ('BII4',)),
    ('UA', 21): ('B.II.4.1.', ('BII4_1',)),
    ('UA', 22): ('B.II.4.2.', ('BII4_2',)),
    ('UA', 23): ('B.II.4.3.', ('BII4_3',)),
    ('UA', 24): ('B.II.5.', ('BII5',)),
    ('UA', 25): ('B.II.5.1', ('BII5_1',)),
    ('UA', 26): ('B.II.5.2.', ('BII5_2',)),
    ('UA', 27): ('B.III.', ('BIII',)),
    ('UA', 28): ('B.III.1.', ('BIII1',)),
    ('UA', 29): ('B.III.2.', ('BIII2',)),
    ('UA', 30): ('B.III.3', ('BIII3',)),
    ('UA', 31): ('B.III.4.', ('BIII4',)),
    ('UA', 32): ('B.III.5.', ('BIII5',)),
    ('UA', 33): ('B.III.6.', ('BIII6',)),
    ('UA', 34): ('B.III.7.', ('BIII7',)),
    ('UA', 35): ('B.III.7.1.', ('BIII7_1',)),
    ('UA', 36): ('B.III.7.2.', ('BIII7_2',)),
    ('UA', 37): ('C.', ('C',)),
    ('UA', 38): ('C.I.', ('CI',)),
    ('UA', 39): ('C.I.1.', ('CI1',)),
    ('UA', 40): ('C.I.2.', ('CI2',)),
    ('UA', 41): ('C.I.3', ('CI3',)),
    ('UA', 42): ('C.I.3.1.', ('CI3_1',)),
    ('UA', 43): ('C.I.3.2.', ('CI3_2',)),
    ('UA', 44): ('C.I.4.', ('CI4',)),
    ('UA', 45): ('C.I.5.', ('CI5',)),
    ('UA', 46): ('C.II.', ('CII',)),
    ('UA', 47): ('C.II.1.', ('CII1',)),
    ('UA', 48): ('C.II.1.1.', ('CII1_1',)),
    ('UA', 49): ('C.II.1.2.', ('CII1_2',)),
    ('UA', 50): ('C.II.1.3.', ('CII1_3',)),
    ('UA', 51): ('C.II.1.4.', ('CII1_4',)),
    ('UA', 52): ('C.II.1.5.', ('CII1_5',)),
    ('UA', 53): ('C.II.1.5.1.', ('CII1_5_1',)),
    ('UA', 54): ('C.II.1.5.2.', ('CII1_5_2',)),
    ('UA', 55): ('C.II.1.5.3.', ('CII1_5_3',)),
    ('UA', 56): ('C.II.1.5.4.', ('CII1_5_4',)),
    ('UA', 57): ('C.II.2.', ('CII2',)),
    ('UA', 58): ('C.II.2.1.', ('CII2_1',)),
    ('UA', 59): ('C.II.2.2.', ('CII2_2',)),
    ('UA', 60): ('C.II.2.3.', ('CII2_3',)),
    ('UA', 61): ('C.II.2.4.', ('CII2_4',)),
    ('UA', 62): ('C.II.2.4.1.', ('CII2_4_1',)),
    ('UA', 63): ('C.II.2.4.2.', ('CII2_4_2',)),
    ('UA', 64): ('C.II.2.4.3.', ('CII2_4_3',)),
    ('UA', 65): ('C.II.2.4.4.', ('CII2_4_4',)),
    ('UA', 66): ('C.II.2.4.5.', ('CII2_4_5',)),
    ('UA', 67): ('C.II.2.4.6.', ('CII2_4_6',)),
    ('UA', 68): ('C.III.', ('CIII',)),
    ('UA', 69): ('C.III.1.', ('CIII1',)),
    ('UA', 70): ('C.III.2.', ('CIII2',)),
    ('UA', 71): ('C.IV.', ('CIV',)),
    ('UA', 72): ('C.IV.1.', ('CIV1',)),
    ('UA', 73): ('C.IV.2.', ('CIV2',)),
    ('UA', 74): ('D.', ('D_A',)),
    ('UA', 75): ('D.1.', ('D1_A',)),
    ('UA', 76): ('D.2.', ('D2_A',)),
    ('UA', 77): ('D.3.', ('D3_A',)),
    ('UB', 1): ('I.', ('I',)),
    ('UB', 2): ('II.', ('II',)),
    ('UB', 3): ('A.', ('A',)),
    ('UB', 4): ('A.1', ('A1',)),
    ('UB', 5): ('A.2', ('A2',)),
    ('UB', 6): ('A.3', ('A3',)),
    ('UB', 7): ('B.', ('Bzm',)),
    ('UB', 8): ('C.', ('Cakt',)),
    ('UB', 9): ('D.', ('D',)),
    ('UB', 10): ('D.1.', ('D1',)),
    ('UB', 11): ('D.2', ('D2',)),
    ('UB', 12): ('D.2.1.', ('D2_1',)),
    ('UB', 13): ('D.2.2.', ('D2_2',)),
    ('UB', 14): ('E.', ('E',)),
    ('UB', 15): ('E.1.', ('E1',)),
    ('UB', 16): ('E.1.1.', ('E1_1',)),
    ('UB', 17): ('E.1.2.', ('E1_2',)),
    ('UB', 18): ('E.2.', ('E2',)),
    ('UB', 19): ('E.3.', ('E3',)),
    ('UB', 20): ('III.', ('III',)),
    ('UB', 21): ('III.1.', ('III1',)),
    ('UB', 22): ('III.2.', ('III2',)),
    ('UB', 23): ('III.3.', ('III3',)),
    ('UB', 24): ('F.', ('F',)),
    ('UB', 25): ('F.1.', ('F1',)),
    ('UB', 26): ('F.2.', ('F2',)),
    ('UB', 27): ('F.3.', ('F3',)),
    ('UB', 28): ('F.4.', ('F4',)),
    ('UB', 29): ('F.5.', ('F5',)),
    ('UB', 30): ('*', ('PROV',)),
    ('UB', 31): ('IV.', ('IV',)),
    ('UB', 32): ('IV.1.', ('IV1',)),
    ('UB', 33): ('IV.2.', ('IV2',)),
    ('UB', 34): ('G.', ('G',)),
    ('UB', 35): ('V.', ('V',)),
    ('UB', 36): ('V.1.', ('V1',)),
    ('UB', 37): ('V.2.', ('V2',)),
    ('UB', 38): ('H.', ('Hfin',)),
    ('UB', 39): ('VI.', ('VI',)),
    ('UB', 40): ('VI.1.', ('VI1',)),
    ('UB', 41): ('VI.2.', ('VI2',)),
    ('UB', 42): ('I.', ('Ifin',)),
    ('UB', 43): ('J.', ('J',)),
    ('UB', 44): ('J.1.', ('J1',)),
    ('UB', 45): ('J.2.', ('J2',)),
    ('UB', 46): ('VII.', ('VII',)),
    ('UB', 47): ('K.', ('K',)),
    ('UB', 48): ('*', ('FIN',)),
    ('UB', 49): ('**', ('VHB',)),
    ('UB', 50): ('L.', ('L',)),
    ('UB', 51): ('L.1.', ('L1',)),
    ('UB', 52): ('L.2.', ('L2',)),
    ('UB', 53): ('**', ('VHA',)),
    ('UB', 54): ('M.', ('M',)),
    ('UB', 55): ('***', ('VHU',)),
    ('UB', 56): ('*', ('COBR',)),
    ('UD', 1): ('', ('PASIVA',)),
    ('UD', 2): ('A.', ('VK',)),
    ('UD', 3): ('A.I.', ('AI',)),
    ('UD', 4): ('A.I.1.', ('AI1',)),
    ('UD', 5): ('A.I.2.', ('AI2',)),
    ('UD', 6): ('A.I.3.', ('AI3',)),
    ('UD', 7): ('A.II.', ('AII',)),
    ('UD', 8): ('A.II.1.', ('AII1',)),
    ('UD', 9): ('A.II.2.', ('AII2',)),
    ('UD', 10): ('A.II.2.1.', ('AII2_1',)),
    ('UD', 11): ('A.II.2.2.', ('AII2_2',)),
    ('UD', 12): ('A.II.2.3.', ('AII2_3',)),
    ('UD', 13): ('A.II.2.4.', ('AII2_4',)),
    ('UD', 14): ('A.II.2.5.', ('AII2_5',)),
    ('UD', 15): ('A.III.', ('AIII',)),
    ('UD', 16): ('A.III.1.', ('AIII1',)),
    ('UD', 17): ('A.III.2.', ('AIII2',)),
    ('UD', 18): ('A.IV.', ('AIV',)),
    ('UD', 19): ('A.IV.1.', ('AIV1',)),
    ('UD', 21): ('A.IV.2.', ('AIV2',)),
    ('UD', 22): ('A.V', ('AV',)),
    ('UD', 23): ('A.VI.', ('AVI',)),
    ('UD', 24): ('B.+C.', ('BC',)),
    ('UD', 25): ('B.', ('BREZ',)),
    ('UD', 26): ('B.1.', ('BREZ1',)),
    ('UD', 27): ('B.2.', ('BREZ2',)),
    ('UD', 28): ('B.3.', ('BREZ3',)),
    ('UD', 29): ('B.4.', ('BREZ4',)),
    ('UD', 30): ('C.', ('CZAV',)),
    ('UD', 31): ('C.I.', ('CIP',)),
    ('UD', 32): ('C.I.1.', ('CIP1',)),
    ('UD', 33): ('C.I.1.1.', ('CIP1_1',)),
    ('UD', 34): ('C.I.1.2.', ('CIP1_2',)),
    ('UD', 35): ('C.I.2.', ('CIP2',)),
    ('UD', 36): ('C.I.3.', ('CIP3',)),
    ('UD', 37): ('C.I.4.', ('CIP4',)),
    ('UD', 38): ('C.I.5.', ('CIP5',)),
    ('UD', 39): ('C.I.6.', ('CIP6',)),
    ('UD', 40): ('C.I.7.', ('CIP7',)),
    ('UD', 41): ('C.I.8.', ('CIP8',)),
    ('UD', 42): ('C.I.9.', ('CIP9',)),
    ('UD', 43): ('C.I.9.1.', ('CIP9_1',)),
    ('UD', 44): ('C.I.9.2.', ('CIP9_2',)),
    ('UD', 45): ('C.I.9.3.', ('CIP9_3',)),
    ('UD', 46): ('C.II.', ('CIIP',)),
    ('UD', 47): ('C.II.1.', ('CIIP1',)),
    ('UD', 48): ('C.II.1.1.', ('CIIP1_1',)),
    ('UD', 49): ('C.II.1.2.', ('CIIP1_2',)),
    ('UD', 50): ('C.II.2.', ('CIIP2',)),
    ('UD', 51): ('C.II.3.', ('CIIP3',)),
    ('UD', 52): ('C.II.4.', ('CIIP4',)),
    ('UD', 53): ('C.II.5.', ('CIIP5',)),
    ('UD', 54): ('C.II.6.', ('CIIP6',)),
    ('UD', 55): ('C.II.7.', ('CIIP7',)),
    ('UD', 56): ('C.II.8.', ('CIIP8',)),
    ('UD', 57): ('C.II.8.1.', ('CIIP8_1',)),
    ('UD', 58): ('C.II.8.2.', ('CIIP8_2',)),
    ('UD', 59): ('C.II.8.3.', ('CIIP8_3',)),
    ('UD', 60): ('C.II.8.4.', ('CIIP8_4',)),
    ('UD', 61): ('C.II.8.5.', ('CIIP8_5',)),
    ('UD', 62): ('C.II.8.6.', ('CIIP8_6',)),
    ('UD', 63): ('C.II.8.7.', ('CIIP8_7',)),
    ('UD', 64): ('D.', ('D_P',)),
    ('UD', 65): ('D.1.', ('D1_P',)),
    ('UD', 66): ('D.2.', ('D2_P',)),
}

#: Plný-rozsah rows deliberately NOT filed, and why.
NOT_APPLICABLE_FULL = {
    key: (
        "%s: the alternative placement of časové rozlišení (vyhláška "
        "500/2002 Sb., § 3 odst. 3 and 4 — the rozvaha carries either this "
        "item or D., never both). l10n_cz_fs presents časové rozlišení as D. "
        "(rows 74-77 of the aktiva, 64-66 of the pasiva); filing both would "
        "count it twice." % label)
    for key, label in (
        (("UA", 78), "C.II.3. Časové rozlišení aktiv"),
        (("UA", 79), "C.II.3.1. Náklady příštích období"),
        (("UA", 80), "C.II.3.2. Komplexní náklady příštích období"),
        (("UA", 81), "C.II.3.3. Příjmy příštích období"),
        (("UD", 67), "C.III. Časové rozlišení pasiv"),
        (("UD", 68), "C.III.1. Výdaje příštích období"),
        (("UD", 69), "C.III.2. Výnosy příštích období"),
    )
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


def rows(rng):
    """The row map of rozsah ``rng`` (``"P"`` or ``"Z"``)."""
    return ROWS_FULL if rng == FULL else ROWS


def not_applicable(rng):
    """The declared not-applicable rows of rozsah ``rng``."""
    return NOT_APPLICABLE_FULL if rng == FULL else NOT_APPLICABLE


def fs_codes(kind, rng=ABRIDGED):
    """Every l10n_cz_fs row code the export reads from a statement of
    ``kind`` when filing rozsah ``rng``."""
    return {
        code
        for (veta, _row), (_designation, codes) in rows(rng).items()
        if TABLES[veta] == kind
        for code in codes
    }
