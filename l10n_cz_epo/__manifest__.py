# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ EPO: check and file through Finanční správa",
    "summary": "Signs Czech statutory filings with the company's qualified "
               "certificate and sends them to EPO — to check (test mode) or "
               "to file — and follows the filing to acceptance.",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_submission_base", "l10n_cz_statutory"],
    "external_dependencies": {"python": ["cryptography", "asn1crypto", "requests"]},
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/l10n_cz_epo_certificate_views.xml",
        "views/cssk_submission_views.xml",
        "views/res_company_views.xml",
    ],
    "installable": True,
}
