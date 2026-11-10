# Copyright 2026 Data Dance s.r.o.
# License AGPL-3.0 or later (https://www.gnu.org/licenses/agpl).
{
    "name": "CZ Data Box (ISDS)",
    "summary": "Signs in to the company's Czech data box and sends and "
               "receives data messages through the operator's web services, "
               "for the filing channels that use it.",
    "version": "19.0.1.1.0",
    "category": "Accounting/Localizations",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "depends": ["l10n_cssk_submission_base"],
    "external_dependencies": {"python": ["requests", "cryptography"]},
    "data": [
        "views/res_company_views.xml",
    ],
    "installable": True,
}
