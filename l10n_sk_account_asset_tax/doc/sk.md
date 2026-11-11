---
title: SK daňové odpisové skupiny
summary: Sedem slovenských odpisových skupín 0 – 6 s dobou odpisovania a koeficientmi zrýchleného odpisovania pre daňový odpisový plán.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Nahrá slovenské zákonné odpisové skupiny do modulu daňových odpisov
[module:account_asset_tax](module:account_asset_tax). S nimi môže slovenská
spoločnosť zaradiť majetok do skupiny a nechať si vypočítať daňový odpisový
plán podľa slovenských pravidiel: pomerný prvý rok podľa mesiacov,
neuplatnená časť v roku po uplynutí doby odpisovania a zrýchlené odpisovanie
v skupinách 2 a 3.

Ako sa plán počíta a čo s ním ďalej robiť, opisuje
[návod k daňovým odpisom](module:account_asset_tax#board).

## Právny rámec {#legal}

[Zákon č. 595/2003 Z. z. o dani z príjmov](law:sk/2003/595):

- odpisové skupiny a dobu odpisovania ustanovuje
  [§ 26 ods. 1](law:sk/2003/595#paragraf-26.odsek-1); do ktorej skupiny
  majetok patrí, určuje príloha č. 1 zákona podľa klasifikácie produkcie;
- zrýchlene možno odpisovať len majetok v skupinách 2 a 3 a spôsob
  odpisovania nemožno zmeniť po celú dobu odpisovania —
  [§ 26 ods. 3](law:sk/2003/595#paragraf-26.odsek-3);
- ročný odpis pri rovnomernom odpisovaní = vstupná cena ÷ doba odpisovania, v
  prvom roku pomerne podľa mesiacov —
  [§ 27](law:sk/2003/595#paragraf-27.odsek-1);
- koeficienty zrýchleného odpisovania —
  [§ 28 ods. 1](law:sk/2003/595#paragraf-28.odsek-1).

## Odpisové skupiny {#groups}

| Skupina | Doba odpisovania | Ročný odpis (rovnomerne) | Zrýchlene (§ 28) — v prvom roku / v ďalších rokoch / pre zvýšenú zostatkovú cenu |
|---|---|---|---|
| 0 | 2 roky | 1/2 | — |
| 1 | 4 roky | 1/4 | — |
| 2 | 6 rokov | 1/6 | 6 / 7 / 6 |
| 3 | 8 rokov | 1/8 | 8 / 9 / 8 |
| 4 | 12 rokov | 1/12 | — |
| 5 | 20 rokov | 1/20 | — |
| 6 | 40 rokov | 1/40 | — |

Záznamy sa volajú *Odpisová skupina 0* až *6* s kódmi `SK-0` až `SK-6` a v
poli skupiny na majetku sa zobrazujú napríklad ako
`SK-2 — Odpisová skupina 2 (6 r.)`.

## Nastavenie {#setup}

Inštaluje sa s modulom daňových odpisov a mostom k registru majetku
([module:account_asset_tax_oca](module:account_asset_tax_oca) v Community,
[module:account_asset_tax_ee](module:account_asset_tax_ee) v Enterprise).
Vyžaduje slovenskú lokalizáciu Odoo (`l10n_sk`). Nič sa nenastavuje: skupiny
sú v *Účtovníctvo → Konfigurácia → Daňové odpisové skupiny* a karta majetku
ich ponúkne spoločnostiam s krajinou Slovensko. Hodnoty sa pri každej
aktualizácii modulu nahrajú znova, takže ručné zmeny aktualizáciu neprežijú.

## Osobné vozidlá: DPH mimo vstupnej ceny {#par52zzzk}

Od 1. 1. 2026 platiteľ odpočíta len polovicu DPH z osobného vozidla
používaného aj na súkromné účely
([§ 85n zákona o DPH](law:sk/2004/222#paragraf-85n)). Účtovníctvo druhú
polovicu zahrnie do obstarávacej ceny vozidla, pre daň z príjmov však „nie je
súčasťou vstupnej ceny“ ([§ 52zzzk](law:sk/2003/595#paragraf-52zzzk)).

Ak je nainštalovaný modul
[module:l10n_sk_vehicle_expense](module:l10n_sk_vehicle_expense), vstupná
cena, ktorú daňové odpisy pri takom majetku navrhnú, ju vynechá: majetok má
hodnotu toho, čo jeho riadky faktúry zaúčtovali na účet majetku, a daňové
odpisy vychádzajú z tejto hodnoty bez neodpočítanej DPH sadzieb označených
*DPH z vozidla obmedzená § 85n*. Auto kúpené za 20 000 € plus 23 % DPH so
sadzbou pre kúpu vozidla je majetok za 22 300 € so vstupnou cenou 20 000 €.
Rozdiel medzi účtovnými a daňovými odpismi sa do daňového priznania
právnickej osoby dostane cez jeho tabuľku B.

Vstupná cena sa len navrhuje — keď daňové odpisy zapnete, alebo keď sa
odpisy počítajú s prázdnou vstupnou cenou. Cenu, ktorú zadáte sami, modul
nemení. Ak sa z jedného riadku faktúry vytvorí viac majetkov, každý dostane
svoj podiel DPH.

## Obmedzenia {#limitations}

- Nahrajú sa len skupiny. Zaradenie majetku do skupiny je na vás; modul
  nenavrhuje skupinu podľa produktu ani účtu.
- Sadzby rovnomerného odpisovania sa neukladajú: plán odvodí ročný odpis z
  doby odpisovania.
- V čom sa plán od zákona odchyľuje alebo čo nepokrýva — rok vyradenia,
  osobné automobily od 48 000 eur, odpisovanie mikrodaňovníka —, uvádza
  [návode k daňovým odpisom](module:account_asset_tax#limitations).
- Nehmotný majetok nemá odpisovú skupinu: zákon zaraďuje len hmotný majetok, preto je prázdna skupina pri nehmotnom majetku správna a konečná.
