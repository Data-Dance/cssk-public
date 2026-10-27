---
title: Slovak Accounting Localization — full suite
summary: Installs the Slovak statutory localization in one step, offers the optional pieces as switches in the settings, and cross-checks the VAT filings with each other and with the ledger.
verified: 19.0.1.4.3
---

## What it is for {#purpose}

The Slovak localization is split into many modules so that each company
installs only what it needs. This module is the one-click way in: installing
it brings the statutory core for a Slovak company and adds switches for the
optional parts. It also adds three **cross-checks** between the VAT filings
and the ledger.

## What it installs {#contents}

| Area | Module |
|---|---|
| Shared core: settings, tax offices, filing life cycle | [module:l10n_cssk_core](module:l10n_cssk_core) |
| Slovak statutory base | [module:l10n_sk_statutory](module:l10n_sk_statutory) |
| VAT return (*daňové priznanie k DPH*) | [module:l10n_sk_vat_return](module:l10n_sk_vat_return) |
| Control statement (*kontrolný výkaz DPH*) | [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph) |
| EC sales list (*súhrnný výkaz*) | [module:l10n_sk_ec_sales](module:l10n_sk_ec_sales) |
| Slovak invoice layout | [module:l10n_sk_invoice](module:l10n_sk_invoice) |
| Partner balances and offsetting (*saldokonto*, *zápočet*) | [module:l10n_cssk_partner_balances](module:l10n_cssk_partner_balances) |
| VIES check of EU VAT numbers | [module:l10n_cssk_vies](module:l10n_cssk_vies) |
| Accruals (*dohadné položky*) | [module:l10n_cssk_accrual](module:l10n_cssk_accrual) |
| Stock-taking records (*inventarizácia*) | [module:l10n_sk_inventory_verification](module:l10n_sk_inventory_verification) |

Each of these modules has its own guide.

## Optional pieces {#setup}

*Accounting → Configuration → Settings*, block **Czech / Slovak
Localization**. Tick a switch and save: Odoo installs the module. Unticking
it uninstalls the module again.

| Switch (Slovak label) | Installs | Notes |
|---|---|---|
| Synchronizácia kurzov (NBS/ECB) | [module:currency_rate_update_sk](module:currency_rate_update_sk) | daily NBS/ECB rates and bank rates; Community only |
| Časové rozlíšenie | [module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff) | prepaid and deferred expenses and revenues (381–385); Community only |
| Kontrola spoľahlivosti dodávateľa | [module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability) | checks the supplier's registered bank account before you pay |
| Dvojité odpisovanie | [module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) | tax depreciation alongside accounting depreciation |
| Spôsob A evidencie zásob | `l10n_sk_stock_account_method_a` | perpetual inventory accounting (*spôsob A*); delivered in a separate repository |
| Zálohové faktúry | [module:l10n_sk_sale_order_advance_invoice](module:l10n_sk_sale_order_advance_invoice) | advance invoices and tax documents for received payments |
| Účtovné vzory (interné doklady) | [module:l10n_sk_account_move_template](module:l10n_sk_account_move_template) | named debit/credit templates for internal documents |
| Účtovná závierka | [module:l10n_sk_fiscal_year_closing](module:l10n_sk_fiscal_year_closing) | year-end closing through 710 / 702 and opening through 701 |
| Finančný prenájom | [module:l10n_sk_account_loan_oca](module:l10n_sk_account_loan_oca) | finance lease |
| Protokoly k majetku | [module:l10n_sk_asset_protocol_oca](module:l10n_sk_asset_protocol_oca) | asset commissioning and disposal records |
| Dovoz tovaru (JCD) | [module:l10n_sk_jcd](module:l10n_sk_jcd) | customs declarations for imports |
| Vozidlá a PHL | [module:l10n_sk_vehicle_expense](module:l10n_sk_vehicle_expense) | vehicles and fuel |
| Manažérske výkazy | [module:l10n_sk_mis_reports](module:l10n_sk_mis_reports) | management P&L on MIS Builder; not a statutory statement |
| Vyťažovanie faktúr (AI) | [module:account_invoice_ai_extract](module:account_invoice_ai_extract) | reading incoming PDF invoices into draft bills |
| Účtovná závierka (Súvaha, VZS) | [module:l10n_sk_fs](module:l10n_sk_fs) | balance sheet and profit and loss account for the register of financial statements |
| Daňové priznanie DPPO | [module:l10n_sk_dppo](module:l10n_sk_dppo) | corporate income-tax return |

With both the financial statements and the income-tax return installed,
[module:l10n_sk_dppo_fs](module:l10n_sk_dppo_fs) installs itself and ties
the accounting result to the tax return.

On Odoo Enterprise the exchange-rate and deferral switches are hidden, because
Enterprise has its own.

## Cross-checks between filings {#reconciliation}

Three buttons appear on the filing forms once a filing has been computed
(state other than draft). Each one creates or refreshes a comparison on the
*Filed vs computed* screens described in
[module:l10n_cssk_core](module:l10n_cssk_core), with the result per row and
room for the accountant's answer.

| On the form of | Button | Compares |
|---|---|---|
| Control statement (KV DPH) | *Porovnať s priznaním* | the KV with the VAT return of the same period |
| EC sales list | *Porovnať s priznaním* | the EC sales list with the VAT return of the same period |
| VAT return | *Porovnať s účtovníctvom* | the VAT return with account 343 and account class 60 |

The VAT return used is a computed or exported one of the same company whose
period overlaps — an exact period match first. If there is none, the button
says so; compute the return first.

**KV and VAT return.** The control statement never contains all of the
return — sales to non-taxable persons, simplified invoices and similar
supplies are on the return only — so the KV must be **contained in** the
return, not equal to it:

| Block | KV sections | Return rows |
|---|---|---|
| Output VAT | A.1 + C.1 | r. 02 + 02a + 04 |
| Self-assessed VAT | B.1 | r. 06, 06a, 08, 10, 10a, 10b, 12, 12a – 12e |
| Deducted VAT | B.2 + B.3.1 + B.3.2 + C.2 | r. 18 + 18a + 19 |

A smaller KV figure is shown as *Difference is expected*. A **larger** KV
figure is impossible and is reported as a difference, with a hint to check the
classification of the supplies.

**EC sales list and VAT return.** Goods supplied to another member state
(transaction code 0) must equal row 14. Triangular trade (code 1) and services
(code 2) have no row of their own in the return and are not compared.

**VAT return and ledger.**

| Row | Compared with | Result |
|---|---|---|
| Output VAT, r. 17 | VAT booked on sales taxes in the period | difference if they do not agree |
| Deducted VAT, r. 18 + 18a + 19 | VAT booked on purchase taxes in the period | difference if they do not agree |
| Taxable base, r. 01 + 01a + 03 + 13 | credit turnover of account class 60 | always informational |

The base and the revenue legitimately differ (advance payments, accruals,
acquisitions, financial income), so that row is never a finding.

A tolerance of € 0.50 or 0.1 % of the compared amount, whichever is larger,
applies everywhere.

## Limitations {#limitations}

- The cross-checks are advisory. They do not block exporting or filing.
- The KV check assumes full deduction; with a coefficient (*koeficient*) the
  deducted VAT blocks will not agree.
- The ledger check splits VAT into output and input by the tax's type (sale or
  purchase). Under domestic reverse charge, where one invoice carries both,
  the split is approximate.
- A switch for a module that is not on the server (Method A, the financial
  statements, the income-tax return) does nothing.
- Uninstalling this module does not uninstall what it brought in.
- The setting help for *Spôsob A evidencie zásob* says perpetual inventory is
  required for audited companies; this guide does not confirm that statement.
