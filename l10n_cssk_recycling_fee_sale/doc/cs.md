---
title: Recyklační příspěvek CZ/SK na prodejních objednávkách
summary: Spočítá recyklační příspěvek na řádcích prodejní objednávky, přenese jej na fakturu a v režimu „navíc“ jej fakturuje samostatným řádkem.
verified: 19.0.1.0.0
family: l10n_cssk_recycling_fee#sales-orders
---

Spočítá zákonný recyklační příspěvek na každém řádku prodejní objednávky podle sazby platné ke dni objednávky, se stejným výběrem trhu a přepočtem jednotek jako na faktuře, a přenese pevnou částku distributora z produktu na fakturu, která příspěvek spočítá znovu ke svému datu. Fakturuje-li společnost příspěvek navíc k ceně, tlačítko **Update Recycling Fee** na objednávce přidá jeden řádek příspěvku za každou klasifikaci a sazbu DPH s nastaveným produktem **Recycling Fee Product**; příspěvky za přenosné baterie řádek nikdy nedostanou.

Nainstaluje se sám, je-li nainstalován [module:l10n_cssk_recycling_fee](module:l10n_cssk_recycling_fee) i modul OCA `account_ecotax_sale`. Jediné nastavení, produkt příspěvku, se zobrazí v bloku *Recycling Fee* nastavení účetnictví, je-li zvoleno uvádění navíc.
