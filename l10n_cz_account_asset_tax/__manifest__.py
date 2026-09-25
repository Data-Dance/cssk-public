{
    "name": "Tax Depreciation - Czech Localization",
    "version": "19.0.1.0.3",
    "summary": "Czech tax depreciation groups and coefficients (zákon 586/1992 Sb. §30–32)",
    "description": """
Czech tax depreciation groups
=============================

Loads the six Czech depreciation groups (odpisové skupiny) with the straight-line
rates (§31), accelerated coefficients (§32) and the §30a extraordinary regime, as
verified against the 2026 consolidated text of zákon 586/1992 Sb.

Requires a bridge (``account_asset_tax_ee`` or ``account_asset_tax_oca``)
to attach the tax board to actual assets.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account_asset_tax", "l10n_cz"],
    "data": [
        "data/account_asset_tax_class_data.xml",
    ],
    "auto_install": False,
    "installable": True,
}
