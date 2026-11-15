---
title: Automatické doplňování partnerů z ARES
summary: Doplňuje české kontakty z Administrativního registru ekonomických subjektů (ARES) podle názvu firmy, IČO nebo DIČ.
verified: 19.0.1.4.0
family: partner_autocomplete_dispatcher#ares
---

Přidá ARES jako poskytovatele automatického doplňování partnerů. Český kontakt se v ARES vyhledá podle názvu firmy, podle IČO nebo podle DIČ právnické osoby a vyplní se jeho název, adresa, DIČ a — zvolíte-li pro ně pole — IČO, převažující činnost podle CZ-NACE 2025 a zápis ve veřejném rejstříku: rejstřík, rejstříkový soud, spisová značka, stav a data vzniku a zániku. Je-li nainstalován modul [module:l10n_cz_trade_registry](module:l10n_cz_trade_registry), zapisují se tyto údaje do jeho polí bez dalšího nastavování. České kontakty se v ARES vyhledávají ze všech společností bez ohledu na to, jakého poskytovatele si zvolila samotná společnost.

Vyžaduje modul pro přepínání poskytovatelů automatického doplňování, který s sebou nainstaluje, a nepotřebuje účet ani klíč. Jeho nastavení se zobrazí v *Nastavení → Obecná nastavení → Kontakty*, je-li ARES zvolen jako poskytovatel společnosti.
