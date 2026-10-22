# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Store receipt issue times in UTC, as every Odoo datetime is.

Until 19.0.1.1.0 both providers wrote the time printed on the receipt — local
time — straight into ``issue_date``, which Odoo reads as UTC. The form showed it
an hour or two late, and fixing the storage without fixing the readers would
have moved receipts printed just after midnight to the previous day.

Only rows a provider wrote are converted (``captured_on`` set): a date typed
into the form went through the web client, which already converts to UTC. A
receipt captured and then corrected by hand cannot be told apart and is
converted too; at this version's age there are a handful of such rows at most.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    cr.execute("""
        UPDATE cssk_receipt
           SET issue_date = (issue_date AT TIME ZONE 'Europe/Bratislava')
                            AT TIME ZONE 'UTC',
               issue_tz = 'Europe/Bratislava'
         WHERE issue_date IS NOT NULL
           AND captured_on IS NOT NULL
           AND issue_tz IS NULL
    """)
    _logger.info("l10n_cssk_receipt_capture: %s receipt issue time(s) moved to UTC",
                 cr.rowcount)
