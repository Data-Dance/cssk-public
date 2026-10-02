# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Bank Statement Import — KB BEST",
    "version": "19.0.1.0.0",
    "summary": "Import Komerční banka BEST electronic statements (*.OKM).",
    "description": """
Bank Statement Import — KB BEST
===============================

Imports Komerční banka's **BEST** electronic statements (``*.OKM`` /
``*.KMO`` from MojeBanka Business, Profibanka, Přímý kanál) through the OCA
statement import framework. The record layout lives in
``account_kb_best_base``.

* One statement per account and booking day (turnover record ``51``), with
  the opening and closing balance; the accounting transactions (``52``)
  become statement lines, the non-accounting ones (``53``) are skipped.
* VS/KS/SS into the statement line's symbol fields when
  ``l10n_cssk_payment_symbols`` is installed, and always into the label.
* The journal is found from the statement's account whether the journal holds
  it as IBAN or as ``prefix-number/0100``.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Bank",
    "depends": ["account_statement_import_file", "account_kb_best_base"],
    "installable": True,
}
