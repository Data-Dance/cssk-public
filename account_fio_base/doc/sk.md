---
title: API Fio banky — spoločný klient a formáty
summary: Klient REST Fio banky, čítanie výpisov a XML platobných príkazov, ktoré zdieľajú všetky moduly Fio.
verified: 19.0.1.2.1
family: account_fio#api
---

Implementuje API Fio raz pre všetky moduly Fio: volania REST, pri ktorých sa každá zdokumentovaná chyba zmení na zrozumiteľné hlásenie, formáty výpisov Fio XML a JSON, XML platobných príkazov (`importIB.xsd`) s tuzemskými, SEPA a zahraničnými príkazmi, čítanie odpovede banky na odoslanie a číselník platobných titulov Českej národnej banky. Token odstraňuje z každého hlásenia a záznamu v logu.

Nemá obrazovku ani nastavenia. Inštaluje sa ako závislosť modulov Fio a potrebuje knižnicu Pythonu `requests`.
