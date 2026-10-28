# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Name the existing Rozvaha and VZZ versions for what they are: zkrácený.

This release adds the plný rozsah as two new versions beside the existing
ones, valid for the same period. The existing two live in a
``noupdate="1"`` file, so an upgrade would leave them without a rozsah and
under names ("Rozvaha 2025") that no longer say which of the two a user is
picking — and the DPPDP9 export reads the rozsah to decide what it files.

The rozsah is set only where it is still empty, and a name only where it is
still exactly what this module shipped, so an administrator's own edit stays.
The new plný-rozsah versions are created by the upgrade itself: a
``noupdate`` file still creates records it has not created before.
"""

VERSIONS = {
    "rozvaha_version_2025": (
        "Rozvaha 2025", "Rozvaha 2025 (zkrácený rozsah)"),
    "vysledovka_version_2025": (
        "Výkaz zisku a ztráty 2025",
        "Výkaz zisku a ztráty 2025 (zkrácený rozsah)"),
}


def migrate(cr, version):
    if not version:
        return
    for xmlid, (old_name, new_name) in VERSIONS.items():
        cr.execute(
            """
            UPDATE cssk_fs_statement_version v
               SET l10n_cz_fs_scope = 'abridged'
              FROM ir_model_data d
             WHERE d.model = 'cssk.fs.statement.version'
               AND d.module = 'l10n_cz_fs'
               AND d.name = %s
               AND d.res_id = v.id
               AND v.l10n_cz_fs_scope IS NULL
            """,
            (xmlid,),
        )
        cr.execute(
            """
            UPDATE cssk_fs_statement_version v
               SET name = %s
              FROM ir_model_data d
             WHERE d.model = 'cssk.fs.statement.version'
               AND d.module = 'l10n_cz_fs'
               AND d.name = %s
               AND d.res_id = v.id
               AND v.name = %s
            """,
            (new_name, xmlid, old_name),
        )
