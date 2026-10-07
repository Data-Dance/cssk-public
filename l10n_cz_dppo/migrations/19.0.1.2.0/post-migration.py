# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""E is "dodatečné-opravné", not "dodatečné".

The DPPDP9 filing type exporting ``dapdpp_forma="E"`` was labelled plain
"Dodatečné", and D did not exist. The data file creates D; the existing E
record is ``noupdate``, so its label is corrected here. Returns already
exported are not touched.
"""


def migrate(cr, version):
    cr.execute("""
        UPDATE cssk_income_tax_type t
           SET name = 'Dodatečné-opravné'
          FROM ir_model_data d
         WHERE d.model = 'cssk.income.tax.type'
           AND d.module = 'l10n_cz_dppo' AND d.name = 'cz_dppo_type_E'
           AND d.res_id = t.id
    """)
