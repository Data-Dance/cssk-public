# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from odoo import SUPERUSER_ID, api

_logger = logging.getLogger(__name__)


def migrate(cr, version):
    """Repoint the shipped money-in-transit predkontácie.

    They used 221000 / 211000, which no bank or cash journal posts to, and
    261000, the company's bank suspense account. Lines still on those
    accounts move to the journal accounts and the Liquidity Transfer
    account; a line somebody changed is left alone.
    """
    if not version:
        return
    env = api.Environment(cr, SUPERUSER_ID, {})
    moved = env["account.chart.template"]._l10n_sk_fix_move_template_accounts(
        env["res.company"].search([("chart_template", "=", "sk")])
    )
    _logger.info("SK predkontácie: %s template line(s) repointed", moved)
