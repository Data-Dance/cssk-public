# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .models.account_chart_template import CZ_ZAVERKOVE_UCTY

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Retype the závěrkové účty on CZ companies that already had the chart.

    The template override covers a chart loaded from now on; this covers every
    company that already exists — which on a migration project is all of them,
    since the companies are created before anybody notices the constraint.
    """
    retype(env)


def retype(env):
    """Retype the three accounts wherever they are still off_balance."""
    changed = 0
    for company in env["res.company"].search([("chart_template", "=", "cz")]):
        for xmlid, account_type in CZ_ZAVERKOVE_UCTY.items():
            account = env.ref(
                "account.%s_%s" % (company.id, xmlid), raise_if_not_found=False
            )
            if account and account.account_type == "off_balance":
                account.account_type = account_type
                changed += 1
                _logger.info(
                    "CZ závěrka: %s retyped to %s for company %s",
                    account.code, account_type, company.name,
                )
    return changed
