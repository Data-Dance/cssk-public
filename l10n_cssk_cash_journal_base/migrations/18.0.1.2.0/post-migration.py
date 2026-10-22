# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Fill ``money_direction`` on rows generated before it existed.

    Until now ``kind`` carried the direction, so the old value is exactly the
    direction: an income row was money in. ``counter_entry`` stays False, which
    is what those rows meant — the storno case is the one the split introduces,
    and a regeneration will find it. The rows are regenerable anyway; this only
    keeps a book that is already on screen readable until someone does.
    """
    # Migration scripts still take ``(cr, version)`` in 19.0 — unlike
    # post_init_hook / uninstall_hook, which took ``(env)`` from 19.0 on.
    cr.execute("""
        UPDATE cssk_cash_journal_line
           SET money_direction = CASE
                   WHEN non_cash THEN 'none'
                   WHEN kind = 'income' THEN 'in'
                   ELSE 'out'
               END
         WHERE money_direction IS NULL OR money_direction = 'none'
    """)
    _logger.info("cssk.cash.journal.line: money_direction set on %s rows",
                 cr.rowcount)
