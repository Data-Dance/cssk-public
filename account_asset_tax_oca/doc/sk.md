---
title: Daňové odpisy — Community (register OCA)
summary: Pridá český a slovenský daňový odpisový plán k majetku v registri OCA, ktorý sa používa v Odoo Community.
verified: 19.0.1.5.0
family: account_asset_tax#oca
---

Pridá záložku *Daňové odpisy* k majetku v registri OCA `account_asset_management`, predvolené nastavenia daňových odpisov k profilom majetku, analýzu *Účtovné vs. daňové odpisy*, hromadnú akciu *Vypočítať daňové odpisy* (menu *Akcia* v zozname majetku a *Účtovníctvo → Konfigurácia*) a pri vyradení majetku v registri zapíše daňové vyradenie. Vstupná cena je obstarávacia hodnota majetku a dátum zaradenia dátum začiatku odpisovania.

Inštaluje sa spolu s modulom [module:account_asset_tax](module:account_asset_tax), registrom `account_asset_management` a údajmi krajiny ([module:l10n_sk_account_asset_tax](module:l10n_sk_account_asset_tax) / [module:l10n_cz_account_asset_tax](module:l10n_cz_account_asset_tax)); sám sa nenainštaluje. Nemožno ho kombinovať s mostom pre Enterprise, [module:account_asset_tax_ee](module:account_asset_tax_ee).
