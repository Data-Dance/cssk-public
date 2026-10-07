# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Slovakia — Prehľad o zrazených preddavkoch na daň",
    "version": "19.0.2.0.0",
    "category": "Human Resources/Payroll",
    "countries": ["sk"],
    "summary": "Monthly Slovak income-tax overview (Prehľad o zrazených a "
               "odvedených preddavkoch na daň) for the Finančná správa — "
               "withheld tax advances + daňový bonus recap, XML validated "
               "against the official PREHLAD_2026 schema. Engine-neutral ("
               "payroll or the hr_payroll engine).",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
        "l10n_sk_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/prehlad_templates.xml",
        "data/prehlad_version_data.xml",
        "views/l10n_sk_prehlad_views.xml",
    ],
    "installable": True,
}
