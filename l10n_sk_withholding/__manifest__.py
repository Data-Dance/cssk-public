{
    "name": "Slovakia — Withholding tax notice 4311",
    "version": "19.0.1.0.0",
    "category": "Accounting/Localizations/Reporting",
    "summary": "Native-ledger dividend and author withholding notices with Annex A",
    "author": "Data Dance s.r.o., votrelec",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "countries": ["sk"],
    "depends": ["l10n_sk_base", "l10n_cssk_submission_base"],
    "external_dependencies": {"python": ["stdnum"]},
    "data": [
        "security/ir.model.access.csv",
        "security/rules.xml",
        "views/withholding.xml",
    ],
    "installable": True,
}
