# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — RLFO (Registračný list FO)",
    "version": "19.0.1.1.1",
    "category": "Human Resources/Payroll",
    "countries": ["sk"],
    "summary": "Slovak social-insurance registration of employees (RLFO / "
               "RLZEC) filed to the Sociálna poisťovňa — prihláška / odhláška "
               "events built from the employee + hr.version lifecycle, XML "
               "validated against RLZEC-v2026.xsd.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/rlfo_templates.xml",
        "data/rlfo_version_data.xml",
        "views/l10n_sk_rlfo_views.xml",
    ],
    "installable": True,
}
