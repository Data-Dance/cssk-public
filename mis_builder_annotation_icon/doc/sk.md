---
title: MIS Builder – ikona poznámky
summary: Poznámka k bunke výkazu MIS Builder sa pridáva cez ikonu poznámky namiesto rozbaľovacej šípky, ktorá vyzerala, akoby sa riadok dal rozbaliť.
verified: 19.0.1.0.0
family: guide:mis_reports#annotations
---

## Na čo slúži {#purpose}

[module:mis_builder](module:mis_builder) umožňuje pripojiť k bunke výkazu
poznámku. Ponúkal to cez rozbaľovaciu šípku v každej bunke, ktorá otvorila
menu s jedinou položkou *Annotate*. Šípka nadol pôsobí ako „tento riadok sa
dá rozbaliť“, čo mätie vedľa riadkov, ktoré sa naozaj rozbaľujú, a šedú šípku
mali aj bunky, ku ktorým sa poznámka pridať nedá.

Modul šípku nahrádza ikonou poznámky. Nič sa nenastavuje: nainštaluje sa
spolu s `mis_builder` a nič iné nemení.

## Ako sa správa {#behaviour}

- Keď ukážete na riadok, pri každej hodnote, ku ktorej sa dá pridať poznámka,
  sa objaví prázdna ikona; kliknutím poznámku napíšete. Dialóg je rovnaký ako
  doteraz.
- Bunka s poznámkou má ikonu vyplnenú a viditeľnú stále, vedľa čísla
  poznámky. Kliknutím poznámku zmeníte; samotná poznámka je pod výkazom, kde
  sa dá aj zmazať.
- Bunky, ku ktorým sa poznámka pridať nedá (napríklad riadky detailov),
  ikonu nemajú.
- Ikonu vidia len používatelia, ktorí môžu poznámky upravovať.
