# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Health monthly advances (dávka 514)",
    "version": "19.0.1.1.0",
    "category": "Human Resources/Payroll",
    "countries": ["sk"],
    "summary": "Monthly Slovak health-insurance advances statement (Mesačný "
               "výkaz preddavkov na poistné, dávka 514) for VšZP / Dôvera / "
               "Union — employer header + per-employee rows, well-formed + "
               "structurally checked XML. Engine-neutral (payroll or the "
               "hr_payroll engine).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
        "l10n_sk_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/davka514_templates.xml",
        "data/davka514_version_data.xml",
        "views/l10n_sk_health_views.xml",
    ],
    "installable": True,
}
