# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Map the chart of every Slovak company already in the database.

    A module installed after the chart cannot rely on a template hook, and an
    accountant should not have to map forty accounts by hand to see the first
    denník. Existing categories are left alone, and the same mapping can be
    re-applied from the settings button later.

    post_init_hook takes (env) from 19.0 on.
    """
    # ``res.company.country_id`` is a non-stored compute over the company's
    # partner in 19.0, so it cannot appear in a search domain — filtering in
    # Python is the only way, and a database has few companies.
    companies = env["res.company"].search([]).filtered(
        lambda company: company.country_id.code == "SK")
    if not companies:
        return
    touched = companies._cssk_map_chart_categories()
    _logger.info(
        "l10n_sk_cash_journal: mapped %s accounts to cash journal categories in %s companies",
        touched, len(companies))
