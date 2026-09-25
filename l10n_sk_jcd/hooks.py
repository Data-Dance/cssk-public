# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from .models.res_company import SK_JCD_CLEARING_ACCOUNT

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Wire the import clearing account and duty product on existing SK companies.

    Only fills what is empty, so re-installing never overrides a mapping the
    accountant changed.
    """
    duty_product = env.ref(
        "l10n_sk_jcd.product_customs_duty", raise_if_not_found=False
    )
    for company in env["res.company"].search([("chart_template", "=", "sk")]):
        vals = {}
        if not company.l10n_sk_jcd_clearing_account_id:
            account = env.ref(
                f"account.{company.id}_{SK_JCD_CLEARING_ACCOUNT}",
                raise_if_not_found=False,
            )
            if account:
                vals["l10n_sk_jcd_clearing_account_id"] = account.id
        if not company.l10n_sk_jcd_duty_product_id and duty_product:
            vals["l10n_sk_jcd_duty_product_id"] = duty_product.id
        if vals:
            company.write(vals)
            _logger.info("SK JCD defaults set for company %s", company.name)
