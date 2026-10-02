# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""E is "dodatečné/opravné", not "dodatečné".

The DPHDP3 filing type exporting ``dapdph_forma="E"`` was labelled plain
"Dodatečné", and D — the plain dodatečné — did not exist. The data file creates
D; the existing E record is ``noupdate``, so its label is corrected here.

Returns already exported with E are NOT changed: E is what was filed.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE cssk_vat_return_type t
           SET name = 'Dodatečné/opravné'
          FROM ir_model_data d
         WHERE d.model = 'cssk.vat.return.type'
           AND d.module = 'l10n_cz_vat_return' AND d.name = 'dphdp3_type_E'
           AND d.res_id = t.id
    """)
