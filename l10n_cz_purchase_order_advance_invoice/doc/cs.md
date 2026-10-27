---
title: Přijaté zálohové faktury — české účty
summary: Napojí nastavení přijatých zálohových faktur na českou účtovou osnovu.
verified: 19.0.1.0.1
family: purchase_order_advance_invoice#localization
---

Vyplní nastavení přijatých zálohových faktur každé společnosti s českou účtovou osnovou: vytvoří párovatelný zúčtovací účet typu závazek 314001 *Poskytnuté zálohy – zúčtování (daňový doklad)*, pro poskytnuté zálohy použije 314000 *Poskytnuté provozní zálohy* a vytvoří nákupní deník PDADV *Daňové doklady k odeslaným platbám*. Dlouhodobý účet nenastavuje.

Spustí se při instalaci pro společnosti, které už českou osnovu mají, a znovu pokaždé, když se osnova načte později, například pro novou společnost. Vyplní jen nastavení, která jsou ještě prázdná.
