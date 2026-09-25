# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Bank Statement Import — GPC (CZ/SK)",
    "version": "19.0.2.0.0",
    "summary": "Import Czech/Slovak GPC (ABO) bank statement files.",
    "description": """
Bank Statement Import — GPC (CZ/SK)
===================================

Imports bank statements in the GPC format (the ABO electronic statement
format used by Czech and Slovak banks — Fio, KB, ČS, ČSOB, …) through the
OCA statement import framework. The parser itself lives in
``account_gpc_base`` and is shared with the Enterprise shim
(``account_statement_import_gpc_ee``).

* Record ``074`` — statement header: account, statement number, opening and
  closing balance, accounting date.
* Record ``075`` — transaction: amount in haléře with the debit/credit and
  reversal accounting codes, counterparty account (with the bank code from
  the constant-symbol field), document number and the native **VS/KS/SS
  payment symbols**.
* Records ``076``/``078``/``079`` — additional message (AV) lines are
  appended to the preceding transaction's label.

The symbols are written to the statement line's ``variable_symbol`` /
``constant_symbol`` / ``specific_symbol`` fields when a module providing
them is installed (``l10n_cssk_payment_symbols``, or upstream l10n_cz once
odoo/odoo#275611 lands) and always kept as ``VS:``-style tokens in the
line label, so matching works with or without the symbols module.

Multiple statements (074 blocks) per file are supported. Files are decoded
as cp1250 (latin-1 fallback).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Bank",
    "depends": ["account_statement_import_file", "account_gpc_base"],
    "installable": True,
}
