# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Cash Payment Limit at the Point of Sale",
    "version": "19.0.1.0.0",
    "summary": "Asks for confirmation before a Point of Sale order takes more "
               "than 5 000 € in cash (zákon č. 394/2012 Z. z.) and flags such "
               "orders in the back office.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_sk_invoice", "point_of_sale"],
    "data": [
        "views/pos_order_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "l10n_sk_pos_cash_limit/static/src/app/**/*",
        ],
        "web.assets_tests": [
            "l10n_sk_pos_cash_limit/static/tests/tours/**/*",
        ],
    },
    "auto_install": True,
    "installable": True,
}
