# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Split the Rozvaha aktiva rows into brutto and korekce on existing databases.

The DPPDP9 return files the Rozvaha as VetaUA with ``kc_brutto`` /
``kc_korekce`` / ``kc_netto`` per row, and a row whose oprávky and opravné
položky are netted into one formula cannot be split back into those columns.
The line definitions now carry the correction accounts in
``account_formula_correction``; netto is unchanged by that.

Those definitions live in a ``noupdate="1"`` file, so an upgrade would not
rewrite them: an existing database would keep the old, netted rows and the
DPPDP9 export would file brutto = netto and korekce = 0 without a word.

Each row is rewritten only where it still holds EXACTLY the formula this module
shipped and no correction formula, so an accountant's own edit is left alone.
The one figure that moves is 094 (OP k nedokončenému DHM), from B.I. to B.II.
"""

# code: (formula as shipped before, gross formula, correction formula)
SPLITS = {
    "BI": (
        "012,013,014,015,016,017,019,040,041,050,051,072,073,074,075,079,091,093,094",
        "012,013,014,015,016,017,019,040,041,050,051",
        "072,073,074,075,079,091,093"),
    "BII": (
        "021,022,025,026,027,029,031,032,042,052,081,082,085,086,089,092,095,097,098",
        "021,022,025,026,027,029,031,032,042,052,097",
        "081,082,085,086,089,092,094,095,098"),
    "BIII": (
        "061,062,063,065,066,067,068,069,043,053,096",
        "061,062,063,065,066,067,068,069,043,053",
        "096"),
    "CI": (
        "1",
        "10,11,12,13,14,15,16,17,18",
        "19"),
    "CII": (
        "311,312,313,314,315,335,343001,343112,343115,343121,351,352,354,355,"
        "358,371,373,374,375,376,378,388,391,395",
        "311,312,313,314,315,335,343001,343112,343115,343121,351,352,354,355,"
        "358,371,373,374,375,376,378,388,395",
        "391"),
    "CIII": (
        "251,253,254,256,257,258,259,291",
        "251,253,254,256,257,258,259",
        "291"),
}


def migrate(cr, version):
    if not version:
        return
    for code, (old, gross, correction) in SPLITS.items():
        cr.execute(
            """
            UPDATE cssk_fs_statement_line_def l
               SET account_formula = %s,
                   account_formula_correction = %s
              FROM ir_model_data d
             WHERE d.model = 'cssk.fs.statement.version'
               AND d.module = 'l10n_cz_fs'
               AND d.name = 'rozvaha_version_2025'
               AND l.version_id = d.res_id
               AND l.code = %s
               AND l.account_formula = %s
               AND COALESCE(l.account_formula_correction, '') = ''
            """,
            (gross, correction, code, old),
        )
