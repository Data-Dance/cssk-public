---
title: Výpočet dane a zdravotného z doplatku
summary: Overené mesačné peňažné zúčtovanie z historického sociálneho poistného a dátumovaných parametrov dane/ZP.
verified: 19.0.1.0.1
---

## Účel {#purpose}

Výpočet kladného peňažného doplatku po skončení vzťahu. Sociálne poistné
prichádza z historického registra; daň a zdravotné používajú overený mesiac a
natívne dátumované parametre. Ďalšie mesačné príjmy sa konsolidujú pred NČZD a
pásmami. Jednodňový2Yprofil podporuje minimum aj vrátenie predošlého doplatku.

Editovateľné polia a voliteľné skryté API fakty sa nesmú miešať. Overujú sa
podklady, digest zdrojov/parametrov, archivácia, opakovanie aj väzby resetu.
Výpočet uchováva sumy, sám nevytvára účtovný doklad.

## Hranice {#scope}

Mesačné peňažné zúčtovanie vyplatené nasledujúci mesiac rovnakého roka,
poistenie skončené pred vykazovaným mesiacom, iba jeden2Ydeň; bez bonusov,
iných benefitov/zrážok a mimoriadnych opráv. Zdravotný profil a dôchodkový
status pre daň sú samostatné overené fakty. Pásku/účtovanie pripája modul
the separate native payroll bridge; historický VPP a zdravotné exporty sú ďalšie časti.
