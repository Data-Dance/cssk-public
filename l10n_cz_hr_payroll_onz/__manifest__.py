# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic — ONZ (Employment Registration)",
    "version": "19.0.1.0.2",
    "category": "Human Resources/Payroll",
    "countries": ["cz"],
    "summary": "Czech employment registration (ONZ) for the ČSSZ — per-employee "
               "start/end events built from the employee and hr.version "
               "lifecycle, XML validated against the official ONZ2022 XSD.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/onz_templates.xml",
        "data/onz_version_data.xml",
        "views/l10n_cz_onz_views.xml",
    ],
    "installable": True,
}
