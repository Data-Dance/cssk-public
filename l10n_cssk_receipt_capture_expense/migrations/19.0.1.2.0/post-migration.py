# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Fill the expenses a late reading left blank.

Until 19.0.1.2.0 an uploaded photograph filled its expense only inside the
upload. One whose first reading failed and that was read later — by hand, or by
the cron's retry — has a captured receipt behind an untitled expense at 0.00,
which cannot be submitted. Those are filled here, by the same rule the receipt
now applies when it becomes captured: only a draft with no amount is touched.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    receipts = env["cssk.receipt"].search([
        ("state", "=", "captured"), ("expense_ids", "!=", False)])
    waiting = receipts.expense_ids.filtered(lambda e: e._cssk_awaits_reading())
    receipts._fill_waiting_expenses()
    _logger.info(
        "l10n_cssk_receipt_capture_expense: %s expense(s) were waiting on a "
        "captured receipt; %s filled", len(waiting),
        len(waiting.filtered(lambda e: not e._cssk_awaits_reading())))
