"""Shared helper for localization modules of ``sale_order_advance_invoice``.

A localization module (e.g. ``l10n_cz_sale_order_advance_invoice``) declares a
spec dict mapping advance-invoice *roles* to statutory account *codes* and calls
:func:`apply_advance_invoice_spec` from its ``post_init_hook``.  The codes are
resolved to ``account.account`` records per company on the matching chart
template and written onto the company configuration fields.

This mirrors the pattern used by the Method A stock-valuation modules: accounts
are referenced by code (stable across companies in Odoo 19), never by xml-id.

Spec shape::

    SPEC = {
        'journal_code': 'TDADV',
        'journal_name': 'Tax Documents for Advance Invoices',
        'accounts': {
            'received_clearing': '324001',   # reconcilable clearing/transit
            'tax_doc_st': '324000',          # short-term net advance liability
            'tax_doc_lt': '475000',          # long-term net advance liability
        },
    }
"""

import calendar
from datetime import date, timedelta


def apply_advance_invoice_spec(env, chart_template_code, spec):
    """Apply ``spec`` to every company installed on ``chart_template_code``.

    Safe to re-run on upgrade; only *empty* configuration fields are filled, so a
    deployment that configured the accounts/journal by hand is never clobbered.
    """
    companies = env["res.company"].search([("chart_template", "=", chart_template_code)])
    if not companies:
        return
    for company in companies:
        company.with_company(company)._apply_advance_invoice_setup(spec)


def advance_tax_doc_deadline(company, paid_date):
    """Last day to issue the tax document on an advance paid on ``paid_date``.

    * Czech Republic - 15 days from the day the obligation to declare the tax
      arose (§ 28 odst. 8 zákona č. 235/2004 Sb.), with no month-end cap.
    * Slovakia - 15 days from receiving the payment *or* the end of the month
      in which it was received, whichever is later (§ 73 ods. 1 písm. b)
      zákona č. 222/2004 Z. z.); the month-end alternative is in force from
      1. 1. 2016, before which it was 15 days only.
    * Anywhere else - the 15 days, which neither rule above undercuts.

    The country is the company's fiscal country: the deadline is the issuer's,
    and an advance between two domestic parties is the case both laws mean.
    """
    fifteen_days = paid_date + timedelta(days=15)
    country = company.account_fiscal_country_id.code or company.country_id.code
    if country == "SK" and paid_date >= date(2016, 1, 1):
        end_of_month = paid_date.replace(
            day=calendar.monthrange(paid_date.year, paid_date.month)[1]
        )
        return max(fifteen_days, end_of_month)
    return fifteen_days
