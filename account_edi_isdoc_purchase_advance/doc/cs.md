---
title: ISDOC — přijaté zálohové faktury
summary: Importovaná zálohová faktura ISDOC vytvoří přijatou zálohu místo faktury k zaúčtování a daňový doklad dodavatele k vaší platbě půjde do deníku a na účty záloh, propojený se zálohou.
verified: 19.0.1.0.1
family: account_edi_isdoc#received-advances
---

Směruje importované zálohové doklady do modulu [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice). **Zálohová faktura** (typ 4) vytvoří přijatou zálohu na hrubou částku dokladu a koncept faktury z importu se označí jako nezaúčtovatelný. Opakovaný import téže zálohové faktury — stejný dodavatel, stejné číslo dodavatele, záloha není zrušená — druhou zálohu nevytvoří: nový koncept se propojí s existující. **Daňový doklad k vaší platbě** (typ 5, opravný doklad 6) se přesune do deníku daňových dokladů k přijatým zálohám, převezme DUZP ze souboru, řádky se přeúčtují na účet zaplacených záloh a závazek na zúčtovací účet a propojí se s odpovídající otevřenou zálohou — podle odkazu na objednávku, variabilního symbolu nebo jedinečné zaplacené částky; není-li to jednoznačné, historie vyzve k ručnímu propojení. Přidá produkt *Advance payment (imported)*.

Nainstaluje se sám, je-li nainstalován modul [module:account_edi_isdoc](module:account_edi_isdoc) i [module:purchase_order_advance_invoice](module:purchase_order_advance_invoice); deník a účty jsou ty, které jsou nastaveny pro přijaté zálohy.
