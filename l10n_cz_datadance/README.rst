=======================================================
Czech Accounting Localization (Data Dance) — full suite
=======================================================

One-click Czech statutory localization — installs the core reporting and
invoice modules, with optional workflow pieces selectable in Settings.

This is a meta-module: installing it pulls in the whole Czech statutory core in
a single step, so a fresh Czech company is reporting-ready without hand-picking
individual technical modules. On top of the core it adds a Czech localization
panel in **Settings → Accounting** where optional workflow pieces can be ticked
on and installed on demand.

Features
========

* Installs the Czech statutory core in one dependency: Kontrolní hlášení
  (DPHKH1), souhrnné hlášení (DPHSHV), přiznání k DPH (DPHDP3), the financial
  statements (Rozvaha + Výsledovka), the DPPDP9 income-tax return, the CZ
  invoice layout, VIES validation, saldokonto with zápočet (partner balances),
  and dohadné položky (accruals).
* Adds a **Czech localization** section under Settings → Accounting with
  install toggles for optional workflow modules.
* Optional: ČNB exchange-rate synchronization (``module_currency_rate_update_cz``).
* Optional: Časové rozlišení / deferrals (``module_l10n_cz_account_cutoff``).
* Optional: supplier reliability check against ADIS before paying
  (``module_l10n_cz_payment_reliability``).
* Optional: dual tax/accounting depreciation
  (``module_l10n_cz_account_asset_tax``).
* Optional: Method A perpetual inventory
  (``module_l10n_cz_stock_account_method_a``).
* Optional: advance invoices / zálohové faktury
  (``module_l10n_cz_sale_order_advance_invoice``).

Usage
=====

Install the module on the Czech company. The full statutory core is brought in
automatically — no further selection is required for the mandatory reporting and
invoicing pieces.

To enable optional workflow pieces, open **Settings → Accounting → Czech
localization**. Each toggle corresponds to one optional module:

* **ČNB exchange-rate sync** — pulls daily rates from the Czech National Bank.
* **Časové rozlišení (deferrals)** — time-based revenue/expense cut-off.
* **Supplier reliability check (ADIS)** — verify a supplier before paying.
* **Dual tax/accounting depreciation** — separate tax and accounting books.
* **Method A perpetual inventory** — perpetual stock accounting.
* **Advance invoices (zálohové faktury)** — advance-payment invoicing.

Tick a box and save; Odoo installs the corresponding module. These toggles live
on the Settings page itself — there is no separate pop-up wizard to launch.

Credits
=======

* Data Dance s.r.o. <https://www.datadance.eu>

License: AGPL-3.0 or later (see the LICENSE file).
