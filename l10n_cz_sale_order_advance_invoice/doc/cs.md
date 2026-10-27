---
title: Zálohové faktury — české účty
summary: Napojí nastavení zálohových faktur na českou účtovou osnovu.
verified: 19.0.1.1.0
family: sale_order_advance_invoice#localization
---

Vyplní nastavení zálohových faktur každé společnosti s českou účtovou osnovou: vytvoří párovatelný zúčtovací účet 324001 *Přijaté zálohy – zúčtování (daňový doklad)*, pro krátkodobé přijaté zálohy použije 324000 *Přijaté provozní zálohy*, pro dlouhodobé 475000 *Dlouhodobé přijaté zálohy* a deník TDADV pojmenuje *Daňové doklady k přijatým platbám*.

Instalujte ho spolu s modulem zálohových faktur na české společnosti. Spustí se při instalaci a znovu pokaždé, když se česká osnova načte později, například pro novou společnost, a vyplní jen nastavení, která jsou ještě prázdná.
