# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Bank Statement Import — MT940 / MultiCash (CZ)",
    "version": "19.0.1.0.0",
    "summary": "Import SWIFT MT940 statements (MultiCash *.STA) with the Czech "
               "VS/KS/SS and counterparty subfields.",
    "description": """
Bank Statement Import — MT940 / MultiCash (CZ)
==============================================

Imports the SWIFT **MT940** statements Czech banks deliver through MultiCash
(``*.STA``), X-business and Business 24, through the OCA statement import
framework. The parser lives in ``account_mt940_base``.

* ``:25:`` account in the bank's national form (``0800/192000145399``) or as an
  IBAN — matched to the bank journal whichever way the journal stores it.
* ``:60F:``/``:62F:`` balances, ``:28:``/``:28C:`` statement number, statements
  continued over several messages (``:60M:``) folded back into one.
* ``:61:`` with the optional booking date and ``RC``/``RD`` reversals.
* ``:86:`` in the structured ``?NN`` layout (Česká spořitelna, Raiffeisenbank):
  **VS/KS/SS**, counterparty account and name, remittance text. Free-text
  ``:86:`` from other banks is kept as the label.

The symbols are written to the statement line's ``variable_symbol`` /
``constant_symbol`` / ``specific_symbol`` when a module provides them
(``l10n_cssk_payment_symbols``) and always kept as ``VS:``-style tokens in
the label.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Bank",
    "depends": [
        "account_statement_import_file",
        "account_mt940_base",
        "account_cz_bankfile_base",
    ],
    "installable": True,
}
