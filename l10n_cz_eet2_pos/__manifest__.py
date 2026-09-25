# -*- coding: utf-8 -*-
{
    "name": "Czech EET 2.0 - Point of Sale",
    "summary": "Register Point-of-Sale contact payments with the Czech EET 2.0 "
            "system and print the POK on the receipt.",
    "author": "Data Dance s.r.o.",
    "category": "Accounting/Localizations/Point of Sale",
    "version": "19.0.1.0.0",
    "license": "AGPL-3",
    "depends": [
        "l10n_cz_eet2",
        "point_of_sale",
    ],
    "data": [
        "views/pos_payment_method_views.xml",
        "views/pos_config_views.xml",
        "views/pos_order_views.xml",
    ],
    "assets": {
        "point_of_sale._assets_pos": [
            "l10n_cz_eet2_pos/static/src/overrides/components/**/*",
            "l10n_cz_eet2_pos/static/src/overrides/utils/**/*",
        ],
    },
    "installable": True,
}
