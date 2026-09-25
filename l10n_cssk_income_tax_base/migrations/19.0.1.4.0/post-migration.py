# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Move historical filings onto the state that describes them.

Until now the importer set ``legacy`` and never touched ``state``, so every
materialised filing kept the default and read "Draft" — a list of completed,
years-old submissions all claiming to be unfinished work. ``legacy`` and
``state == 'legacy'`` are now one fact, joined in create/write.

Raw SQL, and that is not laziness: the ORM path is closed by design. A write
carrying ``state`` on a record that is already ``legacy`` is refused by
``_cssk_check_not_legacy`` — which is exactly the guarantee the new state
exists to give, so the migration must go under it rather than around it.
"""

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE cssk_income_tax_return
           SET state = 'legacy'
         WHERE legacy IS TRUE
           AND state IS DISTINCT FROM 'legacy'
    """)
    if cr.rowcount:
        _logger.info(
            "l10n_cssk_income_tax_base 19.0.1.4.0: %s historical income-tax returns moved onto the "
            "'legacy' state", cr.rowcount)
