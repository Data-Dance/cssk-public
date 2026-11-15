---
title: Slovenské okresy, obce a PSČ
summary: Všetky slovenské okresy, obce a PSČ, aby sa po zadaní PSČ alebo obce na kontakte doplnila obec, PSČ, okres aj krajina.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Modul OCA *Location management* (`base_location`) pridáva na kontakty a
spoločnosti pole **ZIP Location**: zadáte PSČ alebo začiatok názvu obce,
vyberiete zo zoznamu a adresa sa doplní. Sám však žiadne slovenské údaje
neobsahuje. Tento modul ich dopĺňa:

| V Odoo | Na Slovensku | Počet |
|---|---|---|
| Štát (State) | okres s krajom („okres Lučenec, Banskobystrický kraj“) | 79 |
| Mesto (City) | obec | približne 2 900 |
| PSČ (ZIP) | PSČ v tvare zo slovenských dokladov („985 13“) | približne 3 200 |

Obce s rovnakým názvom sú samostatné položky, každá vo svojom okrese (Lúčka
sú štyri), preto vyberajte podľa okresu uvedeného pri názve.

**Bratislava a Košice** sú po jednej obci so všetkými PSČ mesta a bez okresu:
mestská časť nemá pre poštu jeden okres a adresa sa tam píše „851 01
Bratislava“. Výber niektorého z ich PSČ vymaže okres, ktorý na kontakte zostal
z predchádzajúcej adresy.

## Inštalácia {#install}

S balíkom slovenskej lokalizácie sa neinštaluje. Ak chcete výber podľa PSČ,
nainštalujte ho z *Aplikácií*; `base_location` sa nainštaluje s ním.

## Odkiaľ sú údaje {#source}

Zo zoznamov, ktoré Slovenská pošta zverejňuje na posta.sk (obce, detail obcí
obsluhovaných viacerými poštami a zoznam ulíc miest s viacerými PSČ). Súbor
`data/SOURCE` v module uvádza, z ktorého stiahnutia vznikol. Novšia verzia
modulu pri aktualizácii pridá nové obce a PSČ; nikdy neodstráni ani
nepremenuje položku, ktorú už môžete mať na kontakte, a vaše úpravy položiek
zostanú zachované.
