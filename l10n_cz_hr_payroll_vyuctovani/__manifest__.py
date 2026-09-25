# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "Czech Republic — Annual Tax Settlement Statement (DPZVD6)",
    "version": "19.0.1.0.1",
    "category": "Human Resources/Payroll",
    "countries": ["cz"],
    "summary": "Annual Czech income-tax reconciliation (annual tax settlement "
               "statement, DPZVD6) for the Finanční správa — advance "
               "income tax aggregated over the year, EPO XML validated against "
               "the official dpzvd6_epo2.xsd. Engine-neutral.",
    "author": "Data Dance s.r.o.",
    "website": "https://github.com/Data-Dance/l10n_cssk",
    "license": "AGPL-3",
    "depends": [
        "l10n_cssk_payroll_declaration_base",
    ],
    "data": [
        "security/ir.model.access.csv",
        "report/vyuctovani_templates.xml",
        "data/vyuctovani_version_data.xml",
        "views/l10n_cz_vyuctovani_views.xml",
    ],
    "installable": True,
}
