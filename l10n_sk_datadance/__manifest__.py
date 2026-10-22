{
    "name": "Slovak Accounting Localization (Data Dance) — full suite",
    "summary": "One-click Slovak statutory localization: installs the core "
               "statutory reporting + invoice modules, with optional workflow "
               "pieces selectable in Settings.",
    "description": """
Slovak Accounting Localization (Data Dance) — meta-module
=========================================================

Installs the **Slovak statutory core** in one step:

* KV DPH (control statement), Súhrnný výkaz (EC sales list), DPH priznanie
  (VAT return), Súvaha + VZS (financial statements), DPPO (income tax),
  SK invoice, VIES, saldokonto + zápočet, dohadné (accruals).

Optional pieces (FX sync, deferrals, the guarantor-liability check, dual
depreciation, Method A, advance invoices) are **selectable in
Settings → Accounting → Slovak localization** — tick to install.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "18.0.1.1.0",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": [
        "l10n_sk",
        "l10n_cssk_core",
        "l10n_sk_statutory",
        "l10n_sk_kv_dph",
        "l10n_sk_ec_sales",
        "l10n_sk_vat_return",
        "l10n_sk_fs",
        "l10n_sk_invoice",
        "l10n_sk_dppo",
        "l10n_cssk_partner_balances",
        "l10n_cssk_vies",
        "l10n_cssk_accrual",
        # § 29 zákona 431/2002 makes inventarizácia mandatory for every účtovná
        # jednotka. Safe as a hard dependency: proprietary, like every other
        # entry here — see the licence note in models/res_config_settings.py.
        "l10n_sk_inventory_verification",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/cssk_control_statement_views.xml",
        "views/reconciliation_buttons.xml",
    ],
    "installable": True,
}
