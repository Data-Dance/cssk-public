=========================================
Zálohové faktury – česká lokalizace
=========================================

Propojuje modul ``sale_order_advance_invoice`` s českou účtovou osnovou. Po
instalaci nastaví pro každou společnost na české účtové osnově účty a deník pro
daňové doklady k přijatým platbám.

.. contents:: Obsah
   :local:

Co se nastaví
=============

.. list-table::
   :header-rows: 1
   :widths: 40 18 42

   * - Role
     - Účet
     - Název
   * - Zúčtovací (clearing) účet záloh
     - **324001**
     - Přijaté zálohy – zúčtování (daňový doklad) — *vytvoří se, je zúčtovatelný*
   * - Přijaté zálohy (krátkodobé)
     - **324000**
     - Přijaté provozní zálohy
   * - Přijaté zálohy (dlouhodobé)
     - **475000**
     - Dlouhodobé přijaté zálohy
   * - Deník daňových dokladů
     - **TDADV**
     - Daňové doklady k přijatým platbám

Stávající ruční nastavení se zachová – doplní se jen prázdná pole.

Účetní tok
==========

1. **Zálohová (proforma) faktura** – výzva k platbě, *neúčtuje se*.
2. **Přijetí platby** – banka 221 proti zúčtovacímu účtu 324001.
3. **Daňový doklad k přijaté platbě** (do 15 dnů od platby) – 324001 / 324000
   (základ) + 343 (DPH); zúčtovací účet se spáruje s platbou a vrátí na 0.
4. **Vyúčtovací faktura** – celé plnění (311 / 604 + 343) a odečet zálohy s
   vratkou DPH přiznané ze zálohy.

Podrobnosti a interaktivní tahák najdete v modulu ``sale_order_advance_invoice``
(``static/description/advance_invoice_cheat_sheet.html``).

Kredity
=======

Autor: **Data Dance s.r.o.** — https://www.datadance.eu
Licence: AGPL-3.0 or later (viď súbor LICENSE).
