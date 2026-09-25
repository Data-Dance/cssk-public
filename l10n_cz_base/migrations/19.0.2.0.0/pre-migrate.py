# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Merge the legacy symbol values into the canonical l10n_cssk_* columns
before the fields become stored related aliases (whose recompute would
otherwise overwrite manually-set legacy values with the canonical ones)."""


def _column_exists(cr, table, column):
    cr.execute(
        """
        SELECT 1 FROM information_schema.columns
         WHERE table_name = %s AND column_name = %s
        """,
        (table, column),
    )
    return bool(cr.fetchone())


def migrate(cr, version):
    for legacy, canonical in (
        ("variable_symbol", "l10n_cssk_variable_symbol"),
        ("constant_symbol", "l10n_cssk_constant_symbol"),
        ("specific_symbol", "l10n_cssk_specific_symbol"),
    ):
        if not _column_exists(cr, "account_move", legacy):
            continue
        if not _column_exists(cr, "account_move", canonical):
            # canonical module not yet initialised on this DB; create the
            # column so the values survive until its regular install
            cr.execute(
                'ALTER TABLE account_move ADD COLUMN "%s" varchar' % canonical
            )
        cr.execute(
            """
            UPDATE account_move
               SET "{canonical}" = "{legacy}"
             WHERE COALESCE("{legacy}", '') != ''
               AND COALESCE("{canonical}", '') = ''
            """.format(canonical=canonical, legacy=legacy)
        )
