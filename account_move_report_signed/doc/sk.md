---
title: Záporné sumy na dobropisoch (PDF)
summary: Vytlačí sumy na dobropise odberateľovi ako záporné čísla, ako dobropis očakávajú slovenskí a českí čitatelia.
verified: 19.0.1.0.1
---

## Na čo slúži {#purpose}

Odoo tlačí dobropis odberateľovi s kladnými sumami a to, že ide o opačný
pohyb, vyjadruje len nadpis. Slovenskí a českí účtovníci aj odberatelia
očakávajú, že dobropis ukáže zníženie **zápornými** sumami. Modul tlačený
doklad podľa toho upraví. V účtovníctve nemení nič.

## Čo sa na PDF zmení {#usage}

Na **dobropise odberateľovi** sa so znamienkom mínus vytlačia:

- jednotková cena a medzisúčet (alebo celková suma, ak sú ceny s daňou)
  každého riadku;
- medzisúčet každej sekcie;
- zoskupené riadky dokladu;
- blok súčtov: základ dane, daň podľa skupín daní a celková suma, pri
  dobropise v cudzej mene aj v mene spoločnosti.

Faktúry odberateľom, prijaté faktúry a **dobropisy od dodávateľov** si
znamienka ponechajú. Suma na úhradu, zoznam úhrad a platobný QR kód sa
nemenia. Nič sa nenastavuje: modul nainštalujte a tlačte.

## Obmedzenia {#limitations}

- Týka sa len dobropisov odberateľom; dobropisy od dodávateľov vytlačené z
  Odoo zostávajú kladné.
- Zápornú jednotkovú cenu zvolil modul ako spôsob zobrazenia: množstvo
  zostáva kladné.
