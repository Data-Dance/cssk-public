# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Create the starter predkontácie on SK companies that already had the
    chart loaded before this module was installed.

    Reuses the chart-template loader rather than hand-rolling record creation,
    so the xmlids, the company prefixing and the account dereferencing are
    identical to the ones a fresh chart load produces; and, like it, creates
    only the templates a company does not have yet (see
    ``_l10n_sk_load_move_templates``).

    Runs sudo: a post-init hook must work whatever companies the installing
    user happens to belong to.
    """
    companies = env["res.company"].search([("chart_template", "=", "sk")])
    chart_template = env["account.chart.template"].sudo()
    for company in companies:
        loaded = chart_template._l10n_sk_load_move_templates(company)
        if loaded:
            _logger.info(
                "SK predkontácie: %s template(s) loaded for company %s",
                loaded,
                company.name,
            )
