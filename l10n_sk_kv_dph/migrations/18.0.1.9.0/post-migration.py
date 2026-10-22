# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Create the sale-side §69 ods. 12 reverse-charge tax on existing SK
    companies.

    New in 1.9.0. The tax is a chart-template ``@template`` record, which only
    materialises when the SK chart is loaded — so every company that already had
    the chart (i.e. every existing install, the whole point on a migration
    project) would never get it, and an issued §69/12 supply would have no 0 %
    tax to carry it into KV oddiel A.2. Same ``noupdate`` trap the 1.3.0
    migration documents: the post_init_hook runs on install only. Idempotent.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    created = companies._cssk_ensure_rc_out_tax()
    flagged = companies._cssk_flag_reverse_charge_taxes()
    _logger.info(
        "l10n_sk_kv_dph 1.9.0: %s sale-side §69/12 tax(es) created, %s "
        "reverse-charge tax(es) (re)flagged across %s company/companies",
        created, flagged, len(companies),
    )
