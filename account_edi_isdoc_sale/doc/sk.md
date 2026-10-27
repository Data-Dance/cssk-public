---
title: ISDOC — zálohové faktúry z predajných objednávok
summary: Stiahne predajnú objednávku ako zálohovú faktúru ISDOC (typ dokladu 4, výzva na zaplatenie zálohy) z ponuky Akcia na objednávke.
verified: 19.0.1.1.0
family: account_edi_isdoc#proforma
---

Pridá export predajnej objednávky ako **zálohovej faktúry** ISDOC 6.0.2, typ dokladu 4: číslo a dátum objednávky, riadky, súčty a prvý bankový účet spoločnosti s číslicami čísla objednávky ako variabilným symbolom. UUID sa uloží na objednávke, takže opakovaný export nesie rovnakú identitu. Na objednávke ho **Akcia → Download ISDOC Proforma** stiahne ako `S00042.isdoc` a ponechá ako prílohu objednávky, pri každom stiahnutí nahradenú, aby vždy zodpovedala aktuálnej objednávke. Zrušenú objednávku exportovať nemožno a ak chýba názov alebo adresa vašej spoločnosti či odberateľa, namiesto súboru sa zobrazí ich zoznam. Integrácie môžu ten istý export volať priamo.

Nainštaluje sa sám, keď je nainštalovaný modul [module:account_edi_isdoc](module:account_edi_isdoc) aj Predaj, a nemá žiadne nastavenia.
