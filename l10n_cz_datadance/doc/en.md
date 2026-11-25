---
title: Czech Accounting Localization — full suite
summary: Installs the Czech statutory localization in one step and offers the optional pieces as switches in the settings, and cross-checks the VAT filings with each other and with the ledger.
verified: 19.0.1.4.0
---

## What it is for {#purpose}

The Czech localization is split into many modules so that each company
installs only what it needs. This module is the one-click way in: installing
it brings the statutory core for a Czech company, and adds switches for the
optional parts. It also adds three **cross-checks** between the VAT filings
and the ledger (see [below](#reconciliation)).

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
| Stock-taking records (*inventarizace*) | [module:l10n_cz_inventory_verification](module:l10n_cz_inventory_verification) |

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
| Účetní vzory (interní doklady) | [module:l10n_cz_account_move_template](module:l10n_cz_account_move_template) | named debit / credit templates for internal documents |
| Účetní závěrka | [module:l10n_cz_fiscal_year_closing](module:l10n_cz_fiscal_year_closing) | year-end closing through 710 / 702, opening through 701 with the result on 431 |
| Protokoly k majetku | [module:l10n_cz_asset_protocol_oca](module:l10n_cz_asset_protocol_oca) | commissioning and disposal protocols for fixed assets |
| Manažerské výkazy | [module:l10n_cz_mis_reports](module:l10n_cz_mis_reports) | management profit and loss on MIS Builder; not a statutory statement |
| Vytěžování faktur (AI) | `account_invoice_ai_extract` | reads vendor bills from PDF; delivered to subscribers |
| Účetní závěrka (Rozvaha, VZZ) | [module:l10n_cz_fs](module:l10n_cz_fs) | balance sheet and profit and loss account |
| Přiznání k dani z příjmů (DPPDP9) | [module:l10n_cz_dppo](module:l10n_cz_dppo) | corporate income-tax return |

On Odoo Enterprise the exchange-rate and deferral switches are hidden, because
Enterprise has its own automatic exchange rates and deferred revenue and
expense.

## Cross-checks between filings {#reconciliation}

Before filing, three buttons compare the VAT filings of a Czech company with
each other and with the ledger. Each opens the comparison screen of
[module:l10n_cssk_core](module:l10n_cssk_core), where every row keeps its
figures, its state and your note across later runs.

| Where | Button | What is compared |
|---|---|---|
| Kontrolní hlášení | *Porovnat s přiznáním* | the eight control rows of the hlášení with the rows of the přiznání |
| Souhrnné hlášení | *Porovnat s přiznáním* | the hlášení by code with ř. 20, 21 and 31 |
| Přiznání k DPH | *Porovnat s účetnictvím* | the tax of the přiznání with account 343 |

The buttons appear once the filing is computed. The first two need a
computed přiznání covering the same period.

**Kontrolní hlášení ↔ přiznání.** The hlášení ends with control rows, and
the Financial Administration's structure states which row of the přiznání
each must agree with, within 1 000 Kč:

| Control row | Kontrolní hlášení | Přiznání |
|---|---|---|
| obrat23 / obrat5 | bases of A.4 + A.5, standard / reduced rate | ř. 1 / ř. 2 |
| pln23 / pln5 | bases of B.2 + B.3, standard / reduced rate | ř. 40 / ř. 41 |
| pln_rez_pren | base of A.1 | ř. 25 |
| rez_pren23 / rez_pren5 | bases of B.1, standard / reduced rate | ř. 10 / ř. 11 |
| celk_zd_a2 | bases of A.2 | ř. 3 + 4 + 5 + 6 + 9 + 12 + 13 |

A difference above 1 000 Kč is reported as a difference.

**Souhrnné hlášení ↔ přiznání.** The instructions of the přiznání send three
rows to the souhrnné hlášení: ř. 20 with codes 0 and 1 (goods and transfers
of own goods), ř. 21 with code 3 (services under § 9 odst. 1) and ř. 31 with
code 2 (the middle party of a triangular trade).

**Quarterly payers.** Where the přiznání covers a quarter and the hlášení a
month, the hlášení of all three months are added before comparing. If one of
them is not computed, the rows are shown as *informational* with a note, not
as differences.

**Přiznání ↔ ledger.**

| Row | Přiznání | Ledger |
|---|---|---|
| Daň na výstupu | ř. 62 | output tax booked on 343 by tax lines, including the self-assessed tax of reverse charge and acquisitions |
| Odpočet daně | ř. 46, both columns | deduction booked on 343 by tax lines |
| Pohyby na účtu 343 mimo daňové řádky | — | what moved on 343 with no tax behind it: payments to and from the tax office, and anything booked by hand |
| Uskutečněná plnění ↔ tržby | ř. 1, 2, 20–26 | credit turnover of account group 60; for orientation only |

The first two must agree within 20 Kč (each row of the přiznání is rounded
to whole crowns on its own). The last two are informational: look at the
third when it is not explained by payments of the tax.

## Limitations {#limitations}

- The cross-checks are advisory. They do not block exporting or filing.
- The cross-checks read what is computed in Odoo. They cannot see a filing
  made elsewhere, and the ledger check reads account 343 by its code.
- The coefficient rows of the přiznání (52, 53, 60) are not compared with
  the ledger; no tax line books them.
- A switch for a module that is not on the server (Method A, the financial
  statements and the income-tax return are delivered separately) does
  nothing.
- Uninstalling this module does not uninstall what it brought in.
- The setting help for *Method A inventory* says perpetual inventory is
  required for audited companies; this guide does not confirm that statement.
