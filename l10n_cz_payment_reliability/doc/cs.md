---
title: CZ spolehlivost dodavatele — ADIS
summary: Český registr pro kontrolu spolehlivosti dodavatele — nespolehlivý plátce a zveřejněné bankovní účty ze služby ADIS Ministerstva financí.
verified: 19.0.1.2.0
family: l10n_cssk_payment_reliability#cz-provider
---

Odpovídá na kontrolu spolehlivosti dodavatele u českých dodavatelů: zeptá se webové služby ADIS Ministerstva financí, zda je dodavatel nespolehlivým plátcem a jaké bankovní účty má zveřejněné, převede zveřejněná tuzemská čísla účtů — i účet, na který platíte, zadaný v tuzemském tvaru — na IBAN a porovná je. Subjekt, který ADIS nevede jako plátce, označí jako neověřený, ne jako platbu na nezveřejněný účet. Jeden dotaz na kontrolu, bez klíče.

Instaluje se spolu s modulem kontroly spolehlivosti a českou účtovou osnovou (`l10n_cz`). Vlastní obrazovku ani nastavení nemá; uplatní se u dodavatelů, kteří mají zemi Česko a vyplněné *DIČ*.
