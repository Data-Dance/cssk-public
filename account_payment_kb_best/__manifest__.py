# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "KB BEST Payment Export",
    "summary": "Export payment orders in Komerční banka's BEST format "
               "(domestic transfers and direct debits, foreign and SEPA "
               "transfers).",
    "description": """
Generates **BEST** payment files for Komerční banka's direct banking
(MojeBanka Business, Profibanka, Přímý kanál) from an OCA
``account.payment.order`` — CE-clean, no Enterprise dependency. The record
layout lives in ``account_kb_best_base``.

* *KB BEST (domestic transfer)* and *(domestic direct debit / inkaso)* —
  record ``01``, VS/KS/SS per line, conversion flag when the payment currency
  differs from the account's.
* *KB BEST (foreign / SEPA transfer)* — record ``02`` plus the ``03``
  structured address; sent as SEPA when EUR, IBAN, SEPA country and shared
  charges allow it.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Accounting",
    "version": "19.0.1.0.0",
    "depends": ["account_payment_order", "account_kb_best_base", "base_iban"],
    "data": [
        "data/account_payment_method.xml",
        "views/account_payment_line_views.xml",
    ],
    "license": "AGPL-3",
    "installable": True,
}
