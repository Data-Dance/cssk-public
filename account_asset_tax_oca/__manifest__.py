{
    "name": "Tax Depreciation - OCA bridge",
    "version": "19.0.1.4.4",
    "summary": "Attach the CZ/SK tax-depreciation board to OCA account_asset_management (Community)",
    "description": """
Tax Depreciation — OCA bridge
=============================

Wires the country-neutral ``account_asset_tax`` core onto the OCA
``account_asset_management`` model (the Community-friendly asset framework, no
Enterprise required): it adds the non-posted tax-depreciation board, the
asset ↔ tax-line relation, and the *Tax Depreciation* page on the asset form.

Install together with a country data layer (``l10n_cz_account_asset_tax`` /
``l10n_sk_account_asset_tax``). Mutually exclusive with the Enterprise bridge
``account_asset_tax_ee`` (only one asset implementation can be installed).
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Accounting",
    "depends": ["account_asset_tax", "account_asset_management"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/account_asset_views.xml",
        "views/account_asset_book_tax_report_views.xml",
    ],
    "auto_install": False,
    "installable": True,
}
