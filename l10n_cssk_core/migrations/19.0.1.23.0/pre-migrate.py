# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Re-home the seeded person types from the country modules to the core.

``SK-FO`` / ``SK-PO`` were data of ``l10n_sk_statutory`` and ``CZ-FO`` /
``CZ-PO`` of ``l10n_cz_statutory``. They are core data from this version on,
so that a database without one country's statutory module still has that
country's types for its partners.

The records are ``noupdate`` and the code is unique per country, so loading
the core's data file over a database that already holds them under the old
module name would try to create them a second time and fail on the
constraint. Moving the external ids first makes the load find them instead.

A type somebody created by hand with the same code (possible where the
country module was never installed) is adopted the same way, for the same
reason.
"""

#: xmlid name -> (former module, country code, code)
SEEDED = {
    "sk_person_type_fo": ("l10n_sk_statutory", "SK", "SK-FO"),
    "sk_person_type_po": ("l10n_sk_statutory", "SK", "SK-PO"),
    "cz_person_type_fo": ("l10n_cz_statutory", "CZ", "CZ-FO"),
    "cz_person_type_po": ("l10n_cz_statutory", "CZ", "CZ-PO"),
}


def migrate(cr, version):
    if not version:
        return
    for name, (former, country_code, code) in SEEDED.items():
        cr.execute(
            """
            SELECT 1 FROM ir_model_data
             WHERE module = 'l10n_cssk_core' AND name = %s
            """,
            (name,),
        )
        if cr.fetchone():
            continue
        cr.execute(
            """
            UPDATE ir_model_data
               SET module = 'l10n_cssk_core'
             WHERE module = %s AND name = %s AND model = 'cssk.person.type'
            """,
            (former, name),
        )
        if cr.rowcount:
            continue
        cr.execute(
            "SELECT id FROM cssk_person_type WHERE country_code = %s AND code = %s",
            (country_code, code),
        )
        row = cr.fetchone()
        if not row:
            continue
        cr.execute(
            """
            INSERT INTO ir_model_data (module, name, model, res_id, noupdate)
            VALUES ('l10n_cssk_core', %s, 'cssk.person.type', %s, true)
            """,
            (name, row[0]),
        )
