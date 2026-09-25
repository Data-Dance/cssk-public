# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Wage Garnishment — payroll engine bridge",
    "version": "19.0.1.0.1",
    "category": "Human Resources/Payroll",
    "summary": "Apply the Czech/Slovak wage-garnishment waterfall on payslips "
    "computed by the OCA payroll engine.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "payroll",
        "l10n_cssk_hr_payroll_garnishment_base",
    ],
    "data": [
        "views/hr_payslip_views.xml",
    ],
    "installable": True,
    "auto_install": True,
}
