---
title: Súhrnný výkaz CZ/SK — overenie vo VIES
summary: Pri exporte overí každý riadok súhrnného výkazu vo VIES a ponechá na riadku konzultačné číslo VIES ako dôkaz.
verified: 19.0.1.0.4
family: l10n_cssk_ec_summary_base#vies
---

Pri exporte súhrnného výkazu sa pre každé IČ DPH odberateľa opýta služby VIES Európskej komisie, či je platné, a výsledok, konzultačné číslo a čas overenia uloží na riadok. Neplatné číslo export zablokuje bez straty už získaných dôkazov; výpadok VIES export neblokuje a zaznamená sa v chatteri.

Nainštaluje sa sám, keď je nainštalovaný spoločný modul súhrnného výkazu aj modul priameho overenia VIES (`l10n_cssk_vies`), a pôsobí len pri spoločnostiach so zapnutou voľbou **Použiť priame EU VIES (bez IAP)**.
