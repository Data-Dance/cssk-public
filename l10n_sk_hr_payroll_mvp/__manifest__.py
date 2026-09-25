# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — MVP (Mesačný výkaz poistného a príspevkov)",
    "version": "19.0.1.0.3",
    "category": "Human Resources/Payroll",
    "countries": ["sk"],
    "summary": "Monthly Slovak social-insurance statement (MVP/MVPP) for the "
               "Sociálna poisťovňa — aggregate summary + per-employee annex, "
               "XML validated against MVPP-v2026.xsd. Engine-neutral ("
               "payroll or the hr_payroll engine).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/mvpp_templates.xml",
        "data/mvpp_version_data.xml",
        "views/l10n_sk_mvp_views.xml",
    ],
    "installable": True,
}
