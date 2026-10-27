---
title: Czech Accounting Localization — full suite
summary: Installs the Czech statutory localization in one step and offers the optional pieces as switches in the settings.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

The Czech localization is split into many modules so that each company
installs only what it needs. This module is the one-click way in: installing
it brings the statutory core for a Czech company, and adds switches for the
optional parts. It has no screens or data of its own.

## What it installs {#contents}

| Area | Module |
|---|---|
| Shared core: settings, tax offices, filing life cycle | [module:l10n_cssk_core](module:l10n_cssk_core) |
| Czech statutory base | [module:l10n_cz_statutory](module:l10n_cz_statutory) |
| VAT return (*přiznání k DPH*, DPHDP3) | [module:l10n_cz_vat_return](module:l10n_cz_vat_return) |
| Control statement (*kontrolní hlášení*, DPHKH1) | [module:l10n_cz_kh](module:l10n_cz_kh) |
| EC sales list (*souhrnné hlášení*, DPHSHV) | [module:l10n_cz_ec_sales](module:l10n_cz_ec_sales) |
| Czech invoice layout | [module:l10n_cz_invoice](module:l10n_cz_invoice) |
| Partner balances and offsetting (*saldokonto*, *zápočet*) | [module:l10n_cssk_partner_balances](module:l10n_cssk_partner_balances) |
| VIES check of EU VAT numbers | [module:l10n_cssk_vies](module:l10n_cssk_vies) |
| Accruals (*dohadné položky*) | [module:l10n_cssk_accrual](module:l10n_cssk_accrual) |

Each of these modules has its own guide.

## Optional pieces {#setup}

*Accounting → Configuration → Settings*, block **Czech / Slovak
Localization**. Tick a switch and save: Odoo installs the module. Unticking
it uninstalls the module again.

| Switch | Installs | Notes |
|---|---|---|
| Exchange-rate sync (ČNB) | [module:currency_rate_update_cz](module:currency_rate_update_cz) | daily rates of the Czech National Bank; Community only |
| Časové rozlišení (deferrals) | [module:l10n_cz_account_cutoff](module:l10n_cz_account_cutoff) | prepaid and deferred expenses and revenues (381–385); Community only |
| Supplier reliability check | [module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) | checks an unreliable VAT payer and the published bank account before you pay |
| Dual depreciation | [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax) | tax depreciation alongside accounting depreciation |
| Method A inventory | `l10n_cz_stock_account_method_a` | perpetual inventory accounting (*způsob A*); delivered in a separate repository |
| Advance invoices | [module:l10n_cz_sale_order_advance_invoice](module:l10n_cz_sale_order_advance_invoice) | *zálohové faktury* and tax documents for received payments |
| Účetní závěrka (Rozvaha, VZZ) | [module:l10n_cz_fs](module:l10n_cz_fs) | balance sheet and profit and loss account |
| Přiznání k dani z příjmů (DPPDP9) | [module:l10n_cz_dppo](module:l10n_cz_dppo) | corporate income-tax return |

On Odoo Enterprise the exchange-rate and deferral switches are hidden, because
Enterprise has its own automatic exchange rates and deferred revenue and
expense.

## Limitations {#limitations}

- A switch for a module that is not on the server (Method A, the financial
  statements and the income-tax return are delivered separately) does
  nothing.
- Uninstalling this module does not uninstall what it brought in.
- The setting help for *Method A inventory* says perpetual inventory is
  required for audited companies; this guide does not confirm that statement.
