# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ Invoice: Forma úhrady",
    "summary": "Prints the payment mode as 'Forma úhrady' in the header of "
               "the Czech invoice.",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "depends": ["l10n_cz_invoice", "account_payment_mode"],
    "data": ["report/report_invoice.xml"],
    "auto_install": True,
    "installable": True,
}
