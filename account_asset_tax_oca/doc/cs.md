---
title: Daňové odpisy — Community (registr OCA)
summary: Přidá český a slovenský daňový odpisový plán k majetku v registru OCA, který se používá v Odoo Community.
verified: 19.0.1.5.0
family: account_asset_tax#oca
---

Přidá záložku *Daňové odpisy* k majetku v registru OCA `account_asset_management`, výchozí nastavení daňových odpisů k profilům majetku, analýzu *Účetní vs. daňové odpisy*, hromadnou akci *Vypočítat daňové odpisy* (nabídka *Akce* v seznamu majetku a *Účetnictví → Konfigurace*) a při vyřazení majetku v registru zapíše daňové vyřazení. Vstupní cena je pořizovací hodnota majetku a datum zařazení datum zahájení odpisování.

Instaluje se spolu s modulem [module:account_asset_tax](module:account_asset_tax), registrem `account_asset_management` a údaji státu ([module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax) / [module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax)); sám se nenainstaluje. Nelze jej kombinovat s mostem pro Enterprise, [module:account_asset_tax_ee](module:account_asset_tax_ee).
