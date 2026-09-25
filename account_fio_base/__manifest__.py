# Copyright 2026 Data Dance s.r.o.
# License LGPL-3.0 or later (https://www.gnu.org/licenses/lgpl-3.0).
{
    "name": "Fio banka API — shared client and formats",
    "summary": "Shared Fio banka REST client, movement parser and payment-order "
               "builder. The statement puller and both payment-order bridges "
               "build on this.",
    "description": """
Fio banka API — shared client and formats
=========================================

Single source of truth for the Fio banka REST API (documentation *FIO API
BANKOVNICTVÍ*, version 1.9 of 16 October 2025):

* ``utils.client.FioClient`` — the REST calls (movements by period, official
  statements, the server-side bookmark, and the payment-order upload), with the
  documented HTTP failures mapped onto named exceptions. **The token is masked
  in every message and log record it produces**, because Fio carries it in the
  URL path where a stray traceback would publish it.
* ``utils.statement`` — Fio XML and Fio JSON movement parsers, sharing one
  ``column_NN`` mapping.
* ``utils.orders`` — builds the ``importIB.xsd`` payment file (domestic,
  Europlatba and foreign orders) from the ``BankPaymentItem`` of
  ``account_cz_bankfile_base``, so the Community and Enterprise bridges share
  the format byte-for-byte.
* ``utils.response`` — parses the bank's import response, including the
  ``errorCode = 2`` case, which means *accepted with warnings*.
* ``utils.payment_reason`` — the platební titul code list (ČNB), mandatory on
  foreign payments.

No Odoo models — pure helpers, imported via
``odoo.addons.account_fio_base.utils.*``. Response builders for tests live in
``tests.fio_fixtures`` so every downstream module asserts against the same
sample payloads.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.1.2.0",
    "license": "AGPL-3",
    "depends": ["account_cz_bankfile_base", "base_iban"],
    "external_dependencies": {"python": ["requests"]},
    "installable": True,
}
