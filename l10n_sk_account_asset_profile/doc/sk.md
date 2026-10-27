---
title: Slovensko — východiskové profily majetku
summary: Desať pripravených profilov majetku pre slovenskú spoločnosť, jeden na každý odpisovaný účet majetku v účtovej osnove, každý s vlastným účtom oprávok a s účtom 551.
verified: 19.0.1.2.0
---

## Na čo slúži {#purpose}

V registri majetku v Community (OCA
[module:account_asset_management](module:account_asset_management)) potrebuje
každý majetok **profil majetku**: určuje, na ktoré účty sa odpisy účtujú a za
akú dobu sa majetok odpisuje. Nová slovenská spoločnosť má v účtovej osnove
všetky účty majetku, ale žiadny profil, takže prvý majetok — zadaný ručne
alebo importovaný — nemá na čo nadviazať.

Modul dá každej slovenskej spoločnosti desať východiskových profilov, jeden pre
každý odpisovaný účet majetku slovenskej účtovej osnovy. Týkajú sa len
**účtovných odpisov**. Daňové odpisy sa riadia odpisovými skupinami podľa
zákona a rieši ich samostatne modul
[module:account_asset_tax](module:account_asset_tax), ktorý sa nainštaluje
spolu s týmto modulom.

## Právny rámec {#legal}

Podľa [§ 28 ods. 3 zákona o účtovníctve](law:sk/2002/431#paragraf-28.odsek-3)
je účtovná jednotka povinná zostaviť si **odpisový plán** a podľa
[§ 28 ods. 4](law:sk/2002/431#paragraf-28.odsek-4) odpisuje majetok počas
predpokladanej doby používania; goodwill a aktivované náklady na vývoj, ktorých
životnosť sa nedá spoľahlivo odhadnúť, musí odpísať najneskôr do piatich rokov
od obstarania. Podľa [§ 28 ods. 2](law:sk/2002/431#paragraf-28.odsek-2) sa
pozemky neodpisujú.

Doby odpisovania v profiloch sú preto **východiskom pre váš odpisový plán, nie
zákonnými hodnotami**. Pred potvrdením prvého majetku ich porovnajte s
vnútornou smernicou.

## Profily {#profiles}

Každý profil účtuje odpisy na účet **551000** (*Odpisy*) v denníku interných
účtovných dokladov, rovnomerne, jedným zápisom za mesiac:

| Profil | Účet majetku | Účet oprávok | Roky |
|---|---|---|---|
| Aktivované náklady na vývoj | 012000 | 072000 | 5 |
| Softvér | 013000 | 073000 | 4 |
| Oceniteľné práva | 014000 | 074000 | 5 |
| Goodwill | 015000 | 075000 | 5 |
| Ostatný dlhodobý nehmotný majetok | 019000 | 079000 | 5 |
| Stavby | 021000 | 081000 | 40 |
| Samostatné hnuteľné veci a súbory hnuteľných vecí | 022000 | 082000 | 6 |
| Pestovateľské celky trvalých porastov | 025000 | 085000 | 12 |
| Základné stádo a ťažné zvieratá | 026000 | 086000 | 4 |
| Ostatný dlhodobý hmotný majetok | 029000 | 089000 | 6 |

Nastavenie profilov: *Metóda výpočtu* Lineárny, *Časová metóda* Doba odpisovania (roky alebo dátum konca),
*Dĺžka obdobia* Mesiac, *Prorata Temporis* zapnuté. Prvému roku preto pripadne
len jeho podiel ročného odpisu, od dátumu začiatku odpisovania do konca roka —
OCA ho počíta podľa dní — a nie celý ročný odpis za majetok zaradený v
novembri. Pri nehmotnom majetku (012 – 019) na tom záleží dvakrát: podľa
[§ 22 ods. 8 zákona o dani z príjmov](law:sk/2003/595#paragraf-22.odsek-8) sa
jeho daňové odpisy riadia účtovnými. Ak chcete celé mesiace, zadajte ako
dátum začiatku prvý deň mesiaca, od ktorého plán odpisuje (mesiac zaradenia
do používania alebo nasledujúci).

**031 Pozemky** a **032 Umelecké diela a zbierky** profil nemajú: nič na nich
sa neodpisuje a profil by im pripísal dobu používania, ktorú nemajú.

**Žiadny profil nemá daňovú odpisovú skupinu.** *Sledovať daňové odpisy* je
vypnuté a *Daňová odpisová skupina* prázdna, zámerne: odpisovú skupinu neurčuje
účet — budova môže patriť do skupiny 5 alebo 6, stroj do 1, 2 alebo 3 — a
nesprávna predvolená hodnota by potichu vytvárala nesprávne daňové odpisy.

## Nastavenie {#setup}

Profily sa vytvoria pre každú spoločnosť so slovenskou účtovou osnovou: pri
načítaní osnovy a pri inštalácii modulu pre spoločnosti, ktoré ju už majú.
Profil, ktorý spoločnosť už má, sa nikdy nevytvára znova ani neprepisuje, takže
vaše úpravy prežijú aj neskoršie aktualizácie. Spoločnosť, ktorá niektorý z
použitých účtov zmazala alebo prečíslovala, sa preskočí (v logu servera je
upozornenie) a profily si musí vytvoriť ručne.

Po inštalácii v ponuke
*Fakturácia → Konfigurácia → Majetok → Profily majetku* (koreňová ponuka
sa volá *Účtovníctvo*, ak je nainštalované Účtovníctvo z Odoo Enterprise):

1. **Upravte doby odpisovania** podľa svojho odpisového plánu. Ak odpisy
   účtujete raz ročne, zmeňte *Dĺžku obdobia* na rok; *Prorata Temporis*
   nechajte zapnuté, pokiaľ váš plán naozaj neúčtuje v prvom roku celý ročný
   odpis.
2. **Pri profiloch, ktorých majetok patrí celý do jednej odpisovej skupiny**,
   zaškrtnite *Sledovať daňové odpisy* a zvoľte *Daňovú odpisovú skupinu*.
   Majetok vytvorený z profilu potom skupinu prevezme (pozri
   [module:account_asset_tax](module:account_asset_tax#oca)). Inak pole nechajte
   prázdne a skupinu zadajte pri každom majetku.
3. Ďalšie profily vytvorte tam, kde jeden účet zahŕňa majetok s veľmi odlišnou
   dobou používania (napríklad viac profilov na účte 022000).

## Obmedzenia {#limitations}

- Doby odpisovania zodpovedajú bežnej praxi, nie zákonu, a sú pre všetky
  spoločnosti rovnaké. Nezávisia od daňovej odpisovej skupiny.
- OCA kráti prvý rok **podľa dní** od dátumu začiatku odpisovania, nie po
  celých mesiacoch: začiatok 1. júla dá 184/365 ročného odpisu, nie 6/12. Pri
  začiatku k prvému dňu mesiaca ide o rozdiel niekoľkých dní.
- Profily vytvorené pred verziou 19.0.1.2.0 si ponechajú ročné nastavenie bez
  krátenia; zmeňte ich ručne (krok 1).
- Existujúci majetok modul nemení. Neskoršia zmena profilu nezmení majetok,
  ktorý už bol z neho vytvorený.
- Len pre register majetku v Community: modul vyžaduje
  [module:account_asset_tax_oca](module:account_asset_tax_oca), a preto sa
  nedá nainštalovať spolu s modulom `account_asset` z Odoo Enterprise. V
  Enterprise dodáva vzory majetku samotná slovenská účtová osnova Odoo — a v
  Odoo 19.0 dva z nich ukazujú na nesprávny účet majetku (*Základné stádo a
  ťažné zvieratá* na 029000 a *Ostatný dlhodobý hmotný majetok* na 031000,
  pozemky). Tento modul páruje každý profil s účtom majetku, ku ktorému patrí
  jeho účet oprávok; v Enterprise tieto dva vzory skontrolujte ručne.
