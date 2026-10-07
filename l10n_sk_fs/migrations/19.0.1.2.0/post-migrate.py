# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Carry the corrected UZPODv14 row captions to an existing database.

The captions shipped in 19.0.1.1.0 were transcribed from a plain pdftotext
dump of the tlačivo, where a two-line caption bleeds into the row below it:
"Poskytnuté" sat on r009 and r010 read "7. preddavky na dlhodobý nehmotný
majetok". About a third of the form was shifted like that. They are now read
off the form's own column layout — ``tools/parse_uzpod14_labels.py`` produces
``data/uzpod14_row_labels.tsv``, and the generator writes them into the
version record.

The FIGURES do not change; only the names. But the names are what an
accountant reads when checking a statement, and a caption naming the row
above's accounts is worse than no caption at all.

Why the names are written here directly, rather than by reloading the data
file the way 19.0.1.1.0 did: that record lives in a ``noupdate="1"`` file, and
clearing the flag only gets an UPDATE. Its 206 line definitions are a
one2many payload, and on an update the ``(0, 0, {...})`` commands do not
re-create rows that a pre-migration has just deleted — which leaves the
version with no lines at all. It worked in 19.0.1.1.0 only because the record
did not exist yet and was CREATED. Writing the captions is also the narrower
change: nothing else about the rows moves.

A statement already computed keeps its own stored lines, captions and all;
recompute it to pick up the corrected ones.

The column may still be ``jsonb`` when this runs. ``name`` was translatable
in 19.0.1.0.0, and Odoo 19 does not convert such a column when the module
that dropped ``translate`` is upgraded: it snapshots ``ir_model_fields``
at the start of the load and keeps every field translated there patched as
translated for the whole load — converting a column a pre-migration has
flattened straight back to ``jsonb``. The end-of-load step meant to flatten
them (``odoo/modules/loading.py``) re-runs setup for no model, so the patch
survives it and the column stays ``jsonb`` after a successful upgrade too.
Either way, a migration on a database coming from 19.0.1.0.0 sees ``jsonb``. Comparing that
with text failed the whole upgrade with ``operator does not exist: jsonb =
text``.
"""

import logging
import os

_logger = logging.getLogger(__name__)

LABELS = os.path.join(
    os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
    "data", "uzpod14_row_labels.tsv",
)


def migrate(cr, version):
    if not version:
        return
    if not os.path.exists(LABELS):
        _logger.warning("l10n_sk_fs: %s is missing; captions left as they are",
                        LABELS)
        return

    labels = {}
    with open(LABELS, encoding="utf-8") as handle:
        for line in handle:
            code, _sep, label = line.rstrip("\n").partition("\t")
            if code and label:
                labels[code] = label
    if not labels:
        return

    cr.execute(
        """
        SELECT res_id FROM ir_model_data
         WHERE model = 'cssk.fs.statement.version'
           AND module = 'l10n_sk_fs' AND name = 'uzpod_v14'
        """
    )
    row = cr.fetchone()
    if not row:
        return

    cr.execute(
        """
        SELECT data_type FROM information_schema.columns
         WHERE table_schema = current_schema()
           AND table_name = 'cssk_fs_statement_line_def' AND column_name = 'name'
        """
    )
    translated = (cr.fetchone() or [None])[0] == "jsonb"
    if translated:
        current = "d.name->>'en_US'"
        # Keep any other language; Odoo keeps only en_US when it flattens.
        caption = (
            "CASE WHEN jsonb_typeof(d.name) = 'object' THEN d.name "
            "ELSE '{}'::jsonb END || jsonb_build_object('en_US', c.label)"
        )
    else:
        current = "d.name"
        caption = "c.label"

    cr.execute(
        f"""
        UPDATE cssk_fs_statement_line_def d
           SET name = {caption}
          FROM (SELECT unnest(%s::text[]) AS code,
                       unnest(%s::text[]) AS label) c
         WHERE d.version_id = %s AND d.code = c.code
           AND {current} IS DISTINCT FROM c.label
        """,
        (list(labels), [labels[c] for c in labels], row[0]),
    )
    _logger.info("l10n_sk_fs: %d UZPODv14 row caption(s) corrected", cr.rowcount)
