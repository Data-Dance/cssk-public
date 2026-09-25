===========================================
Preddavkové faktúry – slovenská lokalizácia
===========================================

Prepája modul ``sale_order_advance_invoice`` so slovenskou účtovou osnovou. Po
inštalácii nastaví pre každú spoločnosť na slovenskej účtovej osnove účty a denník
pre faktúry k prijatým platbám.

.. contents:: Obsah
   :local:

Čo sa nastaví
=============

.. list-table::
   :header-rows: 1
   :widths: 40 18 42

   * - Rola
     - Účet
     - Názov
   * - Zúčtovací (clearing) účet preddavkov
     - **324001**
     - Prijaté preddavky – zúčtovanie (daňový doklad) — *vytvorí sa, je zúčtovateľný*
   * - Prijaté preddavky (krátkodobé)
     - **324000**
     - Prijaté preddavky
   * - Prijaté preddavky (dlhodobé)
     - **475000**
     - Dlhodobé prijaté preddavky
   * - Denník daňových dokladov
     - **TDADV**
     - Faktúry k prijatým platbám

Existujúce ručné nastavenie sa zachová – doplnia sa len prázdne polia.

Účtovný tok
===========

1. **Zálohová (proforma) faktúra** – výzva na platbu, *neúčtuje sa*.
2. **Prijatie platby** – banka 221 proti zúčtovaciemu účtu 324001.
3. **Faktúra k prijatej platbe** (do 15 dní od platby) – 324001 / 324000
   (základ) + 343 (DPH); zúčtovací účet sa spáruje s platbou a vráti na 0.
4. **Vyúčtovacia faktúra** – celé plnenie (311 / 604 + 343) a odpočet preddavku s
   vrátením DPH priznanej z preddavku.

Podrobnosti a interaktívny ťahák nájdete v module ``sale_order_advance_invoice``
(``static/description/advance_invoice_cheat_sheet.html``).

Kredity
=======

Autor: **Data Dance s.r.o.** — https://www.datadance.eu
Licencia: AGPL-3.0 alebo novšia (pozri súbor LICENSE).
