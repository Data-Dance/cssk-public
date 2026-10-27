---
title: Souhrnné hlášení CZ/SK — ověření ve VIES
summary: Při exportu ověří každý řádek souhrnného hlášení ve VIES a ponechá na řádku konzultační číslo VIES jako důkaz.
verified: 19.0.1.0.4
family: l10n_cssk_ec_summary_base#vies
---

Při exportu souhrnného hlášení se u každého DIČ odběratele zeptá služby VIES Evropské komise, zda je platné, a výsledek, konzultační číslo a čas ověření uloží na řádek. Neplatné číslo export zablokuje, aniž by se ztratily už získané důkazy; výpadek VIES export neblokuje a zaznamená se v chatteru.

Nainstaluje se sám, je-li nainstalován společný modul souhrnného hlášení i modul přímého ověření VIES (`l10n_cssk_vies`), a působí jen u společností se zapnutou volbou **Použít přímé EU VIES (bez IAP)**.
