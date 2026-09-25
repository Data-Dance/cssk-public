# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Clear the `recomputed` basis label, which no longer gets written.

It carried "the same filing, recomputed from the ledger" — a restatement of the
``basis`` selection the screen already shows translated, and, being stored, in
the language of whoever ran the comparison. 19.0.1.11.3 stopped writing it.

Stopping writing it is not the same as clearing it, and the difference showed
up on a live box: the old English text sits in the column until somebody
re-runs that comparison, so a database nobody re-runs keeps showing it for ever.
That is the same trap the label itself was — a stored snapshot that only a
re-run repairs — and refusing to fix it here would be reintroducing in one
column what was just removed from another.

ONLY the ``recomputed`` basis. The others name specific records ("DPH priznanie
FA/2017/06", "účtovníctvo — účet 343 a účtová trieda 60"), are Slovak in source,
and carry information the selection cannot.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    for table in ("cssk_filing_comparison", "cssk_filing_discrepancy"):
        cr.execute("""
            SELECT 1 FROM information_schema.tables WHERE table_name = %s
        """, (table,))
        if not cr.fetchone():
            continue
        cr.execute(
            "UPDATE %s SET basis_label = NULL "
            " WHERE basis = 'recomputed' AND basis_label IS NOT NULL" % table)
        if cr.rowcount:
            _logger.info("l10n_cssk_core: cleared %d stale recomputed "
                         "basis_label(s) on %s", cr.rowcount, table)
