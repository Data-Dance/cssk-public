---
title: Detaily ukazovateľov MIS Builder
summary: Rozbalí ukazovateľ MIS Builder podľa partnera, produktu, denníka, mesiaca alebo iného poľa účtovných položiek, nielen podľa účtov.
verified: 19.0.1.0.1
---

## Na čo slúži {#purpose}

[module:mis_builder](module:mis_builder) vie pod ukazovateľom zobraziť jeho účty
(*Display details by account*). Otázka však často znie inak - ktorí zákazníci
tvoria tržby, v ktorých mesiacoch vznikli náklady. Tento modul umožní
ukazovateľ rozbaliť podľa ľubovoľného poľa účtovných položiek.

## Nastavenie {#setup}

Otvorte šablónu výkazu MIS a v nej ukazovateľ. Vedľa *Display details by
account*:

| Pole | Význam |
|---|---|
| Detaily podľa | Pole účtovných položiek: *Partner*, *Produkt*, *Denník*, *Analytický účet*, *Dátum* (riadok za mesiac)… |
| Najviac riadkov detailu | Najväčší počet riadkov detailu (predvolene 20); zobrazia sa hodnoty s najviac položkami. |

## Ako sa správa {#behaviour}

- Každý riadok detailu je ukazovateľ vypočítaný s filtrami stĺpca a touto
  hodnotou, v každom stĺpci výkazu - aj v stĺpcoch rozpadu.
- Rozkliknutie bunky detailu otvorí presne účtovné položky tejto hodnoty.
- Rozbalí sa len ukazovateľ vypočítaný priamo z účtovných výrazov (napríklad
  `-balp[60%]`). Ukazovateľ zložený z iných ukazovateľov zostane jedným
  riadkom: jeho detaily by vyžadovali prepočítať každý ukazovateľ, z ktorého
  vychádza, pre každú hodnotu.
- *Detaily podľa* a *Display details by account* sa navzájom vylučujú.
