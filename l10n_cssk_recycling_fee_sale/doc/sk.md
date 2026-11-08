---
title: Recyklačný poplatok CZ/SK na predajných objednávkach
summary: Vypočíta recyklačný poplatok na riadkoch predajnej objednávky, prenesie ho na faktúru a v režime „navyše“ ho fakturuje samostatným riadkom.
verified: 19.0.1.0.1
family: l10n_cssk_recycling_fee#sales-orders
---

Vypočíta zákonný recyklačný poplatok na každom riadku predajnej objednávky podľa sadzby platnej v deň objednávky, s rovnakým výberom trhu a prepočtom jednotiek ako na faktúre, a prenesie pevnú sumu distribútora z produktu na faktúru, ktorá poplatok vypočíta znova k svojmu dátumu. Ak spoločnosť fakturuje poplatok navyše k cene, tlačidlo **Update Recycling Fee** na objednávke pridá jeden riadok poplatku za každú klasifikáciu a sadzbu DPH s nastaveným produktom **Recycling Fee Product**; poplatky za prenosné batérie riadok nikdy nedostanú.

Nainštaluje sa sám, keď je nainštalovaný [module:l10n_cssk_recycling_fee](module:l10n_cssk_recycling_fee) aj modul OCA `account_ecotax_sale`. Jediné nastavenie, produkt poplatku, sa zobrazí v bloku *Recycling Fee* nastavení účtovníctva, keď je zvolené uvádzanie navyše.

Opätovné stlačenie **Update Recycling Fee** riadky s poplatkom vytvorí nanovo; po ich vyfakturovaní to tlačidlo odmietne. Riadky sa obnovujú len tlačidlom, nie pri každej zmene objednávky. Ponuky údaj za riadok netlačia, faktúra áno.
