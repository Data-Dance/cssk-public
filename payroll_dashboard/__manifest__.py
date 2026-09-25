# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payroll Dashboard (lightweight)",
    "version": "19.0.1.1.0",
    "category": "Human Resources/Payroll",
    "summary": "A lightweight graph + pivot dashboard of payroll headline "
    "figures (gross, net, employer cost, income tax) per period and employee, "
    "for the community payroll app.",
    "author": "Data Dance s.r.o.",
    "website": "https://datadance.eu",
    "license": "AGPL-3",
    "depends": [
        "payroll",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/payroll_kpi_views.xml",
        "views/payroll_dashboard_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
