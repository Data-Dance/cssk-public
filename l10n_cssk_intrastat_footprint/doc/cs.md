---
title: Intrastat ve výskytu ve výkazech (CZ/SK)
summary: Výskyt zaúčtovaného dokladu ve výkazech uvede i výkazy pro Intrastat, které vykázaly jeho řádky, s obdobím, směrem a stavem.
verified: 19.0.1.1.0
family: l10n_cz_intrastat_oca#footprint
---

Doplní Intrastat do **výskytu ve výkazech** zaúčtovaných faktur a účetních zápisů. Za každý výkaz Intrastat modulu OCA, který převzal některý řádek dokladu, ukáže formulář *Intrastat*, období, směr (přijetí nebo odeslání) a stav výkazu s odkazem na něj. Čte vazbu, kterou si výkaz uložil při generování řádků, proto měsíc, za který výkaz ještě nebyl vygenerován, neukáže nic.

Nainstaluje se sám, je-li přítomen [module:l10n_cssk_core](module:l10n_cssk_core) i modul OCA `intrastat_product` — v databázi, která měla oba dříve, než tento modul vznikl, je třeba jej jednou nainstalovat ručně — a nemá nastavení. Výkaz Intrastat v Odoo Enterprise nečte.
