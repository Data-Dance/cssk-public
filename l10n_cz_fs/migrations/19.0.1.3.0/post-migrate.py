# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""661 moves to IV., 564 to K. of the Výkaz zisku a ztráty, on existing databases.

661 Tržby z prodeje cenných papírů a podílů was reported under VII. Ostatní
finanční výnosy, while its cost, 561, sits in G. Náklady vynaložené na prodané
podíly; IV. is the income side of G. 564 Náklady z přecenění cenných papírů was
in I. Úpravy hodnot a rezervy ve finanční oblasti, whereas its income
counterpart 664 sits in VII., so the cost belongs in K. Both placements are
those of the accountant's practice.

The line definitions live in a ``noupdate="1"`` file, so an upgrade would not
rewrite them. A move touches two or three rows (out of one, into another), and
it is made only when EVERY one of them still holds exactly the formula this
module shipped: rewriting some of them would count the account twice or drop
it. Where an accountant has edited any of them, the move is skipped with a
warning and their rows are left alone. The tag name is likewise renamed only
in the languages that still hold the shipped text.
"""

import logging

_logger = logging.getLogger(__name__)

_VII = ("-660,-661,-663,-664,-667,-668,-669,-698",
        "-660,-663,-664,-667,-668,-669,-698")
_IFIN = ("564,574,579", "574,579")
_K = ("560,563,565,567,568,569,598", "560,563,564,565,567,568,569,598")

# (version xmlid, account moved, {row code: (formula as shipped, new formula)})
MOVES = (
    ("vysledovka_full_version_2025", "661", {
        "IV1": ("-665&IV_1", "-661&IV_1,-665&IV_1"),
        "IV2": ("-665!IV_1!V_1!V_2", "-661!IV_1,-665!IV_1!V_1!V_2"),
        "VII": _VII,
    }),
    ("vysledovka_full_version_2025", "564", {"Ifin": _IFIN, "K": _K}),
    ("vysledovka_version_2025", "661", {
        "IV": ("-665", "-661,-665"),
        "VII": _VII,
    }),
    ("vysledovka_version_2025", "564", {"Ifin": _IFIN, "K": _K}),
)

TAG_NAME = (
    "VZZ IV.1 — výnosy z podílů, ovládaná nebo ovládající osoba (665)",
    "VZZ IV.1 — výnosy z podílů, ovládaná nebo ovládající osoba (661, 665)",
)


def _version_id(cr, xmlid):
    cr.execute(
        """
        SELECT res_id FROM ir_model_data
         WHERE model = 'cssk.fs.statement.version'
           AND module = 'l10n_cz_fs' AND name = %s
        """,
        (xmlid,),
    )
    row = cr.fetchone()
    return row and row[0]


def migrate(cr, version):
    if not version:
        return
    for xmlid, account, rows in MOVES:
        version_id = _version_id(cr, xmlid)
        if not version_id:
            continue
        cr.execute(
            """
            SELECT code, account_formula FROM cssk_fs_statement_line_def
             WHERE version_id = %s AND code IN %s
            """,
            (version_id, tuple(rows)),
        )
        current = dict(cr.fetchall())
        edited = sorted(code for code, (old, _new) in rows.items()
                        if current.get(code) != old)
        if edited:
            _logger.warning(
                "l10n_cz_fs: %s not moved in %s, because row(s) %s no longer "
                "hold the shipped formula; check where the account is "
                "reported.", account, xmlid, ", ".join(edited))
            continue
        for code, (old, new) in rows.items():
            cr.execute(
                """
                UPDATE cssk_fs_statement_line_def
                   SET account_formula = %s
                 WHERE version_id = %s AND code = %s AND account_formula = %s
                """,
                (new, version_id, code, old),
            )
    old_name, new_name = TAG_NAME
    cr.execute(
        """
        UPDATE account_account_tag t
           SET name = (
               SELECT jsonb_object_agg(
                          key,
                          CASE WHEN value = to_jsonb(%s::text)
                               THEN to_jsonb(%s::text) ELSE value END)
                 FROM jsonb_each(t.name))
          FROM ir_model_data d
         WHERE d.model = 'account.account.tag'
           AND d.module = 'l10n_cz_fs'
           AND d.name = 'account_tag_vzz_IV_1'
           AND d.res_id = t.id
           AND t.name->>'en_US' = %s
        """,
        (old_name, new_name, old_name),
    )
