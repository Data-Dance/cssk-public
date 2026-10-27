---
title: ISDOC — prijaté zálohové faktúry
summary: Importovaná zálohová faktúra ISDOC vytvorí prijatú zálohu namiesto faktúry na zaúčtovanie a daňový doklad dodávateľa k vašej platbe pôjde do denníka a na účty záloh, prepojený so zálohou.
verified: 19.0.1.0.1
family: account_edi_isdoc#received-advances
---

Smeruje importované zálohové doklady do modulu [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice). **Zálohová faktúra** (typ 4) vytvorí prijatú zálohu na hrubú sumu dokladu a koncept faktúry z importu sa označí ako nezaúčtovateľný. Opakovaný import tej istej zálohovej faktúry — rovnaký dodávateľ, rovnaké číslo dodávateľa, záloha nie je zrušená — druhú zálohu nevytvorí: nový koncept sa prepojí s existujúcou. **Daňový doklad k vašej platbe** (typ 5, dobropis 6) sa presunie do denníka daňových dokladov k prijatým zálohám, prevezme dátum zdaniteľného plnenia zo súboru, riadky sa preúčtujú na účet zaplatených preddavkov a záväzok na zúčtovací účet a prepojí sa so zodpovedajúcou otvorenou zálohou — podľa odkazu na objednávku, variabilného symbolu alebo jedinečnej zaplatenej sumy; ak to nie je jednoznačné, história vyzve na ručné prepojenie. Pridá produkt *Advance payment (imported)*.

Nainštaluje sa sám, keď je nainštalovaný modul [module:account_edi_isdoc](module:account_edi_isdoc) aj [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice); denník a účty sú tie, ktoré sú nastavené pre prijaté zálohy.
