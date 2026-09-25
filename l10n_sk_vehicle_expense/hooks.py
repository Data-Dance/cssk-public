# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from .models.res_company import SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Wire the non-deductible account on SK companies that predate this module."""
    for company in env["res.company"].search([("chart_template", "=", "sk")]):
        if company.l10n_sk_vehicle_nondeductible_account_id:
            continue
        account = env.ref(
            f"account.{company.id}_{SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT}",
            raise_if_not_found=False,
        )
        if account:
            company.l10n_sk_vehicle_nondeductible_account_id = account
            _logger.info("SK vehicle-cost account set for company %s", company.name)
