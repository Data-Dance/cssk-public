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
  (VAT return), SK invoice, VIES, saldokonto + zápočet, dohadné (accruals),
  inventarizácia.

Further pieces (FX sync, deferrals, the guarantor-liability check, dual
depreciation, Method A, advance invoices, and the annual filings — Súvaha +
VZS and DPPO) are **selectable in Settings → Accounting → Slovak
localization** — tick to install.
""",
    "author": "Data Dance s.r.o.",
    "website": "https://www.datadance.eu",
    "version": "19.0.1.4.3",
    "category": "Accounting/Localizations",
    "license": "AGPL-3",
    "depends": [
        "l10n_sk",
        "l10n_cssk_core",
        "l10n_sk_statutory",
        "l10n_sk_kv_dph",
        "l10n_sk_ec_sales",
        "l10n_sk_vat_return",
        "l10n_sk_invoice",
        "l10n_cssk_partner_balances",
        "l10n_cssk_vies",
        "l10n_cssk_accrual",
        # § 29 zákona 431/2002 makes inventarizácia mandatory for every účtovná
        # jednotka as at the závierka date, so it belongs in the core bundle.
        "l10n_sk_inventarizacia",
    ],
    "data": [
        "security/ir.model.access.csv",
        "views/res_config_settings_views.xml",
        "views/cssk_control_statement_views.xml",
        "views/reconciliation_buttons.xml",
    ],
    "installable": True,
}
