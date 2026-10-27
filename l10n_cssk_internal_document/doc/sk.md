---
title: Interný doklad CZ/SK
summary: Vytlačí účtovný záznam ako interný doklad — s náležitosťami účtovného dokladu, ktoré vyžaduje zákon o účtovníctve.
verified: 19.0.1.0.1
---

## Na čo slúži {#purpose}

Každý účtovný zápis musí byť podložený účtovným dokladom. Pri faktúre alebo
bankovom výpise je ním samotný externý doklad; pri zápise, za ktorým nie je
nič externé — časové rozlíšenie, odpisy, precenenie, uzávierkový zápis, ručná
oprava — vyhotoví účtovník **interný doklad**.

Odoo takú tlačovú zostavu nemá. Modul ju pridáva: každý účtovný záznam sa dá
vytlačiť ako interný doklad s náležitosťami účtovného dokladu a s riadkom na
každý podpis.

Závisí len od modulu `account` a nepotrebuje zvyšok česko-slovenskej
lokalizácie.

## Právny rámec {#legal}

- **Slovensko.** Podľa [§ 10 ods. 1 zákona o účtovníctve](law:sk/2002/431#paragraf-10.odsek-1)
  musí účtovný doklad obsahovať slovné a číselné označenie, obsah účtovného
  prípadu a označenie jeho účastníkov, peňažnú sumu, dátum vyhotovenia, dátum
  uskutočnenia účtovného prípadu, ak nie je zhodný s dátumom vyhotovenia, a
  podpisový záznam osoby zodpovednej za účtovný prípad — ten len vtedy, ak
  overenie účtovného prípadu nie je zabezpečené elektronickou výmenou údajov
  alebo vnútorným kontrolným systémom (§ 32 ods. 3 písm. b) a c)).
- **Česko.** [§ 11 odst. 1 českého zákona o účetnictví č. 563/1991 Sb.](law:cz/1991/563)
  vyžaduje navyše aj podpisový záznam osoby zodpovednej za zaúčtovanie.

Zostava sa riadi dlhším, českým zoznamom, takže vyhovie obom. Na slovenskom
doklade je druhý podpisový riadok (za zaúčtovanie) nad rámec zákona.

## Ako ho vytlačiť {#usage}

Otvorte účtovný záznam (*Účtovníctvo → Účtovníctvo → Účtovné doklady* alebo
akúkoľvek faktúru či zápis) a zvoľte *Tlač → Interní / interný doklad*.
Môžete označiť aj viac záznamov v zozname a vytlačiť ich naraz; každý dostane
vlastnú stranu. Súbor sa pomenuje podľa dokladu, napr.
`Interný doklad - MISC-2026-10-0007.pdf`.

Nič sa nenastavuje.

## Čo doklad obsahuje {#content}

| Na doklade | Odkiaľ sa berie |
|---|---|
| Označenie dokladu | číslo záznamu |
| Účtovná jednotka | spoločnosť a jej IČO, ak je vyplnené |
| Denník | denník záznamu |
| Obsah účtovného prípadu | pole *Referencia*; ak je prázdne, interná poznámka; ak aj tá chýba, popisy riadkov |
| Účastníci účtovného prípadu | spoločnosť a každý partner na zázname a jeho riadkoch |
| Peňažná suma | súčet záznamu (súčet strany Má dať) v mene spoločnosti |
| Dátum vyhotovenia | deň, keď bol záznam v Odoo **vytvorený** |
| Dátum uskutočnenia účtovného prípadu | dátum účtovania |
| Riadky | účet, popis, partner, analytické rozdelenie s podielom (napr. `Sklad (60 %)`), Má dať, Dal a súčty |
| Podpisové záznamy | vľavo používateľ, ktorý záznam **vytvoril**, ako osoba zodpovedná za účtovný prípad; vpravo ten, kto ho **zaúčtoval**; pri každom riadok na podpis |

Nezaúčtovaný koncept má pod nadpisom **NEZAÚČTOVANÉ** a pri podpise za
zaúčtovanie nie je meno.

## Jazyk {#language}

Texty sú zákonné pojmy a **neprekladajú sa**: riadia sa krajinou daňovej
príslušnosti spoločnosti. Slovenská spoločnosť tlačí slovenské znenie, každá
iná české. Jazyk používateľa nerozhoduje.

## Obmedzenia {#limitations}

- *Dátum vyhotovenia* je deň vytvorenia záznamu v Odoo, nie dátum, ktorý
  zvolíte. Ak bol doklad vyhotovený iný deň, zostava to neukáže.
- Kto záznam zaúčtoval, sa číta z histórie záznamu (posledná zmena stavu). Pri
  automatickom zaúčtovaní plánovanou akciou je to používateľ, pod ktorým akcia
  beží; ak bola história vymazaná, meno zostane prázdne.
- Vytlačené mená sú používatelia Odoo, ktorí záznam vytvorili a zaúčtovali, nie
  nevyhnutne osoby, ktoré za prípad zodpovedajú podľa vašej internej smernice.
  Riadky slúžia na skutočný podpis; modul nič elektronicky nepodpisuje.
- Množstvo a jednotková cena sa netlačia; peňažná suma je súčet záznamu.
- Takto sa dá vytlačiť každý záznam vrátane faktúr, hoci tie už majú externý
  doklad.
