---
title: Bankové napojenia — hlavička denníka
summary: Jedna hlavička vo formulári bankového denníka, kam každé bankové napojenie dáva svoje akcie.
verified: 19.0.1.0.0
---

Formulár bankového denníka v Odoo nemá hlavičku, preto každé bankové napojenie dávalo svoje tlačidlá niekam do tela formulára, tie pre Tatra banku dokonca do vlastnej záložky. Tento modul pridá do formulára každého bankového denníka jednu hlavičku a moduly bankových napojení (Tatra banka Premium API, Fio banka) v nej zobrazia svoje akcie: *Stiahnuť transakcie*, *Stiahnuť obdobie…*, *Znova načítať z banky* a podobne. Každé tlačidlo sa ukáže len vtedy, keď je jeho napojenie nastavené v poli *Bankové pohyby* denníka.

Nemá vlastnú obrazovku ani nastavenia. Inštaluje sa ako závislosť modulov bankových napojení.
