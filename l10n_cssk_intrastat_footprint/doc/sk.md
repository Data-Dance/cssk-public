---
title: Intrastat vo výskyte vo výkazoch (CZ/SK)
summary: Výskyt zaúčtovaného dokladu vo výkazoch uvedie aj hlásenia Intrastat, ktoré vykázali jeho riadky, s obdobím, tokom a stavom.
verified: 19.0.1.1.0
family: l10n_sk_intrastat#footprint
---

Doplní Intrastat do **výskytu vo výkazoch** zaúčtovaných faktúr a účtovných zápisov. Za každé hlásenie Intrastat modulu OCA, ktoré prevzalo niektorý riadok dokladu, ukáže formulár *Intrastat*, obdobie, tok (prijatie alebo odoslanie) a stav hlásenia s odkazom naň. Číta väzbu, ktorú si hlásenie uložilo pri generovaní riadkov, preto mesiac, za ktorý hlásenie ešte nebolo vygenerované, neukáže nič.

Nainštaluje sa sám, keď je prítomný [module:l10n_cssk_core](module:l10n_cssk_core) aj modul OCA `intrastat_product` — v databáze, ktorá mala oba skôr, než tento modul vznikol, ho treba raz nainštalovať ručne — a nemá nastavenia. Výkaz Intrastat v Odoo Enterprise nečíta.
