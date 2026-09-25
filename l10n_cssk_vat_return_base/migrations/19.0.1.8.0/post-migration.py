# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
"""Remove historical twins generated from an already-superseded tax.

Until 1.8.0 the generator took any tax at the source rate that was not one of
ours. Core renames a tax the chart replaces — ``chart_template.py`` builds
the prefix as ``f"[old{n if n > 1 else ''}] "``, so repeats are ``[old1]``,
``[old2]`` — and leaves it
in place, so a host that has been through a rate change carries both
``23% BAD DEBT`` and ``[old] 23% BAD DEBT`` — and the generator made a
historical twin of each:

    20% BAD DEBT              <- from "23% BAD DEBT"          keep
    20% [old] 23% BAD DEBT    <- from "[old] 23% BAD DEBT"    remove

Same concept, same rate, same type_tax_use, two records, one named for two
rates. Measured on a client instance: six of them.

Only twins WE generated (they carry ``cssk_historic_source_tax_id``) whose
SOURCE is superseded are considered, and only ones nothing references are
removed — a tax named on a posted move line is left in place and logged, so a
figure never moves silently. Idempotent.
"""
import logging

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    from odoo import SUPERUSER_ID, api

    env = api.Environment(cr, SUPERUSER_ID, {})
    twins = env["account.tax"].with_context(active_test=False).search(
        [("cssk_historic_source_tax_id", "!=", False)])

    doomed = twins.filtered(
        lambda t: t.company_id._cssk_tax_is_superseded(
            t.cssk_historic_source_tax_id))
    removed = kept = 0
    for tax in doomed:
        try:
            with env.cr.savepoint():
                tax.unlink()
            removed += 1
        except Exception:  # referenced by a move line, a fiscal position, …
            kept += 1
            _logger.warning(
                "l10n_cssk_vat_return_base 1.8.0: %r (id %s) is a twin of a "
                "superseded tax and should not exist, but something references "
                "it — left in place, review by hand",
                tax.name, tax.id)
    _logger.info(
        "l10n_cssk_vat_return_base 1.8.0: removed %s duplicate historical "
        "tax(es) generated from a superseded source, kept %s still referenced",
        removed, kept)
