---
title: Výpočet dane a zdravotného z doplatku
summary: Overené mesačné peňažné zúčtovanie z historického sociálneho poistného a dátumovaných parametrov dane/ZP.
verified: 19.0.1.0.2
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
samostatného natívneho mzdového mosta; historický VPP a zdravotné exporty sú ďalšie časti.

## Právny základ {#legal-basis}

Mesačná daň vychádza z [§ 35](law:sk/2003/595#paragraf-35), vyhlásenie
z [§ 36](law:sk/2003/595#paragraf-36) a centové zaokrúhľovanie z [§ 47](law:sk/2003/595#paragraf-47).
Status poberateľa dôchodku k 1. januáru podľa [§ 11 ods. 6](law:sk/2003/595#paragraf-11.odsek-6)
nezakladá mesačnú NČZD iba zaškrtnutím vyhlásenia. [FAQ Finančnej správy pre 2026,
otázky 7 a 9](https://podpora.financnasprava.sk/260857-Nezdanite%C4%BEn%C3%A1-%C4%8Das%C5%A5-z%C3%A1kladu-dane-na-da%C5%88ovn%C3%ADka-za-rok-2026)
výslovne vylučujú mesačnú NČZD pri tomto profile aj pri nízkom dôchodku.
Rozdiel po odpočítaní ročného dôchodku vrátane 13. dôchodku patrí do RZD/osobného
DP. Dôchodok účinný až počas roka je iná daňová skutočnosť. Znenie § 35 pre 2027
zachováva toto rozlíšenie.

Zdravotné výnimky upravujú [§ 10b](law:sk/2004/580#paragraf-10b)
a [§ 11 ods. 3](law:sk/2004/580#paragraf-11.odsek-3), sadzby a mesačné preddavky
[§ 16](law:sk/2004/580#paragraf-16), pomerné minimum, výnimky a doplatok
[§ 16a](law:sk/2004/580#paragraf-16a). Kód 2Y a jednodňové prihlásenie na posledný
deň mesiaca sú metodikou poisťovní, nie doslovným kódom zákona:
[postup Union](https://www.union.sk/pomoc-a-podpora/nepravidelny-prijem-a-prijem-vyplateny-zamestnancovi-po-skonceni-pracovneho-pomeru/).
Ak skoršia platba rovnakého mesiaca už niesla doplatok do minima, nový výpočet
určí iba rozdiel voči súhrnu mesiaca. Záporný rozdiel vráti predošlý nadmerný
doplatok; nejde o ročnú vratku poisťovne ani vratku poistného iného obdobia.
