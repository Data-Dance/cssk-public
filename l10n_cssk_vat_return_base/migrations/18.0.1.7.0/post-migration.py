# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Repair historical VAT taxes whose name carries two rates.

Until 1.7.0 the historical twin's name was built by testing
``name.startswith("%g%%" % source_rate)`` — that is ``"23%"``. A chart naming
the same tax ``"23 % EÚ"``, with a space, failed the test and fell through to
the collision-avoiding branch, producing ``"20% 23 % EÚ"``: two rates in one
name, saying neither.

Cosmetic on its own, and it broke cross-host tax matching by name outright —
found on a client instance where every pre-2025 tax read that way, while a host
whose chart writes ``"23%"`` was clean.

Only a name this module itself generated the OLD way is touched: the migration
recomputes what the buggy generator would have produced and replaces the name
only where the stored one matches it exactly. A tax someone renamed by hand
does not match, and is left alone.
"""
import logging

_logger = logging.getLogger(__name__)


def _old_name(name, source_rate, rate):
    """What 1.6.0 and earlier would have generated."""
    prefix = "%g%%" % source_rate
    if name.startswith(prefix):
        return "%g%%%s" % (rate, name[len(prefix):])
    return "%g%% %s" % (rate, name)


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    taxes = env["account.tax"].with_context(active_test=False).search(
        [("cssk_historic_source_tax_id", "!=", False)])
    renamed = 0
    for tax in taxes:
        source = tax.cssk_historic_source_tax_id
        if not source.name:
            continue
        company = tax.company_id
        was = _old_name(source.name, source.amount, tax.amount)
        if tax.name != was:
            continue  # hand-edited, or already correct — not ours to change
        now = company._cssk_historic_tax_name(
            source.name, source.amount, tax.amount)
        if now != tax.name:
            tax.name = now
            renamed += 1
    _logger.info(
        "l10n_cssk_vat_return_base 1.7.0: repaired %s historical tax name(s) "
        "that carried two rates", renamed)
