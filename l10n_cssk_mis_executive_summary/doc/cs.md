---
title: Přehled pro vedení CZ/SK
summary: Jednostránkový přehled MIS Builder pro českou a slovenskou účtovou osnovu - peníze, tržby a marže, doba inkasa a splatnosti, běžná likvidita a rentabilita aktiv.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Údaje, na které se vedení ptá nejdřív, na jedné stránce a přímo z účetnictví:
co přišlo a odešlo z peněz, co se prodalo a s jakou marží, jak dlouho platí
zákazníci a jak dlouho my a zda jsou krátkodobé dluhy kryty. Je to šablona pro
[module:mis_builder](module:mis_builder) postavená na třídách účtů, které mají
česká a slovenská osnova společné.

## Použití {#usage}

*Účetnictví › Výkazy › MIS Reports*, *Nový*, šablona **Přehled pro vedení
(CZ/SK)**, a přidejte sloupce, které potřebujete - tento měsíc, tento rok,
stejné období loni, porovnání. Údaje se řídí daty a filtry sloupce; každý lze
rozkliknout na účetní položky.

## Z čeho se údaje skládají {#figures}

| Údaj | Účty |
|---|---|
| Peníze a banka na začátku / na konci | 21x, 22x, 261 - počáteční a konečný zůstatek |
| Příjmy / výdaje peněz | pohyb má dáti / dal na 21x, 22x, 261 (převody mezi pokladnou a bankou se započtou na obou stranách) |
| Tržby | zůstatek na straně dal 60x |
| Náklady na prodané zboží a materiál | 501, 504 |
| Hrubý zisk | tržby − náklady na prodané zboží a materiál |
| Výnosy celkem / Náklady celkem | třída 6 / třída 5 |
| Výsledek hospodaření | výnosy celkem − náklady celkem |
| Hrubá / čistá marže | hrubý zisk / výsledek ÷ tržby |
| Pohledávky / závazky z obchodních vztahů | konečný zůstatek 311 / 321 |
| Doba inkasa pohledávek | pohledávky ÷ tržby × dny období |
| Doba splatnosti závazků | závazky ÷ nákupy (účtové skupiny 50 a 51) × dny období |
| Běžná likvidita | oběžná aktiva (třída 1, peníze, debetní zůstatky 31x, 33x–35x, 37x, 38x) ÷ krátkodobé závazky (kreditní zůstatky 23x, 24x, 32x–34x, 36x–38x) |
| Rentabilita aktiv | výsledek ÷ aktiva celkem (třídy 0 a 1, debetní zůstatky tříd 2 a 3) |

Marže a ukazatele se v součtovém sloupci nesčítají; zůstatky také ne.

## Omezení {#limitations}

Jde o manažerské ukazatele z tříd účtů, ne o účetní závěrku: společnost, která
účtuje na neobvyklé účty, si může šablonu zkopírovat a upravit (*Duplicate*
v MIS Builder). Rentabilita aktiv používá výsledek období, za měsíc je to tedy
měsíční údaj.
