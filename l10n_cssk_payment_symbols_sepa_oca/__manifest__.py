# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Payment Symbols — SEPA Credit Transfer (OCA)",
    "version": "19.0.1.0.0",
    "summary": "Writes VS, KS and SS into the SEPA credit transfer file of OCA "
               "payment orders, in the form Slovak and Czech banks read.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": [
        "l10n_cssk_payment_symbols_payment_order",
        "account_banking_sepa_credit_transfer",
    ],
    "data": ["views/account_journal_views.xml"],
    "auto_install": True,
    "installable": True,
}
