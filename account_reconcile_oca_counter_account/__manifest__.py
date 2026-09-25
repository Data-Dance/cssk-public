# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl-3.0).
{
    "name": "Reconcile OCA — show the counterparty's account",
    "summary": "Put the counterparty bank account back on the OCA bank "
               "statement reconciliation screen.",
    "description": """
Reconcile OCA — show the counterparty's account
===============================================

OCA's reconciliation widget renders a curated set of fields, and
``account_number`` — the counterparty's account as the bank sent it — is not
among them. Every statement importer in the
``account_statement_import_base`` family fills that field, so the information is
there; it is simply invisible on the one screen where somebody is deciding who a
payment came from.

In CZ/SK that matters more than elsewhere. A payer who quotes no variable symbol
is very often identifiable only by their account number, and matching by name
alone is exactly the guess that puts a receivable against the wrong customer.

This module adds ``account_number`` and ``partner_bank_id`` to the reconciliation
form. Nothing else — no fields, no logic.

It is deliberately generic: it names no bank, so it serves the Tatra banka and
Fio banka importers, the GPC file importer and anything else in that family
equally. Worth proposing upstream.
    """,
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Bank",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": ["account_reconcile_oca"],
    "data": ["views/account_bank_statement_line_views.xml"],
    "auto_install": True,
    "installable": True,
}
