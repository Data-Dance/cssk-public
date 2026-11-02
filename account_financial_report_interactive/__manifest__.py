# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Interactive General Ledger and Trial Balance",
    "version": "19.0.1.5.0",
    "summary": "Open the OCA general ledger and trial balance interactively: "
               "unfold an account to load its journal items, a page at a time.",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Reporting",
    "depends": ["account_financial_report"],
    "data": [
        "security/ir.model.access.csv",
        "security/ir_rule.xml",
        "views/report_wizard_views.xml",
        "views/saved_view_views.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "account_financial_report_interactive/static/src/**/*",
        ],
    },
    "installable": True,
}
