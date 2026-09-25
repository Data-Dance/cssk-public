# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .models.account_chart_template import CZ_CUTOFF_ACCOUNTS

_logger = logging.getLogger(__name__)


def post_init_hook(env):
    """Set the deferral default accounts on CZ companies that already had the
    chart loaded before this module was installed."""
    companies = env["res.company"].search([("chart_template", "=", "cz")])
    for company in companies:
        vals = {}
        for field, xmlid in CZ_CUTOFF_ACCOUNTS.items():
            if company[field]:
                continue
            account = env.ref(
                f"account.{company.id}_{xmlid}", raise_if_not_found=False
            )
            if account:
                vals[field] = account.id
        if not company.default_cutoff_journal_id:
            journal = env["account.journal"].search(
                [("type", "=", "general"), ("company_id", "=", company.id)], limit=1
            )
            if journal:
                vals["default_cutoff_journal_id"] = journal.id
        if vals:
            company.write(vals)
            _logger.info("CZ cut-off defaults set for company %s", company.name)
