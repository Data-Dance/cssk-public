# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Flag the reverse-charge taxes of companies that already had this module.

    ``post_init_hook`` runs on install only, so a company whose chart was
    loaded after the module went in was never flagged — and an unflagged
    company reports **no B.1 rows at all**, silently. Found on the reference
    database: of two Slovak companies in one installation, the one whose chart
    was loaded first had 10 flagged taxes and the one created later had none.
    """
    env = api.Environment(cr, SUPERUSER_ID, {})
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if not companies:
        return
    flagged = companies._cssk_flag_reverse_charge_taxes()
    _logger.info(
        "l10n_sk_kv_dph: %s reverse-charge tax(es) flagged across %s company/companies",
        flagged, len(companies),
    )
