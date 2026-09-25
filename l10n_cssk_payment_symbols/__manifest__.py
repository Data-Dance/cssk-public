# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Payment Symbols (VS/KS/SS)",
    "version": "19.0.1.2.0",
    "summary": "Variable, constant and specific payment symbols on invoices, "
               "credit notes and bank statement lines.",
    "description": """
CZ/SK Payment Symbols (VS/KS/SS)
================================

Canonical home of the Czech/Slovak payment symbols. Depends on Odoo core
``account`` only, so it installs standalone on Community and Enterprise.

* ``account.move``: ``l10n_cssk_variable_symbol`` (computed — digits of the
  document number, capped at 10; credit notes follow a company policy: own
  number or the original invoice's symbol), ``l10n_cssk_constant_symbol``
  (company default on customer documents) and ``l10n_cssk_specific_symbol``,
  all validated digits-only (10/4/10).
* Optional company toggle: use the variable symbol as the invoice's
  ``payment_reference`` on posting — core QR codes, UBL payment IDs and bank
  matching then carry the VS with no further glue.
* ``account.bank.statement.line``: ``variable_symbol`` / ``constant_symbol``
  / ``specific_symbol``, extracted on create from explicit values, the bank
  connector's ``transaction_details`` (including the ``variable_code`` key
  used by odoo/odoo#275611) or ``VS:``-style tokens in the label; the
  variable symbol is prefixed into ``payment_ref`` (``"<vs> - <label>"``,
  never twice) so stock matching heuristics see it. Field names and
  semantics are deliberately compatible with upstream PR odoo/odoo#275611.
* QR integration: invoices pass their symbols to the QR generator via
  context (``cssk_payment_symbols``) — consumed by the Data Dance QR modules
  (QR Platba CZ, PAY by square, payme.sk).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account"],
    "data": [
        "views/account_move_views.xml",
        "views/account_payment_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
