# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ/SK Payroll e-Reporting — Declaration Base",
    "version": "19.0.1.4.3",
    "category": "Human Resources/Payroll",
    "summary": "Engine-neutral base for Czech/Slovak payroll authority "
               "e-submissions: XSD-validated XML export, a submission state "
               "machine and an hr.payslip adapter that works on both the "
               "payroll and the hr_payroll engines.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "hr",
        "mail",
        "l10n_cssk_submission_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/cssk_payroll_declaration_version_views.xml",
        "views/cssk_payroll_declaration_menus.xml",
    ],
    "installable": True,
}
