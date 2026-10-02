# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "MT940 / MultiCash Statement Format — shared parser",
    "summary": "Shared SWIFT MT940 parser with the Czech ?NN layout of field "
               ":86: (MultiCash *.STA statements).",
    "description": """
Single source of truth for **SWIFT MT940** bank statements as Czech banks hand
them to accounting through MultiCash (``*.STA``), X-business and Business 24:

* ``utils.mt940.parse_mt940`` — parses a file into the ``(currency, account,
  statements)`` triplets the OCA statement-import framework consumes, with the
  VS/KS/SS symbols, counterparty account and name read out of the structured
  ``?NN`` subfields of field :86:.
* ``utils.mt940.is_mt940`` — cheap format sniff for a parser chain.
* ``utils.mt940.statement_account`` — normalises the :25: account.

No models — pure helpers, imported via
``odoo.addons.account_mt940_base.utils.mt940``. Sample-file builders for tests
live in ``tests.mt940_fixtures``.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base"],
    "installable": True,
}
