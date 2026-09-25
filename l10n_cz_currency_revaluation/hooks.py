# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .models.account_chart_template import CZ_REVAL_ACCOUNTS

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Set OCA revaluation accounts + journal on existing Czech companies."""
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    for company in companies:
        vals = {}
        for field, xmlid in CZ_REVAL_ACCOUNTS.items():
            if company[field]:
                continue
            account = env.ref(
                f"account.{company.id}_{xmlid}", raise_if_not_found=False
            )
            if account:
                vals[field] = account.id
        if not company.currency_reval_journal_id:
            Journal = env["account.journal"]
            journal = Journal.search(
                [("code", "=", "KURZ"), ("company_id", "=", company.id)], limit=1
            )
            if not journal:
                journal = Journal.create(
                    {
                        "name": "Kurzové rozdíly",
                        "code": "KURZ",
                        "type": "general",
                        "company_id": company.id,
                    }
                )
            vals["currency_reval_journal_id"] = journal.id
        if vals:
            company.write(vals)
            _logger.info("Czech revaluation defaults set for %s", company.name)
