{
    "name": "Tax Depreciation - Slovak Localization",
    "version": "19.0.1.0.3",
    "summary": "Slovak tax depreciation groups and coefficients (zákon 595/2003 Z.z. §26–28)",
    "description": """
Slovak tax depreciation groups
==============================

Loads the seven Slovak depreciation groups (odpisové skupiny 0–6) with the
straight-line regime (§27, monthly pro-rata in year one) and the accelerated
coefficients (§28, groups 2 & 3 only), as verified against the 2026 consolidated
text of zákon 595/2003 Z.z.

Requires a bridge (``account_asset_tax_ee`` or ``account_asset_tax_oca``)
to attach the tax board to actual assets.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Localizations",
    "depends": ["account_asset_tax", "l10n_sk"],
    "data": [
        "data/account_asset_tax_class_data.xml",
    ],
    "auto_install": False,
    "installable": True,
}
