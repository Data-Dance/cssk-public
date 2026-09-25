# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Payroll Worked Days & Inputs Timeline",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Payroll",
    "summary": "Timeline and pivot views of payslip worked days and inputs, "
    "per employee over time — a community alternative to the Enterprise "
    "work-entries gantt for reviewing the inputs used in payroll calculation.",
    "author": "Data Dance s.r.o.",
    "website": "https://datadance.eu",
    "license": "AGPL-3",
    "depends": [
        "payroll",
        "web_timeline",
    ],
    "data": [
        "views/hr_payslip_worked_days_views.xml",
        "views/hr_payslip_input_views.xml",
    ],
    "installable": True,
    "auto_install": False,
}
