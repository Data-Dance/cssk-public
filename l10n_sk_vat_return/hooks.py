# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Generate the archived historical Slovak VAT rates for existing companies.

    Runs on install rather than waiting to be asked, because the rates are
    archived: nothing appears in a picker, nothing changes on a document, and
    the only observable effect is that a history import has something correct to
    map onto. A company that loads the Slovak chart later gets them from
    :meth:`~odoo.addons.l10n_sk_vat_return.models.res_company.ResCompany`'s
    chart-load hook.
    """
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    if companies:
        # Before the historical rates, so a clone run afterwards sees them.
        env["account.chart.template"]._cssk_load_sk_eu_service_taxes(companies)
        companies._cssk_create_historic_vat_taxes()
        _logger.info(
            "l10n_sk_vat_return: historical VAT rates prepared for %s company "
            "(companies)", len(companies),
        )
