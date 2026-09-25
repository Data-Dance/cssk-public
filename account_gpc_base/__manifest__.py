# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "GPC Statement Format — shared parser",
    "summary": "Shared GPC (ABO electronic statement) parser. The CE "
               "(account_statement_import_file) and EE "
               "(account_bank_statement_import) import shims both build on this.",
    "description": """
Single source of truth for the Czech/Slovak **GPC** bank-statement format (the
ABO electronic statement used by Fio, KB, ČS, ČSOB, …):

* ``utils.gpc.parse_gpc`` — parses a GPC file into the ``(currency, account,
  statements)`` triplets both import frameworks consume.
* ``utils.gpc.is_gpc`` — cheap format sniff for the Enterprise framework, which
  asks each installed parser whether it recognises the file.

No models — pure helpers, imported via
``odoo.addons.account_gpc_base.utils.gpc``. Record builders for tests live in
``tests.gpc_fixtures`` so both shims assert against the same sample files.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["base"],
    "installable": True,
}
