"""Shared helper for localization modules of ``purchase_order_advance_invoice``.

Mirror of the sale-side pattern: a localization module declares a spec dict
mapping purchase-advance *roles* to statutory account *codes* and calls
:func:`apply_purchase_advance_spec` from its ``post_init_hook``. Codes are
resolved to ``account.account`` records per company on the matching chart
template — never by xml-id.

Spec shape::

    SPEC = {
        'journal_code': 'PDADV',
        'journal_name': 'Tax Documents for Sent Advance Payments',
        'create_accounts': [
            {'code': '314001', 'name': '…', 'account_type': 'liability_payable',
             'reconcile': True},
        ],
        'accounts': {
            'paid_clearing': '314001',  # reconcilable clearing/transit
            'paid_st': '314000',        # short-term paid advances
            'paid_lt': '',              # optional long-term variant
        },
    }
"""

import calendar
from datetime import date, timedelta


def apply_purchase_advance_spec(env, chart_template_code, spec):
    """Apply ``spec`` to every company installed on ``chart_template_code``.

    Safe to re-run on upgrade; only *empty* configuration fields are filled,
    so a deployment configured by hand is never clobbered.
    """
    companies = env["res.company"].search(
        [("chart_template", "=", chart_template_code)]
    )
    for company in companies:
        company.with_company(company)._apply_purchase_advance_setup(spec)


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
