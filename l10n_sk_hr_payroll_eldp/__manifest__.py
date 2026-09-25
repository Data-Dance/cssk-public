# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — ELDP (Evidenčný list dôchodkového poistenia)",
    "version": "19.0.1.0.2",
    "category": "Human Resources/Payroll",
    "countries": ["sk"],
    "summary": "Annual per-employee Slovak pension record (ELDP) filed to the "
               "Sociálna poisťovňa — aggregates each year's pension assessment "
               "base and insured period per employee, XML validated against "
               "ELDP-v2015_1.3.xsd. Engine-neutral (payroll or the "
               "hr_payroll engine).",
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
        "views/l10n_sk_eldp_views.xml",
    ],
    "installable": True,
}
