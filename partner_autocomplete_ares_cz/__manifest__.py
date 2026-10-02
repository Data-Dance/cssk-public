# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Partner Autocomplete using ARES CZ",
    "category": "Tools",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.2.0",
    "post_init_hook": "post_init_hook",
    "summary": """
Completes Partner information using ARES from https://wwwinfo.mfcr.cz/
    """,
    "depends": ["partner_autocomplete_dispatcher"],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "assets": {
        "web.assets_tests": [
            "partner_autocomplete_ares_cz/static/tests/tours/*.js",
        ],
    },
    "installable": True,
    "price": 150.00,
    "currency": "EUR",
}
