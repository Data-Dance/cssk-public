# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .models.account_chart_template import SK_ZAVIERKOVE_UCTY

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Retype the závierkové účty on SK companies that already had the chart.

    See the comment on SK_ZAVIERKOVE_UCTY: while they are 'off_balance', Odoo
    refuses to post any entry that mixes them with ordinary accounts, so no
    závierka can be produced at all.
    """
    for company in env["res.company"].search([("chart_template", "=", "sk")]):
        for xmlid, account_type in SK_ZAVIERKOVE_UCTY.items():
            account = env.ref(
                f"account.{company.id}_{xmlid}", raise_if_not_found=False
            )
            if account and account.account_type == "off_balance":
                account.account_type = account_type
                _logger.info(
                    "SK závierka: %s retyped to %s for company %s",
                    account.code,
                    account_type,
                    company.name,
                )
