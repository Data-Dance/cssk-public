"""Give the regional tax offices the code the tax office's form matches.

They were seeded with the full office name ("Daňový úrad Bratislava") as the
``danovyUrad`` string. The form lists the offices by their seat alone, so the
full name matched nothing and the box loaded empty. The data file now carries
the seat, but it is ``noupdate``, so the existing records are rewritten here.

Only a record whose code is still the old seeded value is rewritten; a code
someone changed is left alone.
"""

#: xmlid name -> seat of the office
SEATS = {
    "sk_du_ba": "Bratislava",
    "sk_du_tt": "Trnava",
    "sk_du_tn": "Trenčín",
    "sk_du_nr": "Nitra",
    "sk_du_za": "Žilina",
    "sk_du_bb": "Banská Bystrica",
    "sk_du_po": "Prešov",
    "sk_du_ke": "Košice",
}


def migrate(cr, version):
    if not version:
        return
    for xmlid, seat in SEATS.items():
        cr.execute(
            """
            UPDATE cssk_tax_authority t
               SET submission_code = %s
              FROM ir_model_data d
             WHERE d.model = 'cssk.tax.authority' AND d.res_id = t.id
               AND d.module = 'l10n_sk_statutory' AND d.name = %s
               AND t.submission_code = %s
            """,
            (seat, xmlid, "Daňový úrad " + seat),
        )
