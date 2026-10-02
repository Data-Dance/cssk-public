# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "EU NACE: Rev. 2.1 and the Czech subclasses",
    "summary": "NACE Rev. 2.1 industries with the CZ-NACE 2025 fifth digit, "
    "linked to the partner's NACE code",
    "version": "19.0.1.0.0",
    "category": "Hidden/Tools",
    "license": "AGPL-3",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "depends": ["l10n_eu_nace", "partner_nace"],
    "data": [
        "views/res_partner_industry_views.xml",
        "views/res_partner_industry_eu_nace_wizard_views.xml",
    ],
    "post_init_hook": "post_init_hook",
    "auto_install": True,
    "installable": True,
}
