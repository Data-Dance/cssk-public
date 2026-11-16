---
title: Položková tabuľka A DPPO
summary: Nákladové položky s dokladmi napĺňajú natívne riadky tabuľky A podľa vzoru priznania, bez nahradenia odpisového registra a histórie podaní.
verified: 19.0.1.0.1
---

## Účel {#purpose}

Doplnok zoskupuje nedaňové náklady do vstupných riadkov tabuľky A zvoleného vzoru DPPO. Vyžaduje l10n_sk_dppo aspoň 19.0.1.5.0 a l10n_cssk_income_tax_base aspoň 19.0.1.6.0. Daň ďalej počítajú natívne riadky priznania. Tabuľku B a r150/r250 napĺňa odpisový register a natívne ručné vstupy.

## Postup {#workflow}

Zapnite položkový rozpis, vyberte riadok, zadajte sumu a dôkaz. Overte celý rozpis a prepočítajte priznanie. Viaceré položky jedného riadka sa sčítajú. Popisy vychádzajú z príslušného vzoru; súčtový riadok staršieho formulára nemožno zadať ako nákladovú položku.

Doplnok spravuje iba riadky s položkami. Ostatné ručné vstupy A a všetky vstupy B zachováva. Pri zapnutom rozpise má súčet položiek prednosť. Odstránenie položky či vypnutie doplnku pri prepočte uvoľní predchádzajúce generované prepisy; nezávisle zmenená ručná hodnota zostáva. Po zmene súm treba pred exportom prepočet.

Tá istá kontrola aktuálneho rozpisu sa používa pri XML, natívnom úradnom PDF,
ak je dostupný, aj pri zaúčtovaní dane. Po zmene rozpisu treba priznanie
prepočítať, až potom výstupy použijú jeho sumy. Historické prílohy ostávajú
dostupné. Pridanie položiek pre viac priznaní overí celú dávku pred zmenou
ktoréhokoľvek z nich.

## Dodatočné priznanie a história {#amendments}

Natívne vytvorenie dodatočného priznania skopíruje položky a riadky, ale zruší overenie a jeho dôkaz. Opravu samostatne overte a prepočítajte. Archiváciu podaného XML rieši spoločný rámec. Doplnok nezasahuje do príloh, sťahovania súborov, šablón tabuľky B ani výpočtového jadra. Zmena sídla alebo zaúčtovanie daňovej rezervy neblokuje stiahnutie starého exportu.

## Rozsah {#scope}

Daňovú uznateľnosť a dôkazy posudzuje účtovník. Nevzniká druhá účtovná kniha ani vlastný archív podaní.
