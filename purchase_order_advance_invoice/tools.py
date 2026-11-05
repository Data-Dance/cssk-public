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
            {'code': '314001',
             'name': {'en_US': '…', 'sk_SK': '…'},  # or one str
             'account_type': 'liability_payable', 'reconcile': True},
        ],
        'accounts': {
            'paid_clearing': '314001',  # reconcilable clearing/transit
            'paid_st': '314000',        # short-term paid advances
            'paid_lt': '',              # optional long-term variant
        },
    }
"""

import calendar
import json
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


def advance_account_names(name):
    """``{lang: name}`` for a spec name given as a str or a dict.

    A plain str is the old spec shape: one name, stored as the English source.
    """
    if isinstance(name, dict):
        return dict(name)
    return {"en_US": name}


def _stored_names(record, field="name"):
    record.flush_recordset([field])
    record.env.cr.execute(
        f'SELECT "{field}" FROM "{record._table}" WHERE id = %s', [record.id]
    )
    row = record.env.cr.fetchone()
    return (row and row[0]) or {}


def write_translated_names(record, names, field="name"):
    """Store every language of ``names`` on ``record``, installed or not.

    The ORM's ``update_field_translations`` refuses languages that are not
    active, so a Slovak name written while only English is installed would be
    lost and a Slovak user installing the language later would see the English
    one. The jsonb is merged directly instead: a key for an inactive language
    is harmless and is simply there once the language is activated.
    """
    if not names:
        return
    record.flush_recordset([field])
    record.env.cr.execute(
        f'UPDATE "{record._table}" SET "{field}" = '
        f'COALESCE("{field}", \'{{}}\'::jsonb) || %s::jsonb WHERE id = %s',
        [json.dumps(names), record.id],
    )
    record.invalidate_recordset([field])


def adopt_translated_names(record, names, also_replace=(), field="name"):
    """Give an existing record the names of the spec, if it still has ours.

    * Its English name is one of the spec's other-language names, or a default
      an earlier version used (``also_replace``): it was made by us with a
      national name stored as the English source, and gets all of ``names``.
    * Its English name is already the spec's: only the languages it lacks are
      added, so a translation someone corrected by hand survives.
    * Anything else is a name the user chose, and is left alone.
    """
    stored = _stored_names(record, field)
    current = stored.get("en_US")
    ours = {value for lang, value in names.items() if lang != "en_US"}
    ours |= set(also_replace)
    if current in ours and current != names.get("en_US"):
        write_translated_names(record, names, field)
    elif current == names.get("en_US"):
        missing = {lang: value for lang, value in names.items() if lang not in stored}
        if missing:
            write_translated_names(record, missing, field)


# The names these helpers had when they only handled accounts.
write_advance_account_names = write_translated_names
adopt_advance_account_names = adopt_translated_names
