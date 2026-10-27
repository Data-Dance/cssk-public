# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl.html).

import logging

from .models.account_chart_template import CZ_CUTOFF_ACCOUNTS

_logger = logging.getLogger(__name__)


def _accrued_tax_accounts_configured(company):
    """True when somebody has set up accruing VAT, on the company or a tax."""
    if (company.default_accrued_expense_tax_account_id
            or company.default_accrued_revenue_tax_account_id):
        return True
    taxes = company.env["account.tax"].with_context(active_test=False)
    return bool(taxes.search_count([
        ("company_id", "=", company.id),
        "|",
        ("account_accrued_expense_id", "!=", False),
        ("account_accrued_revenue_id", "!=", False),
    ], limit=1))


def disable_unconfigured_tax_accrual(companies):
    """Switch Accrual On Taxes off where nothing is set up to take the VAT.

    Left on with nowhere to book the tax, every accrual of a taxed line
    fails; see CZ_CUTOFF_FLAGS for why off is also the law. A company with an
    accrued-tax account, on itself or on a tax, made a choice: kept.
    Returns the companies changed.
    """
    changed = companies.filtered(
        lambda company: company.accrual_taxes
        and not _accrued_tax_accounts_configured(company)
    )
    if changed:
        changed.write({"accrual_taxes": False})
    return changed


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
    disable_unconfigured_tax_accrual(companies)
