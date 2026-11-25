---
title: CZ/SK Inventarizácia — zaúčtovanie rozdielov (základ)
summary: Spoločný kód, ktorý účtuje rozdiely zistené slovenskou inventarizáciou alebo českou inventarizací ako účtovný zápis v overovanom období.
verified: 19.0.1.0.0
family: l10n_sk_inventory_verification#differences
---

Obsahuje logiku spoločnú obom modulom inventarizácie: riadky vyúčtovania rozdielu (manko alebo schodok, úbytok do normy, prebytok, náhrada od zodpovednej osoby), kontrolu, že vysvetľujú celý rozdiel súpisu, účtovný zápis v návrhu s dátumom v overovanom období a jeho vymazanie alebo storno pri opätovnom otvorení dokladu. Odmietne tiež zaúčtovať taký zápis do uzamknutého obdobia, kde by ho Odoo inak posunulo do iného účtovného obdobia.

Nemá vlastné obrazovky ani nastavenia a inštaluje sa automaticky s modulom [module:l10n_sk_inventory_verification](module:l10n_sk_inventory_verification) alebo [module:l10n_cz_inventory_verification](module:l10n_cz_inventory_verification). O tom, ktorý účet patrí ku ktorému rozdielu, rozhodujú tieto dva moduly.
