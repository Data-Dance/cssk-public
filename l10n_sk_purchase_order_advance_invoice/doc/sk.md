---
title: Prijaté zálohové faktúry — slovenské účty
summary: Napojí nastavenia prijatých zálohových faktúr na slovenskú účtovú osnovu.
verified: 19.0.1.0.1
family: purchase_order_advance_invoice#localization
---

Vyplní nastavenia prijatých zálohových faktúr každej spoločnosti so slovenskou účtovou osnovou: vytvorí párovateľný zúčtovací účet typu záväzok 314001 *Poskytnuté preddavky – zúčtovanie (daňový doklad)*, pre poskytnuté preddavky použije 314000 *Poskytnuté preddavky* a vytvorí nákupný denník PDADV *Faktúry k odoslaným platbám*. Dlhodobý účet nenastavuje.

Spustí sa pri inštalácii pre spoločnosti, ktoré už slovenskú osnovu majú, a znova vždy, keď sa osnova načíta neskôr, napríklad pre novú spoločnosť. Vyplní len nastavenia, ktoré sú ešte prázdne.
