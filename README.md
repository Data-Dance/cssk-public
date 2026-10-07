# cssk-public

Czech and Slovak localization for Odoo: statutory accounting, VAT and control-statement filings, payroll, banking formats and company-register lookups. Published by Data Dance s.r.o. as a contribution to the Odoo community.

- [Slovak modules](https://www.datadance.eu/en/moduly/slovensko)
- [Czech modules](https://www.datadance.eu/en/moduly/cesko)
- [Licensing FAQ](https://www.datadance.eu/en/moduly/licencia)

**Generated from a private source repository.**

Every module here is produced from Data Dance's private source
repository, and each sync replaces what is here. A change committed
directly to this repository is lost, not merged.

Pull requests are welcome **here**: we apply an accepted one to the
source, keeping your authorship, and it returns in the next sync.
See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the steps and the
contributor licence agreement.

## Requirements

These modules depend on 24 module(s) that are not in
this repository. Add them to the addons path as well:

| Source | Modules |
|---|---|
| [OCA/account-closing](https://github.com/OCA/account-closing) | `account_cutoff_start_end_dates`, `account_fiscal_year_closing`, `account_multicurrency_revaluation` |
| [OCA/account-financial-tools](https://github.com/OCA/account-financial-tools) | `account_asset_management`, `account_leasing`, `account_move_template` |
| [OCA/account-fiscal-rule](https://github.com/OCA/account-fiscal-rule) | `account_ecotax`, `account_ecotax_sale` |
| [OCA/account-reconcile](https://github.com/OCA/account-reconcile) | `account_reconcile_oca` |
| [OCA/bank-payment](https://github.com/OCA/bank-payment) | `account_banking_sepa_credit_transfer`, `account_payment_mode`, `account_payment_order` |
| [OCA/bank-statement-import](https://github.com/OCA/bank-statement-import) | `account_statement_import_base`, `account_statement_import_camt`, `account_statement_import_file` |
| [OCA/community-data-files](https://github.com/OCA/community-data-files) | `l10n_eu_nace` |
| [OCA/currency](https://github.com/OCA/currency) | `currency_rate_update` |
| [OCA/intrastat-extrastat](https://github.com/OCA/intrastat-extrastat) | `intrastat_product`, `intrastat_product_hscodes_import` |
| [OCA/mis-builder](https://github.com/OCA/mis-builder) | `mis_builder` |
| [OCA/payroll](https://github.com/OCA/payroll) | `payroll`, `payroll_account` |
| [OCA/reporting-engine](https://github.com/OCA/reporting-engine) | `report_xlsx` |
| [OCA/web](https://github.com/OCA/web) | `web_timeline` |

## Modules

166 module(s), grouped by the country or domain they serve. Every one of them is licensed `AGPL-3`.

### Czech Republic (34)

| Module | Version | What it does |
|---|---|---|
| `l10n_cz_account_asset_tax` | 19.0.1.0.3 | Czech tax depreciation groups and coefficients (zákon 586/1992 Sb. §30–32) |
| `l10n_cz_account_cutoff` | 19.0.1.0.1 | Pre-fills the OCA cut-off / deferral default accounts with the Czech 381/383/384/385 accounts so časové rozlišení works out of the box. |
| `l10n_cz_base` | 19.0.2.0.2 | Czech IBAN <-> legacy account number conversion and variable/constant/specific symbols |
| `l10n_cz_cash_journal` | 19.0.1.0.4 | Czech cash journal for daňová evidence (§ 7b ZDP): the členění vendors settled on, the peněžní deník, and the figures for Příloha č. 1 including oddíl D. |
| `l10n_cz_currency_revaluation` | 19.0.1.1.0 | Pre-fills the OCA multicurrency-revaluation accounts with the Czech 563/663 (kurzové rozdiely) accounts. |
| `l10n_cz_datadance` | 19.0.1.1.1 | One-click Czech statutory localization: installs the core statutory reporting + invoice modules, with optional workflow pieces selectable in Settings. |
| `l10n_cz_dppo` | 19.0.1.3.0 | Czech corporate income-tax return on the income-tax framework: ř.10 from the P&L, manual adjustments, the II. oddíl tax spine, and EPO Pisemnost/DPPDP9 XML… |
| `l10n_cz_ec_sales` | 19.0.1.2.0 | Czech EC sales list / souhrnné hlášení (DPHSHV) on the shared EC-summary framework + the EPO Pisemnost/DPHSHV XML export. |
| `l10n_cz_epo` | 19.0.1.0.0 | Signs Czech statutory filings with the company's qualified certificate and sends them to EPO — to check (test mode) or to file — and follows the filing to… |
| `l10n_cz_fiscal_year_closing` | 19.0.1.0.0 | Make the Czech year-end closing postable: retype 701/702/710 from off_balance, which Odoo refuses to mix with any other account in one entry. |
| `l10n_cz_fs` | 19.0.1.1.0 | Czech balance sheet (Rozvaha), P&L (Výkaz zisku a ztráty), cash flow and changes in equity on the shared FS framework — account-code line mappings + XML. |
| `l10n_cz_hr_payroll_account_oca` | 19.0.1.0.1 | Post Czech payslips to the general ledger |
| `l10n_cz_hr_payroll_annual_tax_settlement` | 19.0.1.0.1 | Annual Czech income-tax reconciliation (annual tax settlement statement, DPZVD6) for the Finanční správa — advance income tax aggregated over the year, EPO XML… |
| `l10n_cz_hr_payroll_eldp` | 19.0.1.0.2 | Annual Czech pension-insurance record (ELDP) for the ČSSZ — per-employee assessment base and days aggregated over the calendar year, XML validated against the… |
| `l10n_cz_hr_payroll_health` | 19.0.1.1.0 | Czech health-insurance employer e-filings — monthly premium overview (PPPZ, payslip-aggregate) and bulk employee enrol/terminate notification (HOZ, employee… |
| `l10n_cz_hr_payroll_oca` | 19.0.1.11.1 | Czech payroll rules for the payroll engine |
| `l10n_cz_hr_payroll_onz` | 19.0.1.0.2 | Czech employment registration (ONZ) for the ČSSZ — per-employee start/end events built from the employee and hr.version lifecycle, XML validated against the… |
| `l10n_cz_hr_payroll_parity` | 19.0.1.2.1 | Cross-engine parity harness: drives one shared set of payroll scenarios through both the OCA payroll and the Enterprise hr_payroll Czech implementations and… |
| `l10n_cz_hr_payroll_pvpoj` | 19.0.1.1.1 | Monthly Czech social-insurance overview (PVPOJ) for the ČSSZ — employer-aggregate XML export validated against the official PVPOJ25.xsd. Engine-neutral… |
| `l10n_cz_hr_payroll_surcharges` | 19.0.1.0.0 | Engine-neutral statutory wage surcharges for overtime, public holiday, night, weekend and difficult-environment work (§§ 114–118 zákoníku práce), plus the… |
| `l10n_cz_hr_payroll_surcharges_oca` | 19.0.1.0.0 | Statutory Czech wage surcharges (§§ 114–118 zákoníku práce) as salary rules for the OCA payroll engine. |
| `l10n_cz_intrastat_oca` | 19.0.1.0.0 | INTRASTAT-CZ Celní správa InstatOnline CSV on the OCA intrastat_product engine (CE-clean). EE uses Odoo EE l10n_cz_intrastat instead. |
| `l10n_cz_invoice` | 19.0.1.0.2 | Czech invoice layout: customer DIČ, payment symbols and the mandatory statutory phrases (reverse charge §92a, exemptions §64/§66). |
| `l10n_cz_invoice_payment_mode` | 19.0.1.0.0 | Prints the payment mode as 'Forma úhrady' in the header of the Czech invoice. |
| `l10n_cz_kh` | 19.0.1.8.0 | Czech VAT control statement on the shared KV/KH framework: per-document A1–B3 sections with the 10 000 CZK split + the EPO Pisemnost/DPHKH1 XML export. |
| `l10n_cz_oss` | 19.0.1.0.0 | Czech layer of the OSS return: the EPO Pisemnost/OSSEI1 XML (daňové přiznání k DPH ve zvláštním režimu jednoho správního místa — režim Evropské unie)… |
| `l10n_cz_payment_reliability` | 19.0.1.0.2 | Czech provider for the CZ/SK supplier-reliability check: nespolehlivý plátce + zveřejněné účty from the MFČR ADIS web service (rozhraniCRPDPH). |
| `l10n_cz_purchase_order_advance_invoice` | 19.0.1.0.0 | Czech chart wiring for purchase_order_advance_invoice. |
| `l10n_cz_sale_order_advance_invoice` | 19.0.1.1.0 | Czech chart wiring for advance invoices (zálohové faktury) |
| `l10n_cz_statutory` | 19.0.1.3.0 | Czech statutory reference registries: finanční úřady (seeded from the official l10n_cz.tax_office codelist) and person types. |
| `l10n_cz_vat_return` | 19.0.1.10.0 | Czech VAT return (přiznání k DPH / DPHDP3) on the shared VAT-return framework: line set mapped to the l10n_cz tax tags + the EPO Pisemnost/DPHDP3 XML export. |
| `l10n_cz_vat_status` | 19.0.1.1.0 | The Czech company's own VAT registration status over time, and what it does to invoices, bills, DPHDP3 and the kontrolní hlášení. |
| `l10n_cz_vat_status_purchase` | 19.0.1.0.0 | Purchase order lines propose the taxes the company's VAT status allows on the order date (l10n_cz_vat_status). |
| `l10n_cz_vat_status_sale` | 19.0.1.0.0 | Sales order lines propose the taxes the company's VAT status allows on the order date (l10n_cz_vat_status). |

### Slovakia (50)

| Module | Version | What it does |
|---|---|---|
| `l10n_sk_account_asset_profile` | 19.0.1.1.0 | Starter accounting-depreciation profiles for a Slovak company, wired to the chart's asset and oprávky accounts. |
| `l10n_sk_account_asset_tax` | 19.0.1.0.3 | Slovak tax depreciation groups and coefficients (zákon 595/2003 Z.z. §26–28) |
| `l10n_sk_account_cutoff` | 19.0.1.0.2 | Pre-fills the OCA cut-off / deferral default accounts with the Slovak 381/383/384/385 accounts so časové rozlíšenie works out of the box. |
| `l10n_sk_account_loan_base` | 19.0.1.0.2 | Engine-neutral Slovak leasing/loan account defaults on the l10n_sk chart, shared by the Community and Enterprise bridges. |
| `l10n_sk_account_loan_oca` | 19.0.1.1.2 | Applies the Slovak leasing account defaults to the OCA account_loan / account_leasing engine. |
| `l10n_sk_account_move_template` | 19.0.1.0.2 | Slovak posting templates for INTERNAL accounting documents on the l10n_sk chart. Not a document-level predkontácia: invoices, bank and cash keep deriving their… |
| `l10n_sk_asset_protocol_base` | 19.0.1.0.4 | Engine-neutral Slovak asset-protocol data and templates, shared by the Community and Enterprise asset bridges. |
| `l10n_sk_asset_protocol_oca` | 19.0.2.0.1 | Zaraďovací and vyraďovací protokol as printable documents on the OCA asset register. |
| `l10n_sk_base` | 19.0.2.0.0 | The Slovak DIČ — the income-tax identifier, which is not the VAT number and not the company registry number. |
| `l10n_sk_cash_journal` | 19.0.1.1.0 | Slovak cash journal: the statutory členenie of opatrenie MF/27076/2007-74, the peňažný denník in its official column layout, and the DPFO typ B tabuľka 1 / 1a… |
| `l10n_sk_currency_revaluation` | 19.0.1.0.1 | Pre-fills the OCA multicurrency-revaluation accounts with the Slovak 563/663 (kurzové rozdiely) accounts. |
| `l10n_sk_datadance` | 19.0.1.4.3 | One-click Slovak statutory localization: installs the core statutory reporting + invoice modules, with optional workflow pieces selectable in Settings. |
| `l10n_sk_dppo` | 19.0.1.4.3 | Slovak DPPO return on the income-tax framework: full r-line set + header mapping + XSD-validated XML export against the official dppo2025 schema. |
| `l10n_sk_dppo_fs` | 19.0.1.1.2 | Tie the DPPO r100 to the VZS r56 of the účtovná závierka (UZPODv14) and flag a disagreement before filing. |
| `l10n_sk_ec_sales` | 19.0.1.2.2 | Slovak EC sales list (Súhrnný výkaz) — codes 0/1/2 (goods / triangulation / services), FS SR SDV XML export. Built on the shared l10n_cssk_ec_summary_base… |
| `l10n_sk_ekasa_receipt` | 19.0.1.0.0 | Read the QR code on a Slovak fiscal receipt and fetch the registered receipt — items, quantities and the VAT recap — from Finančná správa's… |
| `l10n_sk_fiscal_year_closing` | 19.0.1.0.1 | Slovak year-end closing template: costs and revenues to 710, balance-sheet accounts to 702, reopened through 701. |
| `l10n_sk_fs` | 19.0.1.7.0 | Slovak balance sheet (Súvaha) on the shared l10n_cssk_fs_base framework — account-code line mapping + comparison period + XML export. |
| `l10n_sk_hr_payroll_account_oca` | 19.0.1.0.1 | Post Slovak payslips to the general ledger |
| `l10n_sk_hr_payroll_annual_tax_report` | 19.0.2.0.0 | Annual Slovak employer income-tax report (Hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti, § 39 ods. 9) for the Finančná správa — aggregate… |
| `l10n_sk_hr_payroll_base` | 19.0.1.0.0 | Engine-neutral base for the Slovak payroll: the employment forms (pracovný pomer, DoVP, DoPČ, DoBPŠ) and one table saying which contributions and entitlements… |
| `l10n_sk_hr_payroll_eldp` | 19.0.1.0.2 | Annual per-employee Slovak pension record (ELDP) filed to the Sociálna poisťovňa — aggregates each year's pension assessment base and insured period per… |
| `l10n_sk_hr_payroll_health` | 19.0.1.1.0 | Monthly Slovak health-insurance advances statement (Mesačný výkaz preddavkov na poistné, dávka 514) for VšZP / Dôvera / Union — employer header + per-employee… |
| `l10n_sk_hr_payroll_monthly_tax_overview` | 19.0.2.0.0 | Monthly Slovak income-tax overview (Prehľad o zrazených a odvedených preddavkoch na daň) for the Finančná správa — withheld tax advances + daňový bonus recap… |
| `l10n_sk_hr_payroll_mvp` | 19.0.1.0.3 | Monthly Slovak social-insurance statement (MVP/MVPP) for the Sociálna poisťovňa — aggregate summary + per-employee annex, XML validated against MVPP-v2026.xsd… |
| `l10n_sk_hr_payroll_oca` | 19.0.1.18.3 | Slovak payroll rules for the payroll engine |
| `l10n_sk_hr_payroll_parity` | 19.0.1.8.0 | Cross-engine parity harness: drives one shared set of payroll scenarios through both the OCA payroll and the Enterprise hr_payroll Slovak implementations and… |
| `l10n_sk_hr_payroll_rlfo` | 19.0.1.1.1 | Slovak social-insurance registration of employees (RLFO / RLZEC) filed to the Sociálna poisťovňa — prihláška / odhláška events built from the employee +… |
| `l10n_sk_hr_payroll_surcharges` | 19.0.1.2.4 | Engine-neutral statutory wage surcharges for night, Saturday, Sunday, public-holiday, overtime, difficult-conditions and standby work (§§ 121–123 Zákonníka… |
| `l10n_sk_hr_payroll_surcharges_oca` | 19.0.1.0.2 | Statutory Slovak wage surcharges and the minimum-wage top-up as salary rules for the OCA payroll engine. |
| `l10n_sk_hr_payroll_vpp` | 19.0.1.0.1 | Slovak social-insurance statement for dohody / irregular income (VPP/VPP2026) filed to the Sociálna poisťovňa — aggregate summary + per-employee annex, XML… |
| `l10n_sk_intrastat` | 19.0.1.1.0 | INTRASTAT-SK INSTAT XML on the OCA intrastat_product engine (CE-clean). EE variant: l10n_sk_intrastat_ee. |
| `l10n_sk_inventory_verification` | 19.0.1.0.1 | Statutory Slovak inventory verification: inventúrne súpisy (§ 30 ods. 2) and the inventarizačný zápis (§ 30 ods. 3). |
| `l10n_sk_invoice` | 19.0.1.0.4 | Slovak invoice layout: DIČ/IČO/IČ DPH party block, payment symbols, supply/issue/due dates and mandatory §74 statutory phrases (reverse charge, exemptions)… |
| `l10n_sk_jcd` | 19.0.1.1.4 | Slovak import customs declaration: duty into stock value, import VAT onto the right DPH rows, deduction gated on the confirmed customs document. |
| `l10n_sk_kv_dph` | 19.0.2.3.0 | Slovak VAT control statement (Kontrolný výkaz DPH) — sections A.1–D.2 incl. D.1, with FS SR XML export. Built on the shared l10n_cssk_kv_kh_base framework. |
| `l10n_sk_mis_reports` | 19.0.1.0.0 | Management P&L on the Slovak chart, for Community — the counterpart to Enterprise's account_reports. |
| `l10n_sk_oss` | 19.0.1.0.0 | Slovak layer of the OSS return: the Finančná správa eForm DPOSS_EUv01 XML (daňové priznanie k DPH — osobitná úprava pre Úniu), on the EU OSSVATReturnMSCON… |
| `l10n_sk_payment_reliability` | 19.0.1.1.0 | Slovak provider for the CZ/SK supplier-reliability check: registered bank accounts (ds_dph_iban) and the tax-reliability index (ds_iz_ran) from the Financial… |
| `l10n_sk_purchase_order_advance_invoice` | 19.0.1.0.0 | Slovak chart wiring for purchase_order_advance_invoice. |
| `l10n_sk_sale_order_advance_invoice` | 19.0.1.1.0 | Slovak chart wiring for advance invoices (preddavkové faktúry) |
| `l10n_sk_single_entry_closing` | 19.0.1.0.2 | The closing a SZČO keeping jednoduché účtovníctvo files: výkaz o príjmoch a výdavkoch from the peňažný denník, výkaz o majetku a záväzkoch from the ledger. |
| `l10n_sk_statutory` | 19.0.1.0.0 | Slovak statutory reference registries: daňové úrady and person types. |
| `l10n_sk_trade_registry` | 19.0.2.0.0 | Keep the register, court and oddiel/vložka as data and compose the § 3a Obchodného zákonníka sentence from them, instead of typing it once into the company… |
| `l10n_sk_ubl_bis3` | 19.0.3.1.0 | Slovak e-invoicing: Peppol BIS Billing 3.0 / UBL 2.1 export |
| `l10n_sk_vat_registration` | 19.0.1.0.1 | Record which paragraph of the SK VAT Act a partner's IČ DPH was issued under, and warn when a § 69/12 reverse charge is aimed at a § 7 / § 7a registrant, who… |
| `l10n_sk_vat_return` | 19.0.1.12.0 | Slovak VAT return (DPHv25) — output/input lines wired to the l10n_sk tax tags, with FS SR DPH XML export. Built on the shared l10n_cssk_vat_return_base… |
| `l10n_sk_vehicle_expense` | 19.0.1.0.2 | 50 % VAT deduction on mixed-use vehicles and the 80 % fuel tax-expense paušál — two independent Slovak regimes. |
| `l10n_sk_vrp2_account` | 19.0.2.3.0 | Fiscalize customer invoices through the Slovak Virtual Cash Register (VRP 2) |
| `l10n_sk_vrp2_base` | 19.0.2.4.0 | Connection layer for the Slovak Virtual Cash Register (VRP 2) |

### Czech Republic and Slovakia (29)

| Module | Version | What it does |
|---|---|---|
| `l10n_cssk_accrual` | 19.0.1.0.4 | Estimated unbilled items — book an estimate to the accrual account (CZ 388/389, SK 326), then link the actual invoice to true it up. |
| `l10n_cssk_cash_journal_base` | 19.0.1.6.0 | Country-neutral single-entry cash journal derived from ordinary double-entry books: payments become dated, categorised denník rows, with the year-end balances… |
| `l10n_cssk_core` | 19.0.1.17.0 | Country-neutral foundation for the Czech & Slovak statutory localization: tax-authority registry, person types, shared company/partner fields, settings and… |
| `l10n_cssk_ec_summary_base` | 19.0.1.6.5 | Country-neutral framework for the Slovak Súhrnný výkaz and Czech Souhrnné hlášení (EC sales list): single-line aggregation per (country, VAT, transaction… |
| `l10n_cssk_ec_summary_vies` | 19.0.1.0.4 | Validate EC sales list partners against VIES at export and snapshot the consultation number onto each line. |
| `l10n_cssk_fs_base` | 19.0.1.9.0 | Country-neutral framework for the Slovak and Czech financial statements (balance sheet + P&L): line trees computed from account-code balances + aggregates… |
| `l10n_cssk_hr_payroll_garnishment_account` | 19.0.1.1.1 | Turn each wage-garnishment deduction into a payable to the bailiff, stamped with the case number as variable symbol, ready for the payment order and the bank… |
| `l10n_cssk_hr_payroll_garnishment_base` | 19.0.1.2.1 | Engine-neutral register of Czech and Slovak wage-garnishment orders (exekuční / exekučný príkaz) with the statutory multi-claim waterfall and the employer's… |
| `l10n_cssk_hr_payroll_garnishment_oca` | 19.0.1.0.1 | Apply the Czech/Slovak wage-garnishment waterfall on payslips computed by the OCA payroll engine. |
| `l10n_cssk_income_tax_base` | 19.0.1.5.5 | Country-neutral framework for the corporate income-tax return (DPPO): versioned line definitions, accounting-result + aggregate evaluator, manual-override UI… |
| `l10n_cssk_internal_document` | 19.0.1.0.0 | Print a journal entry as the interní / interný doklad the law requires |
| `l10n_cssk_intrastat_base` | 19.0.1.1.0 | Edition-neutral INTRASTAT-SK INSTAT (instat62) XML renderer shared by the CE (OCA) and EE (account_intrastat) adapters. |
| `l10n_cssk_intrastat_footprint` | 19.0.1.1.0 | A document says which Intrastat declaration reports it, alongside the VAT return, control statement and financial statements it feeds. |
| `l10n_cssk_kv_kh_base` | 19.0.2.2.1 | Abstract framework for the Slovak KV DPH and Czech KH DPH VAT control statements: versioned templates, section/summary/reconciliation row mixins, move-line… |
| `l10n_cssk_leave_expiry_reminder` | 19.0.1.0.3 | Proactively remind employees and HR about expiring carried-over leave |
| `l10n_cssk_oss_base` | 19.0.1.0.0 | Country-neutral engine for the quarterly One-Stop-Shop VAT return (Union scheme): OSS-tagged sales aggregated by member state of consumption, rate and supply… |
| `l10n_cssk_partner_balances` | 19.0.1.2.0 | Saldokonto / odsúhlasenie (potvrdenie) zostatkov pohľadávok a záväzkov — a stored, state-tracked confirmation of a partner's open AR/AP as of a date, with a… |
| `l10n_cssk_payment_reliability` | 19.0.1.1.0 | Before you pay a vendor, check the supplier's tax reliability and whether the bank account is the one registered with the tax authority — and snapshot the… |
| `l10n_cssk_payment_symbols` | 19.0.1.3.0 | Variable, constant and specific payment symbols on invoices, credit notes and bank statement lines. |
| `l10n_cssk_payment_symbols_payment_order` | 19.0.1.0.0 | Copy invoice VS/KS/SS onto OCA payment order lines. |
| `l10n_cssk_payroll_declaration_base` | 19.0.1.4.3 | Engine-neutral base for Czech/Slovak payroll authority e-submissions: XSD-validated XML export, a submission state machine and an hr.payslip adapter that works… |
| `l10n_cssk_receipt_capture` | 19.0.1.0.0 | Country-neutral framework for capturing cash-register receipts (bločky / účtenky) into Odoo: a provider registry, the captured receipt with its lines and… |
| `l10n_cssk_receipt_capture_expense` | 19.0.1.0.0 | Turn a captured fiscal receipt into employee expenses, and capture receipts from the expense attachment upload. |
| `l10n_cssk_recycling_fee` | 19.0.1.0.0 | Dated CZ/SK recycling-fee rates on OCA ecotax classifications, the statutory per-line 'z toho recyklační příspěvek' on the invoice, and a per-category period… |
| `l10n_cssk_recycling_fee_sale` | 19.0.1.0.0 | Price the CZ/SK recycling fee on sale order lines at the order date, carry it to the invoice, and optionally invoice it as its own line. |
| `l10n_cssk_registry_verify` | 19.0.1.0.0 | Answer whether an IČO exists in the state register, and say so in a way a gate can act on |
| `l10n_cssk_submission_base` | 19.0.1.0.1 | Channel-agnostic delivery framework for statutory filings: one record per delivery attempt-set, a pluggable channel contract, retry with backoff, and durable… |
| `l10n_cssk_vat_return_base` | 19.0.1.10.5 | Country-neutral framework for the Slovak and Czech VAT return: numbered report lines computed from tax tags + aggregate formulas, with an XSD-validated XML… |
| `l10n_cssk_vies` | 19.0.2.0.0 | Validate EU VAT numbers directly against the European Commission VIES service (no Odoo IAP) and store the official consultation number as proof of check. |

### European Union (1)

| Module | Version | What it does |
|---|---|---|
| `l10n_eu_nace_cssk` | 19.0.1.0.0 | NACE Rev. 2.1 industries with the CZ-NACE 2025 fifth digit, linked to the partner's NACE code |

### EDI and e-invoicing (5)

| Module | Version | What it does |
|---|---|---|
| `edi_base` | 19.0.1.8.0 | Shared infrastructure for EDI integrations (Editel, GRiT, ...) |
| `edi_base_peppol` | 19.0.1.5.1 | Provider-neutral Peppol BIS Billing 3.0: send/receive invoices and credit notes, and business responses (MLR / Invoice Response), over any EDI transport… |
| `edi_epostak_base` | 19.0.1.0.1 | Base module for the ePošťák (epostak.sk) Peppol access point: provider registration, environment/mode configuration and the Peppol addressing metadata every… |
| `edi_epostak_connector_sapi` | 19.0.1.1.1 | Concrete REST connector for the ePošťák Peppol access point (SAPI-SK 1.0): send and receive UBL, acknowledge, track delivery |
| `edi_epostak_peppol` | 19.0.1.0.0 | Send & receive Peppol BIS Billing 3.0 (invoices, credit notes, business responses) through the ePošťák access point |

### Payroll (2)

| Module | Version | What it does |
|---|---|---|
| `payroll_dashboard` | 19.0.1.1.0 | A lightweight graph + pivot dashboard of payroll headline figures (gross, net, employer cost, income tax) per period and employee, for the community payroll… |
| `payroll_worked_days_timeline` | 19.0.1.0.0 | Timeline and pivot views of payslip worked days and inputs, per employee over time — a community alternative to the Enterprise work-entries gantt for reviewing… |

### Banking and payments (17)

| Module | Version | What it does |
|---|---|---|
| `account_abo` | 19.0.2.0.0 | Export Czech/Slovak domestic credit transfers in the ABO file format |
| `account_fio` | 19.0.2.2.3 | Fio banka API tokens per bank journal, with the mandatory 30-second throttle and token-expiry watch. |
| `account_fio_base` | 19.0.1.2.0 | Shared Fio banka REST client, movement parser and payment-order builder. The statement puller and both payment-order bridges build on this. |
| `account_multicash` | 19.0.2.0.0 | Export payments in MultiCash formats (CFD/CFU/CFA/MT101) for Czech banks |
| `account_payment_fio` | 19.0.1.2.1 | Build Fio XML payment orders and send them to the bank from an OCA payment order. |
| `account_payment_kb_best` | 19.0.1.0.0 | Export payment orders in Komerční banka's BEST format (domestic transfers and direct debits, foreign and SEPA transfers). |
| `account_payment_kb_sepa` | 19.0.1.0.0 | Komerční banka's profile of the OCA pain.001.001.03 SEPA credit transfer: structured postal address, SWIFT character set. |
| `account_payment_mode_pay_on_post` | 19.0.1.0.0 | A payment mode can register the payment when the invoice is posted — cash and card sales paid on the spot. |
| `account_qr_code_frame_provider` | 19.0.1.1.0 | Shared QR-code frame parameters for the payment-QR providers (PAY by square, payme, QR Platba) that build on it. |
| `account_qr_code_pay_by_square_sk` | 19.0.1.2.0 | Slovak PAY by square payment QR code on invoices — the Slovak Banking Association standard every Slovak banking app reads, pre-filling IBAN, amount, currency… |
| `account_qr_code_payme_sk` | 19.0.1.2.0 | Slovak payme payment QR code on invoices — a payme.sk link that opens the customer's banking app with IBAN, amount, currency and payment identification… |
| `account_qr_code_qr_platba_cz` | 19.0.1.1.1 | Czech QR Platba payment QR code on invoices — the Czech Banking Association short payment descriptor (SPD) every Czech banking app reads, pre-filling IBAN… |
| `account_statement_fio` | 19.0.2.4.0 | Pull movements and official statements from the Fio banka API into bank journals. Community and Enterprise alike. |
| `account_statement_import_camt_balance` | 19.0.1.0.0 | Last daily closing balance; one line per entry when a bank splits its details |
| `account_statement_import_gpc` | 19.0.2.0.0 | Import Czech/Slovak GPC (ABO) bank statement files. |
| `account_statement_import_kb_best` | 19.0.1.0.0 | Import Komerční banka BEST electronic statements (*.OKM). |
| `account_statement_import_mt940` | 19.0.1.0.0 | Import SWIFT MT940 statements (MultiCash *.STA) with the Czech VS/KS/SS and counterparty subfields. |

### Currency rates (3)

| Module | Version | What it does |
|---|---|---|
| `currency_rate_sk_base` | 19.0.1.0.1 | Shared VÚB / Tatra banka exchange-rate fetch + parse. The CE (OCA currency_rate_update) and EE (currency_rate_live) SK providers both build on this. |
| `currency_rate_update_cz` | 19.0.1.3.0 | Czech National Bank (ČNB) daily exchange-rate provider for the OCA currency_rate_update framework. |
| `currency_rate_update_sk` | 19.0.1.1.0 | Slovak FX-rate providers for OCA currency_rate_update: ECB reference rate (NBS statutory) with previous-day fill, plus VÚB and Tatra banka commercial rate… |

### Point of sale (1)

| Module | Version | What it does |
|---|---|---|
| `pos_vrp2` | 19.0.5.0.0 | Integrate Odoo POS with Slovak Virtual Cash Register (VRP 2) |

### Partner and company data (5)

| Module | Version | What it does |
|---|---|---|
| `partner_autocomplete_ares_cz` | 19.0.1.2.1 | Completes Partner information from ARES (https://ares.gov.cz/) |
| `partner_autocomplete_dispatcher` | 19.0.1.1.0 | Technical dispatcher for the partner-autocomplete providers: assigns each dependent provider module to the companies that should use it. |
| `partner_autocomplete_orsf_sk` | 19.0.1.4.0 | Completes Partner information from the Slovak state registers via https://orsf.sk |
| `partner_autocomplete_orsf_sk_related_parties` | 19.0.2.0.0 | Pull one partner's ownership/officer graph from ORSF on demand, so § 17 ods. 5 related-party transactions can be recognised instead of remembered. |
| `partner_nace` | 19.0.1.0.0 | The partner's main economic activity as its NACE code |

### Accounting (18)

| Module | Version | What it does |
|---|---|---|
| `account_asset_board` | 19.0.1.0.0 | Interactive depreciation schedule and pivot/graph analysis for OCA assets (Community) |
| `account_asset_tax` | 19.0.1.9.4 | Country-neutral engine for a second, non-posted tax-depreciation board alongside accounting depreciation (daňové vs účetní/účtovné odpisy) |
| `account_asset_tax_oca` | 19.0.1.4.4 | Attach the CZ/SK tax-depreciation board to OCA account_asset_management (Community) |
| `account_cz_bankfile_base` | 19.0.1.3.1 | Shared ABO and MultiCash payment-file builders. The CE (account_payment_order) and EE (account_batch_payment) variants of account_abo / account_multicash both… |
| `account_debit_note_dd` | 19.0.1.0.0 | Names Odoo's core debit note as the Czech vrubopis (opravný daňový doklad zvyšující základ) on screen and on the printed document — a UI and report layer that… |
| `account_edi_isdoc` | 19.0.1.2.0 | Import and export ISDOC 6.0.2 electronic invoices (Czech national e-invoicing standard) |
| `account_edi_isdoc_purchase_advance` | 19.0.1.0.0 | Route imported ISDOC advance documents (DocumentType 4/5/6) into the received-advances flow. |
| `account_edi_isdoc_sale` | 19.0.1.0.0 | Export a sale order as an ISDOC proforma (zálohová faktura, DocumentType 4) |
| `account_edi_isdoc_sale_advance` | 19.0.1.0.0 | Map the Czech advance-payment documents to ISDOC DocumentType 4/5/6 |
| `account_gpc_base` | 19.0.1.0.0 | Shared GPC (ABO electronic statement) parser. The CE (account_statement_import_file) and EE (account_bank_statement_import) import shims both build on this. |
| `account_kb_best_base` | 19.0.1.0.0 | Komerční banka BEST client format: domestic and foreign/SEPA payment files out, electronic statements in. |
| `account_move_report_signed` | 19.0.1.0.0 | Renders negative (signed) values in Account Move note PDF reports |
| `account_mt940_base` | 19.0.1.0.0 | Shared SWIFT MT940 parser with the Czech ?NN layout of field :86: (MultiCash *.STA statements). |
| `account_reconcile_oca_counter_account` | 19.0.1.0.0 | Put the counterparty bank account back on the OCA bank statement reconciliation screen. |
| `purchase_order_advance_invoice` | 19.0.1.1.0 | Received advance invoices (vendor proformas) with tax documents on sent payments |
| `sale_order_advance_invoice` | 19.0.2.7.1 | Advance invoices (proforma) with tax documents on received payments |
| `sale_order_advance_invoice_payment_match` | 19.0.1.0.1 | Match incoming bank statement lines to advance invoices by variable symbol and register the payment automatically. |
| `sale_order_advance_invoice_payment_match_oca` | 19.0.1.0.1 | Runs the advance-invoice matching inside the OCA reconciliation widget's auto-reconcile. |

### Other (1)

| Module | Version | What it does |
|---|---|---|
| `advance_invoice_saldo_xlsx` | 19.0.1.0.1 | XLSX saldo of issued and received advance invoices: paid, tax-documented, deducted and open amounts. |
