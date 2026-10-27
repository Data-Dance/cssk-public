{
    "name": "Tax Depreciation (CZ/SK dual depreciation core)",
    "version": "19.0.1.11.0",
    "summary": "Country-neutral engine for a second, non-posted tax-depreciation "
               "board alongside accounting depreciation (daňové vs účetní/účtovné odpisy)",
    "description": """
Tax Depreciation — dual depreciation core
==========================================

Czech and Slovak income-tax law requires every depreciable asset to carry **two**
parallel depreciation plans:

* **Accounting depreciation** (účetní / účtovné odpisy) — the company's own plan,
  posted to the general ledger (account 551).
* **Tax depreciation** (daňové odpisy) — statutory groups and rates, *never*
  posted; it only adjusts the income-tax base (add-back when accounting > tax:
  SK DPPO r. 150 / CZ DPPO ř. 50; deduction when tax > accounting: SK r. 250 /
  CZ ř. 150).

This module provides the country-neutral core: the statutory depreciation-group
model, the non-posted tax-depreciation board, and a pure-Python calculation
engine implementing:

* CZ — zákon 586/1992 Sb. §31 (rovnoměrné), §32 (zrychlené), §30a (mimořádné)
* SK — zákon 595/2003 Z.z. §27 (rovnomerné), §28 (zrýchlené)

It does **not** itself extend an asset model. Install a bridge:

* ``account_asset_tax_ee`` — for Odoo Enterprise ``account_asset``
* ``account_asset_tax_oca`` — for OCA ``account_asset_management`` (CE)

and a country data layer:

* ``l10n_cz_account_asset_tax`` — Czech groups & coefficients
* ``l10n_sk_account_asset_tax`` — Slovak groups & coefficients
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "license": "AGPL-3",
    "category": "Accounting/Accounting",
    "depends": ["account"],
    "data": [
        "security/ir.model.access.csv",
        "security/record_rules.xml",
        "views/account_asset_tax_class_views.xml",
        "views/res_company_views.xml",
        "views/account_asset_tax_menus.xml",
        "wizard/account_asset_tax_compute_views.xml",
        "wizard/account_asset_tax_event_views.xml",
        "wizard/account_asset_tax_reconciliation_views.xml",
        "wizard/account_asset_tax_backfill_views.xml",
        "wizard/account_asset_tax_close_year_views.xml",
        "report/account_asset_tax_reconciliation_report.xml",
        "report/account_asset_tax_register_report.xml",
        "wizard/account_asset_tax_register_views.xml",
    ],
    "installable": True,
}
