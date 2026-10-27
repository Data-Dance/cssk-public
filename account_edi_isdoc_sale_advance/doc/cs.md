---
title: ISDOC — zálohové faktury
summary: Daňový doklad k přijaté platbě exportuje jako ISDOC typu 5 (jeho opravný doklad jako 6) a zálohy odečtené na vyúčtovací faktuře vykazuje jako zálohy.
verified: 19.0.1.0.0
family: account_edi_isdoc#advances
---

Mapuje řetěz záloh modulu [module:sale_order_advance_invoice](module:sale_order_advance_invoice) na ISDOC: daňový doklad k přijaté platbě se exportuje jako typ dokladu **5**, jeho opravný doklad jako **6** a na vyúčtovací faktuře se každý odpočet zálohy vykáže jako zdaněná nebo nezdaněná záloha s číslem a variabilním symbolem daňového dokladu k záloze a s již uplatněnou DPH, ne jako běžný řádek.

Nainstaluje se sám, jsou-li nainstalovány moduly [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) i [module:sale_order_advance_invoice](module:sale_order_advance_invoice), a nemá žádná nastavení.
