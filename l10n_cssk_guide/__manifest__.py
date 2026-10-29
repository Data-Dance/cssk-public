# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK User Guides",
    "version": "19.0.1.0.0",
    "summary": "One page to start from: the first steps and the guide of every "
               "Czech and Slovak localization module on this server, by topic.",
    "description": """
CZ/SK User Guides
=================

*Accounting → Configuration → Guides* opens the start page of the Czech and
Slovak localization's user guide: the first steps, then the guide of every
module present on this server, sorted by topic (VAT and filings, financial
statements, banking, payroll, …) and marked installed or not.

The page lists what it finds on the server, so it covers every delivery
repository the server has, and shows the modules of the company's country
first.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["l10n_cssk_core"],
    "data": [
        "views/guide_templates.xml",
        "views/guide_menu.xml",
    ],
    "auto_install": True,
    "installable": True,
}
