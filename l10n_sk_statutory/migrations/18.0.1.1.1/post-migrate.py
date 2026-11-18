"""Give the office for selected taxpayers the code the form's list contains.

The record was seeded with "Daňový úrad pre vybrané daňové subjekty"; the tax
office's form lists the office as "Úrad pre vybrané hospodárske subjekty" and
matches the exported ``danovyUrad`` against that list. The data is
``noupdate``, so the existing record is rewritten here, and only while its
code is still the seeded value.
"""


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        UPDATE cssk_tax_authority t
           SET submission_code = %s
          FROM ir_model_data d
         WHERE d.model = 'cssk.tax.authority' AND d.res_id = t.id
           AND d.module = 'l10n_sk_statutory' AND d.name = 'sk_du_vds'
           AND t.submission_code = %s
        """,
        ("Úrad pre vybrané hospodárske subjekty",
         "Daňový úrad pre vybrané daňové subjekty"),
    )
