# Copyright 2026 votrelec
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Health registration notices (601)",
    "version": "19.0.1.0.0",
    "category": "Human Resources/Payroll",
    "summary": "Published Slovak health-insurance registration batch interfaces",
    "author": "Data Dance s.r.o., votrelec",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "countries": ["sk"],
    "depends": [
        "l10n_cssk_payroll_declaration_base",
        "l10n_sk_base",
        "l10n_sk_hr_payroll_base",
    ],
    "data": [
        "security/registration_security.xml",
        "security/ir.model.access.csv",
        "data/registration_version.xml",
        "views/registration_views.xml",
    ],
    "installable": True,
}
