# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""E is "následné/opravné", not "následné".

The KH filing type exporting ``khdph_forma="E"`` was labelled plain
"Následné", and N — the plain následné — did not exist. The data file creates
N; the existing E record is ``noupdate``, so its label is corrected here.

Statements already exported with E are NOT changed: E is what was filed, and
whether a filing meant N instead is a question for whoever filed it.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE cssk_control_statement_type t
           SET name = 'Následné/opravné'
          FROM ir_model_data d
         WHERE d.model = 'cssk.control.statement.type'
           AND d.module = 'l10n_cz_kh' AND d.name = 'cz_kh_type_E'
           AND d.res_id = t.id
    """)
