# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Payment Symbols — Payment Orders",
    "version": "19.0.1.0.0",
    "summary": "Copy invoice VS/KS/SS onto OCA payment order lines.",
    "description": """
CZ/SK Payment Symbols — Payment Orders
======================================

Bridge between ``l10n_cssk_payment_symbols`` and the OCA payment order
framework (``account_payment_order``): when a payment line is created from a
journal item, the document's variable, constant and specific symbols are
copied onto the line's ``variable_symbol`` / ``constant_symbol`` /
``specific_symbol`` fields.

The field declarations are identical to the ones in ``account_abo`` and
``account_multicash`` (Odoo collapses duplicate declarations), so the bank
format exporters get structured symbols without having to parse ``VS:``
tokens out of the communication. No extra UI — the exporter modules already
surface the fields on the payment line views.

Auto-installs when both ``l10n_cssk_payment_symbols`` and
``account_payment_order`` are present.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_payment_symbols", "account_payment_order"],
    "auto_install": True,
    "installable": True,
}
