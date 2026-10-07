# -*- coding: utf-8 -*-
"""UZPODv14 kontrolné pravidlá (business rules beyond the XSD).

Source of truth: Opatrenie MF SR č. MF/23377/2014-74 (a nadv.), prílohy —
Súvaha Úč POD 1-01 a Výkaz ziskov a strát Úč POD 2-01, kde každý medzisúčtový
riadok je definovaný ako súčet uvedených riadkov; the per-row súčty below are
the official cross-line totals.

SUCET_BS / SUCET_PL: ``(parent_row, [component_rows])`` — parent NETTO must
equal the sum of the component NETTO values (Súvaha AKTÍVA netto = s3,
PASÍVA netto = s5; VZS = s1). Plus two cross-statement / per-row invariants
checked in code: AKTÍVA (r001) = PASÍVA (r079); netto = brutto − korekcia."""

SUCET_BS = [  # Súvaha: (parent_r, [component_r]) — official medzisúčty
    (1, [2, 33, 74]),
    (2, [3, 11, 21]),
    (3, [4, 5, 6, 7, 8, 9, 10]),
    (11, [12, 13, 14, 15, 16, 17, 18, 19, 20]),
    (21, [22, 23, 24, 25, 26, 27, 28, 29, 30, 31, 32]),
    (33, [34, 41, 53, 66, 71]),
    (34, [35, 36, 37, 38, 39, 40]),
    (41, [42, 46, 47, 48, 49, 50, 51, 52]),
    (42, [43, 44, 45]),
    (53, [54, 58, 59, 60, 61, 62, 63, 64, 65]),
    (54, [55, 56, 57]),
    (66, [67, 68, 69, 70]),
    (71, [72, 73]),
    (74, [75, 76, 77, 78]),
    (79, [80, 101, 141]),
    (80, [81, 85, 86, 87, 90, 93, 97, 100]),
    (81, [82, 83, 84]),
    (87, [88, 89]),
    (90, [91, 92]),
    (93, [94, 95, 96]),
    (97, [98, 99]),
    (101, [102, 118, 121, 122, 136, 139, 140]),
    (102, [103, 107, 108, 109, 110, 111, 112, 113, 114, 115, 116, 117]),
    (103, [104, 105, 106]),
    (118, [119, 120]),
    (122, [123, 127, 128, 129, 130, 131, 132, 133, 134, 135]),
    (123, [124, 125, 126]),
    (136, [137, 138]),
    (141, [142, 143, 144, 145]),
]

SUCET_PL = [  # Výkaz ziskov a strát: (parent_r, [component_r])
    (2, [3, 4, 5, 6, 7, 8, 9]),
    (10, [11, 12, 13, 14, 15, 20, 21, 24, 25, 26]),
    (15, [16, 17, 18, 19]),
    (21, [22, 23]),
    (29, [30, 31, 35, 39, 42, 43, 44]),
    (31, [32, 33, 34]),  # IX = IX.1 prepojené + IX.2 podiel. + IX.3 ostatné
    (35, [36, 37, 38]),  # X  = X.1 + X.2 + X.3
    (39, [40, 41]),      # XI = XI.1 prepojené + XI.2 ostatné
    (45, [46, 47, 48, 49, 52, 53, 54]),
    (49, [50, 51]),      # N  = N.1 prepojené + N.2 ostatné
    (57, [58, 59]),
]
