# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Re-resolve the lines a tax "Based on Payment" touches.

The resolver used to classify an unpaid invoice from its taxes without asking
whether they were due, and a cash-basis entry as a document of its own (no
partner, no number). Both are stored values that no data change will refresh;
see ``account.move.line._cssk_recompute_cash_basis_section_codes``.
"""
import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    changed = env["account.move.line"]._cssk_recompute_cash_basis_section_codes(
        "SK")
    _logger.info("l10n_sk_kv_dph 19.0.2.0.7: %s cash-basis line(s) changed section", changed)
