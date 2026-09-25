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
