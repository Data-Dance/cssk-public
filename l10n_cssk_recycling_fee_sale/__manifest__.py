# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Recycling Fee on Sales Orders",
    "version": "19.0.1.0.0",
    "summary": "Price the CZ/SK recycling fee on sale order lines at the order "
    "date, carry it to the invoice, and optionally invoice it as its own line.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_recycling_fee", "account_ecotax_sale"],
    "data": [
        "views/sale_order_views.xml",
        "views/res_config_settings_views.xml",
    ],
    "auto_install": True,
    "installable": True,
}
