"""Give the seeded person types an English source name.

They were seeded with the Slovak/Czech name as the en_US value, so an English
user read "Právnická osoba" and the sk/cs catalogue translated it into itself.
The data file now says "Natural person" / "Legal entity", but it is
``noupdate``, so an upgrade does not touch records that already exist: they
are rewritten here.

Only a record whose en_US name is still the old seeded value is rewritten; a
name someone changed is left alone. Slovak and Czech get the native term
(identical in both languages), for the languages that are installed.
"""

import json

#: xmlid name -> (old seeded en_US value, English name, native name)
RENAMES = {
    "sk_person_type_fo": ("Fyzická osoba", "Natural person", "Fyzická osoba"),
    "sk_person_type_po": ("Právnická osoba", "Legal entity", "Právnická osoba"),
}
NATIVE_LANGS = ("sk_SK", "cs_CZ")


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        "SELECT code FROM res_lang WHERE active AND code IN %s", (NATIVE_LANGS,))
    langs = [row[0] for row in cr.fetchall()]
    for xmlid, (old, english, native) in RENAMES.items():
        cr.execute(
            """
            SELECT t.id, t.name FROM cssk_person_type t
              JOIN ir_model_data d
                ON d.model = 'cssk.person.type' AND d.res_id = t.id
             WHERE d.module = 'l10n_sk_statutory' AND d.name = %s
            """,
            (xmlid,),
        )
        row = cr.fetchone()
        if not row or (row[1] or {}).get("en_US") != old:
            continue
        record_id, name = row
        name = dict(name)
        name["en_US"] = english
        for lang in langs:
            if name.get(lang) in (None, old):
                name[lang] = native
        cr.execute(
            "UPDATE cssk_person_type SET name = %s::jsonb WHERE id = %s",
            (json.dumps(name), record_id),
        )
