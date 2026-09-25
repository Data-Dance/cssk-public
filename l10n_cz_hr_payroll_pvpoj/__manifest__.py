# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic — PVPOJ (Social Insurance Overview)",
    "version": "19.0.1.1.1",
    "category": "Human Resources/Payroll",
    "countries": ["cz"],
    "summary": "Monthly Czech social-insurance overview (PVPOJ) for the ČSSZ — "
               "employer-aggregate XML export validated against the official "
               "PVPOJ25.xsd. Engine-neutral (payroll or "
               "hr_payroll).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/pvpoj_templates.xml",
        "data/pvpoj_version_data.xml",
        "views/l10n_cz_pvpoj_views.xml",
    ],
    "installable": True,
}
