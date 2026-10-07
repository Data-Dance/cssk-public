# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Let the corrected UZPODv14 row definitions reach existing databases.

The version record lives in a ``noupdate="1"`` data file — it has to, because
its 206 line definitions are a one2many payload and ``_load_data`` APPENDS
those rather than replacing them, so an ordinary reload would double every
row. The consequence is that an upgrade alone leaves an existing database on
the OLD mapping: the one where r043/r044/r045 each claimed the whole of
311-315 and A.VIII was a plug that hid it. Nothing would look wrong — the
sheet still footed and still balanced.

So: drop the existing line definitions and clear the record's noupdate flag
before the data file loads. The payload then appends onto nothing, which is
the same result a fresh install gets. Runs PRE, because the data file loads
after pre-migration and before post.

Statements already computed keep their stored lines; they are a record of
what was computed at the time. Recompute one to move it onto the corrected
mapping — and expect A.VIII to change, because that is the row that was
absorbing the error.
"""


def migrate(cr, version):
    if not version:
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
        return                      # never installed; the fresh load is right
    version_id = row[0]

    cr.execute(
        """
        DELETE FROM ir_model_data
         WHERE model = 'cssk.fs.statement.line.def'
           AND res_id IN (SELECT id FROM cssk_fs_statement_line_def
                           WHERE version_id = %s)
        """,
        (version_id,),
    )
    cr.execute(
        "DELETE FROM cssk_fs_statement_line_def WHERE version_id = %s",
        (version_id,),
    )
    cr.execute(
        """
        UPDATE ir_model_data SET noupdate = FALSE
         WHERE model = 'cssk.fs.statement.version'
           AND module = 'l10n_sk_fs' AND name = 'uzpod_v14'
        """
    )
