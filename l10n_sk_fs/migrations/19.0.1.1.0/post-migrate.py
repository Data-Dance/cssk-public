# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Retire the two stand-in závierka versions in favour of the real UZPODv14.

Until 19.0.1.1.0 this module filed the Súvaha and the VZS as two documents
with roots ``UZSUV`` / ``UZVZS`` against two XSDs we wrote ourselves — the
template said as much in its own header ("WORKING STAND-IN … replace with the
official FS SR UZPODv14 structure before live filing"). Finančná správa
publishes neither root nor schema; the real form is ONE ``dokument`` whose
``telo`` carries ``ucPod1Suvaha`` beside ``ucPod2VykazZS``, and
``uzpod-2014.xsd`` was already sitting in this module unreferenced.

Runs POST, not pre: it needs the surviving ``uzpod_v14_template`` to exist,
and Odoo drops a module's obsolete xmlids in ``_process_end`` — after every
module's post-migration — so the foreign key is clear by the time the old
views are deleted.

Two things have to happen here rather than in the data files:

* The stand-in QWeb templates are gone from the module, but
  ``cssk_fs_statement_version.xml_template_ref_id`` is a RESTRICT foreign key
  on ``ir_ui_view``, so an upgrade that tries to drop them aborts the registry
  load outright — "Failed to load registry", nowhere near the cause.
* The version records live in a ``noupdate="1"`` file, so nothing would
  rewrite them on their own.

The stand-ins are kept (an existing statement points at one, and its filed
attachment is what a retention obligation actually asks for) but retired:
deactivated, closed off with ``valid_to``, repointed at the surviving
template, and stripped of their invented schema. That last part is what stops
a stale draft from quietly re-exporting the old made-up structure — export
refuses without a schema, which is the correct answer for a form that never
had one. Recompute such a statement on the UZPODv14 version instead.
"""

OLD = ["suvaha_version_2025", "vzs_version_2025"]


def migrate(cr, version):
    if not version:
        return
    cr.execute(
        """
        SELECT d.name, d.res_id FROM ir_model_data d
         WHERE d.model = 'cssk.fs.statement.version'
           AND d.module = 'l10n_sk_fs' AND d.name = ANY(%s)
        """,
        (OLD,),
    )
    old_ids = [row[1] for row in cr.fetchall()]
    if not old_ids:
        return

    cr.execute(
        """
        SELECT res_id FROM ir_model_data
         WHERE model = 'ir.ui.view' AND module = 'l10n_sk_fs'
           AND name = 'uzpod_v14_template'
        """
    )
    row = cr.fetchone()
    if not row:
        # Nothing to repoint onto; leave the records alone rather than
        # breaking a required foreign key.
        return

    cr.execute(
        """
        UPDATE cssk_fs_statement_version
           SET active = FALSE,
               valid_to = COALESCE(valid_to, DATE '2024-12-31'),
               xml_template_ref_id = %s,
               xml_schema_filename = NULL,
               xml_schema_optional = FALSE
         WHERE id = ANY(%s)
        """,
        (row[0], old_ids),
    )
    # ``xml_schema_data`` is attachment=True, so it has no column: the
    # invented XSD lives in ir_attachment and has to be dropped there.
    cr.execute(
        """
        DELETE FROM ir_attachment
         WHERE res_model = 'cssk.fs.statement.version'
           AND res_field = 'xml_schema_data'
           AND res_id = ANY(%s)
        """,
        (old_ids,),
    )
