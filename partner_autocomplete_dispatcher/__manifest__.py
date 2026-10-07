# Copyright 2022 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Partner Autocomplete Dispatcher",
    "category": "Tools",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.0",
    "summary": "Technical dispatcher for the partner-autocomplete providers: assigns each dependent "
        "provider module to the companies that should use it.",
    "depends": ["partner_autocomplete", "web"],
    "data": [
        "views/res_config_settings_views.xml",
        "views/res_company_views.xml",
        "views/res_partner_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "partner_autocomplete_dispatcher/static/src/js/*",
        ]
    },
    "installable": True,
}
