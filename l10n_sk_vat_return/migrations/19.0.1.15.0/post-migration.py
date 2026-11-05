# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Row names most specific first, and without the code.

19.0.1.14.2 named every row "code — section, rate — column", which the Lines
list cuts at its end: r01, r02, r01a, r02a, r03 and r04 all read "Dodanie
tovaru a služby podľa § 8 a 9 zákona a daň…", base and tax, every rate. 1.15.0
names them column — rate — section, verbatim from each vzor's eForm, and leaves
the row number to the Code column.

Same rules as 1.14.2: the new name is read from the data files
(``row_names.shipped_row_names``); a definition is renamed only while it holds
a name this module shipped — its code, a pre-1.14.2 short name, or the 1.14.2
name, frozen in ``names_19.0.1.14.2.json`` next to this file — and a return line
only while it holds such a name, so nothing a user edited is touched.
"""
import json
import logging
import os

_logger = logging.getLogger(__name__)

#: Short names shipped before 19.0.1.14.2 for the rows that had one.
PRE_1_14_2 = (
    "r17 — Daň celkom",
    "r24 — Rozdiel základu (§25)",
    "r25 — Rozdiel dane (§25)",
    "r26 — Rozdiel základu (§25a)",
    "r27 — Rozdiel dane (§25a)",
    "r28 — Oprava odpočítanej dane (§53)",
    "r29 — Oprava odpočítanej dane (§53b)",
    "r30 — Odpočet pri registrácii",
    "r31 — Vrátenie dane cestujúcim",
    "r32 — Vlastná daňová povinnosť",
    "r33 — Nadmerný odpočet (§79/2)",
    "r34 — Nadmerný odpočet odpočítaný",
    "r35 — Vlastná daň na úhradu",
    "r36 — Rozdiel oproti poslednej známej dani",
    "r37 — Daň na úhradu (+/-)",
)


def previous_names():
    """``{version xmlid: {code: name}}`` as 19.0.1.14.2 shipped them."""
    path = os.path.join(os.path.dirname(__file__), "names_19.0.1.14.2.json")
    with open(path, encoding="utf-8") as fh:
        return json.load(fh)


def migrate(cr, version):
    if not version:
        return
    from odoo.addons.l10n_sk_vat_return.row_names import shipped_row_names

    previous = previous_names()
    defs_renamed = lines_renamed = 0
    for xmlid, names in shipped_row_names().items():
        cr.execute(
            "SELECT res_id FROM ir_model_data WHERE module = 'l10n_sk_vat_return' "
            "AND model = 'cssk.vat.return.version' AND name = %s", (xmlid,))
        row = cr.fetchone()
        if not row:
            continue
        version_id = row[0]
        for code, name in names.items():
            # Each old name belongs to its own row only: a user may have named
            # r04 "r17 — Daň celkom", and that is theirs.
            shipped = [n for n in PRE_1_14_2 if n.startswith(code + " — ")]
            old = previous.get(xmlid, {}).get(code)
            if old and old != name:
                shipped.append(old)
            cr.execute(
                """
                UPDATE cssk_vat_return_line_def
                   SET name = %s
                 WHERE version_id = %s AND code = %s AND name <> %s
                   AND (name = code OR name = ANY(%s))
                """,
                (name, version_id, code, name, shipped),
            )
            defs_renamed += cr.rowcount
            cr.execute(
                """
                UPDATE cssk_vat_return_line l
                   SET name = %s
                  FROM cssk_vat_return r
                 WHERE l.return_id = r.id AND r.version_id = %s AND l.code = %s
                   AND l.name IS DISTINCT FROM %s
                   AND (l.name IS NULL OR l.name = l.code OR l.name = ANY(%s))
                """,
                (name, version_id, code, name, shipped),
            )
            lines_renamed += cr.rowcount
    _logger.info(
        "l10n_sk_vat_return 19.0.1.15.0: %s row definition(s) and %s return "
        "line(s) renamed most specific first", defs_renamed, lines_renamed)
