# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Drop ``form_label``: the label is rendered now, not stored.

It held the form's name as TEXT, written in the language of whoever ran the
comparison. So a comparison run in English read English to every later reader,
and the only repair was to re-run it — seven filings by hand on the demo box to
turn one screen Slovak. The key (``res_model``) was sitting in the next column
the whole time; it is now a Selection whose labels are rendered per reader, so
the field stays groupable and the text stays correct for everybody.

Nothing is backfilled because nothing is lost: ``form_label`` was derived from
``res_model`` on every write, and ``res_model`` is required and already
populated. Odoo does not drop removed columns by itself, so an untouched
``form_label`` would sit there for ever looking authoritative.

THE SCHEMA IS ALREADY FINAL WHEN THIS RUNS, and that is worth stating because
it is what makes the sibling script at 19.0.1.11.0 safe. ``loading.py`` runs
``migrate_module(pre)`` → ``registry.init_models()`` → ``migrate_module(post)``,
once per module upgrade rather than once per version — so EVERY post-migration,
including older ones replayed in the same upgrade, sees the final columns. That
is why 19.0.1.11.0's INSERT no longer names ``form_label``: on a database coming
from 19.0.1.10.5 the table is created without it before that script runs.

Both paths are therefore covered. A database that already carries the column
(one upgraded through 19.0.1.11.0 earlier) gets it dropped here; one arriving
fresh never had it and the guard below simply finds nothing.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    for table in ("cssk_filing_comparison", "cssk_filing_discrepancy"):
        cr.execute("""
            SELECT 1 FROM information_schema.columns
             WHERE table_name = %s AND column_name = 'form_label'
        """, (table,))
        if not cr.fetchone():
            continue
        # Refuse to drop a column carrying something res_model cannot rebuild.
        # It never should — the writer derived it from the model on every run —
        # but "never should" is what the NULL-in-a-required-column audit said
        # about four other fields in this repo.
        cr.execute("SELECT COUNT(*) FROM %s WHERE res_model IS NULL" % table)
        orphans = cr.fetchone()[0]
        if orphans:
            raise ValueError(
                "%s: %d row(s) have no res_model, so dropping form_label would "
                "lose the only record of which form they belong to. Fix those "
                "rows and re-run the upgrade." % (table, orphans))
        cr.execute("ALTER TABLE %s DROP COLUMN form_label" % table)
        _logger.info("l10n_cssk_core: dropped %s.form_label", table)
