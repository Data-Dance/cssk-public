# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Annual tax reconciliation statement",
    "version": "18.0.1.1.0",
    "category": "Human Resources/Payroll",
    "countries": ["sk"],
    "summary": "Annual Slovak employer income-tax report (§ 39 "
               "ods. 9) for the Finančná správa — aggregate wrap-up + full "
               "per-employee annex (Part V), XML validated against the "
               "official rh2023 schema. Engine-neutral (payroll or the "
               "hr_payroll engine).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/hlasenie_templates.xml",
        "data/hlasenie_version_data.xml",
        "views/l10n_sk_hlasenie_views.xml",
    ],
    "installable": True,
}
