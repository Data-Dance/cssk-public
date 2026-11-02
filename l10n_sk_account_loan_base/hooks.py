# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

from .models.account_chart_template import sk_loan_company_values

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Set the leasing accounts on SK companies that already had the chart
    loaded before this module was installed.

    Only fills empty fields, so re-installing never overwrites a mapping the
    accountant has changed.
    """
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    for company in companies:
        vals = {}
        for field, xmlid in sk_loan_company_values().items():
            if company[field]:
                continue
            account = env.ref(
                f"account.{company.id}_{xmlid}", raise_if_not_found=False
            )
            if account:
                vals[field] = account.id
        if vals:
            company.write(vals)
            _logger.info("SK leasing accounts set for company %s", company.name)
