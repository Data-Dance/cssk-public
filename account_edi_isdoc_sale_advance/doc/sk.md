---
title: ISDOC — zálohové faktúry
summary: Daňový doklad k prijatej platbe exportuje ako ISDOC typu 5 (jeho dobropis ako 6) a zálohy odpočítané na konečnej faktúre vykazuje ako zálohy.
verified: 19.0.1.0.0
family: account_edi_isdoc#advances
---

Mapuje reťaz záloh modulu [module:sale_order_advance_invoice](module:sale_order_advance_invoice) na ISDOC: daňový doklad k prijatej platbe sa exportuje ako typ dokladu **5**, jeho dobropis ako **6** a na konečnej faktúre sa každý odpočet zálohy vykáže ako zdanená alebo nezdanená záloha s číslom a variabilným symbolom daňového dokladu k zálohe a s už uplatnenou DPH, nie ako bežný riadok.

Nainštaluje sa sám, keď sú nainštalované moduly [module:account_edi_isdoc_sale](module:account_edi_isdoc_sale) aj [module:sale_order_advance_invoice](module:sale_order_advance_invoice), a nemá žiadne nastavenia.
