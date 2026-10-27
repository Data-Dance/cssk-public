---
title: SK Leasing — Community engine (OCA)
summary: Opens every new OCA loan or lease with the Slovak accounts and, for a lease that is a supply of goods, leaves VAT off its instalment bills.
verified: 19.0.1.2.0
family: l10n_sk_account_loan_base#community
---

Fills a new loan or lease of the OCA engine with the Slovak accounts from the company settings — *Long term account* 474000, *Short term account* 474100, *Interests account* 562000 and the leased asset account 022000 — and refills them when the company on the form changes. On companies with the Slovak chart the *Leasing* tab gains the Slovak tax treatment: the VAT regime (*Režim DPH*), the depreciation group and the 60 % lease-term warning. When the regime is a supply of goods, the bridge removes VAT from the instalment bills the engine generates, because such a lease is taxed once at handover; until a regime is chosen the instalments keep their VAT. The family guide explains the details.

It installs itself when [module:l10n_sk_account_loan_base](module:l10n_sk_account_loan_base) and OCA `account_leasing` are installed, and cannot be installed together with Enterprise loans (`account_loans`).
