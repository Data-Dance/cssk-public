# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic — ELDP (Pension Insurance Record)",
    "version": "19.0.1.0.2",
    "category": "Human Resources/Payroll",
    "countries": ["cz"],
    "summary": "Annual Czech pension-insurance record (ELDP) for the ČSSZ — "
               "per-employee assessment base and days aggregated over the "
               "calendar year, XML validated against the official ELDP09.xsd. "
               "Engine-neutral (payroll or hr_payroll).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/eldp_templates.xml",
        "data/eldp_version_data.xml",
        "views/l10n_cz_eldp_views.xml",
    ],
    "installable": True,
}
