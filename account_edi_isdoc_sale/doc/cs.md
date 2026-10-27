---
title: ISDOC — zálohové faktury z prodejních objednávek
summary: Stáhne prodejní objednávku jako zálohovou fakturu ISDOC (typ dokladu 4, výzva k platbě zálohy) z nabídky Akce na objednávce.
verified: 19.0.1.1.0
family: account_edi_isdoc#proforma
---

Přidá export prodejní objednávky jako **zálohové faktury** ISDOC 6.0.2, typ dokladu 4: číslo a datum objednávky, řádky, součty a první bankovní účet společnosti s číslicemi čísla objednávky jako variabilním symbolem. UUID se uloží na objednávce, takže opakovaný export nese stejnou identitu. Na objednávce ji **Akce → Download ISDOC Proforma** stáhne jako `S00042.isdoc` a ponechá jako přílohu objednávky, při každém stažení nahrazenou, aby vždy odpovídala aktuální objednávce. Zrušenou objednávku exportovat nelze a chybí-li název nebo adresa vaší společnosti či odběratele, místo souboru se zobrazí jejich seznam. Integrace mohou tentýž export volat přímo.

Nainstaluje se sám, je-li nainstalován modul [module:account_edi_isdoc](module:account_edi_isdoc) i Prodej, a nemá žádná nastavení.
