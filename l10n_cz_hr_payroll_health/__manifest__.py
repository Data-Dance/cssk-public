# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic — Health Insurance (PPPZ + HOZ)",
    "version": "19.0.1.1.0",
    "category": "Human Resources/Payroll",
    "countries": ["cz"],
    "summary": "Czech health-insurance employer e-filings — monthly premium "
               "overview (PPPZ, payslip-aggregate) and bulk employee "
               "enrol/terminate notification (HOZ, employee lifecycle), per "
               "health insurer, validated against the official VZP/ZP XSDs. "
               "Engine-neutral (payroll or hr_payroll).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/pppz_templates.xml",
        "report/hoz_templates.xml",
        "data/health_version_data.xml",
        "views/l10n_cz_pppz_views.xml",
        "views/l10n_cz_hoz_views.xml",
    ],
    "installable": True,
}
