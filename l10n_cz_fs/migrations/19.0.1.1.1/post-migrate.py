# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""A.V of the Rozvaha reads the period's result, on existing databases.

A.V. Výsledek hospodaření běžného účetního období read the cumulative balance
of classes 5 and 6 since the first entry, so in a database holding more than
one year without a closing every earlier year's result landed in A.V. The row
now reads the movement within the period (``basis = 'movement'``).

The line definitions live in a ``noupdate="1"`` file, so an upgrade would not
rewrite them. The row is changed only where it still holds exactly what this
module shipped, so an accountant's own edit is left alone.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE cssk_fs_statement_line_def l
           SET basis = 'movement'
          FROM ir_model_data d
         WHERE d.model = 'cssk.fs.statement.version'
           AND d.module = 'l10n_cz_fs'
           AND d.name = 'rozvaha_version_2025'
           AND l.version_id = d.res_id
           AND l.code = 'AV'
           AND l.account_formula = '-5,-6'
           AND COALESCE(l.basis, 'version') = 'version'
        """
    )
