# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Wage Garnishment — Base",
    "version": "19.0.1.2.1",
    "category": "Human Resources/Payroll",
    "summary": "Engine-neutral register of Czech and Slovak wage-garnishment "
    "orders (exekuční / exekučný príkaz) with the statutory multi-claim "
    "waterfall and the employer's statutory notices.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "hr",
        "mail",
    ],
    "data": [
        "security/ir.model.access.csv",
        "security/hr_wage_garnishment_security.xml",
        "data/hr_wage_garnishment_rate_data.xml",
        "views/hr_wage_garnishment_views.xml",
        "views/hr_wage_garnishment_line_views.xml",
        "views/hr_wage_garnishment_rate_views.xml",
        "views/hr_employee_views.xml",
        "wizard/hr_wage_garnishment_notice_views.xml",
        "report/garnishment_reports.xml",
        "report/report_garnishment_settlement.xml",
        "report/report_garnishment_notice.xml",
        "views/hr_wage_garnishment_menus.xml",
    ],
    "installable": True,
}
