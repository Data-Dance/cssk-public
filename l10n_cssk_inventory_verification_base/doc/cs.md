---
title: CZ/SK Inventarizace — zaúčtování rozdílů (základ)
summary: Společný kód, který účtuje rozdíly zjištěné slovenskou inventarizácií nebo českou inventarizací jako účetní zápis v ověřovaném období.
verified: 19.0.1.0.0
family: l10n_sk_inventory_verification#differences
---

Obsahuje logiku společnou oběma modulům inventarizace: řádky vyúčtování rozdílu (manko nebo schodek, úbytek do normy, přebytek, náhrada od odpovědné osoby), kontrolu, že vysvětlují celý rozdíl soupisu, účetní zápis v návrhu s datem v ověřovaném období a jeho smazání nebo storno při opětovném otevření dokladu. Odmítne také zaúčtovat takový zápis do uzamčeného období, kde by jej Odoo jinak posunulo do jiného účetního období.

Nemá vlastní obrazovky ani nastavení a instaluje se automaticky s modulem [module:l10n_sk_inventory_verification](module:l10n_sk_inventory_verification) nebo [module:l10n_cz_inventory_verification](module:l10n_cz_inventory_verification). O tom, který účet patří ke kterému rozdílu, rozhodují tyto dva moduly.
