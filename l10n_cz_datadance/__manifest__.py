{
    "name": "Czech Accounting Localization (Data Dance) — full suite",
    "summary": "One-click Czech statutory localization: installs the core "
               "statutory reporting + invoice modules, with optional workflow "
               "pieces selectable in Settings.",
    "description": """
Czech Accounting Localization (Data Dance) — meta-module
========================================================

Installs the **Czech statutory core** in one step:

* Kontrolní hlášení (DPHKH1), souhrnné hlášení (DPHSHV), přiznání k DPH
  (DPHDP3), CZ invoice, VIES, saldokonto + zápočet, dohadné (accruals).

Further pieces (dual depreciation, Method A, advance invoices, and the annual
filings — Rozvaha + Výsledovka and DPPDP9) are selectable in
**Settings → Accounting → Czech localization** — tick to install.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.1.1",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": [
        "l10n_cz",
        "l10n_cssk_core",
        "l10n_cz_statutory",
        "l10n_cz_kh",
        "l10n_cz_ec_sales",
        "l10n_cz_vat_return",
        "l10n_cz_invoice",
        "l10n_cssk_partner_balances",
        "l10n_cssk_vies",
        "l10n_cssk_accrual",
    ],
    "data": [
        "views/res_config_settings_views.xml",
    ],
    "installable": True,
}
