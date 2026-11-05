# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Every DP DPH row carries the text of its tlačivo, not just its number.

The line definitions of all five vzory were named by their code ("r01",
"r02", …), so a return listed rows nobody could tell apart without the paper
form. The data now names each row as the form does (MF/007833/2025-731,
MF/017342/2020-731, MF/014640/2019-731, MF/016923/2017-731 and
439/2011 Z. z.).

The data is ``noupdate="1"``, so the names are written here: the new name is
read from the module's own data files, which keeps the texts in one place.
A definition is renamed only while it still holds a name this module shipped
(its code, or one of the short names below), and a return line only while it
still holds its definition's old name, so nothing a user edited is touched.
"""
import ast
import logging

from lxml import etree

from odoo.tools.misc import file_path

_logger = logging.getLogger(__name__)

DATA_FILES = (
    "l10n_sk_vat_return/data/cssk_vat_return_version_data.xml",
    "l10n_sk_vat_return/data/cssk_vat_return_2024_version_data.xml",
    "l10n_sk_vat_return/data/cssk_vat_return_legacy_version_data.xml",
)

#: Short names shipped before 19.0.1.14.2 for the rows that had one.
OLD_NAMES = {
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
}


def shipped_names():
    """{version xmlid: {code: name}} as the data files define them."""
    out = {}
    for rel in DATA_FILES:
        tree = etree.parse(file_path(rel))
        for rec in tree.iter("record"):
            if rec.get("model") != "cssk.vat.return.version":
                continue
            field = rec.find("field[@name='line_def_ids']")
            if field is None:
                continue
            defs = [cmd[2] for cmd in ast.literal_eval(field.get("eval"))]
            out[rec.get("id")] = {d["code"]: d["name"] for d in defs}
    return out


def migrate(cr, version):
    if not version:
        return
    defs_renamed = lines_renamed = 0
    for xmlid, names in shipped_names().items():
        cr.execute(
            "SELECT res_id FROM ir_model_data WHERE module = 'l10n_sk_vat_return' "
            "AND model = 'cssk.vat.return.version' AND name = %s", (xmlid,))
        row = cr.fetchone()
        if not row:
            continue
        version_id = row[0]
        for code, name in names.items():
            cr.execute(
                """
                UPDATE cssk_vat_return_line_def
                   SET name = %s
                 WHERE version_id = %s AND code = %s AND name <> %s
                   AND (name = code OR name = ANY(%s))
             RETURNING id
                """,
                (name, version_id, code, name, list(OLD_NAMES)),
            )
            if not cr.rowcount:
                continue
            defs_renamed += cr.rowcount
            cr.execute(
                """
                UPDATE cssk_vat_return_line l
                   SET name = %s
                  FROM cssk_vat_return r
                 WHERE l.return_id = r.id AND r.version_id = %s AND l.code = %s
                   AND (l.name IS NULL OR l.name = l.code OR l.name = ANY(%s))
                """,
                (name, version_id, code, list(OLD_NAMES)),
            )
            lines_renamed += cr.rowcount
    _logger.info(
        "l10n_sk_vat_return 19.0.1.14.2: %s row definition(s) and %s return "
        "line(s) now carry the tlačivo's row text", defs_renamed, lines_renamed)
