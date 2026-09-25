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
