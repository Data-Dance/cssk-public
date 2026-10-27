---
title: Tax Depreciation — Community (OCA register)
summary: Puts the Czech/Slovak tax depreciation board on assets of the OCA asset register used on Odoo Community.
verified: 19.0.1.5.0
family: account_asset_tax#oca
---

Adds the *Tax Depreciation* tab to assets of the OCA `account_asset_management` register, tax depreciation defaults to asset profiles, the *Book vs Tax Depreciation* analysis, the *Compute Tax Depreciation* batch action (asset list *Action* menu and *Accounting → Configuration*), and records the tax disposal when an asset is removed in the register. The entry value is the asset's purchase value and the in-service date its depreciation start date.

Install it together with [module:account_asset_tax](module:account_asset_tax), `account_asset_management` and the country data ([module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) / [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax)); it does not install itself. It cannot be combined with the Enterprise bridge, [module:account_asset_tax_ee](module:account_asset_tax_ee).
