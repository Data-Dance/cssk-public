# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from .models.res_company import SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Bring SK companies that predate this module up to a fresh chart load.

    Both the vehicle taxes and the non-deductible account come from
    ``@template`` data, which only a chart load applies — so a company whose
    chart was loaded before this module was installed would get neither.
    """
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if companies:
        loaded = env["account.chart.template"]._l10n_sk_vehicle_load_taxes(
            companies
        )
        _logger.info("SK vehicle taxes: %s created", loaded)
    for company in companies:
        if company.l10n_sk_vehicle_nondeductible_account_id:
            continue
        account = env.ref(
            f"account.{company.id}_{SK_VEHICLE_NONDEDUCTIBLE_ACCOUNT}",
            raise_if_not_found=False,
        )
        if account:
            company.l10n_sk_vehicle_nondeductible_account_id = account
            _logger.info("SK vehicle-cost account set for company %s", company.name)
