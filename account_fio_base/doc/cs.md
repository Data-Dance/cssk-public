---
title: API Fio banky — společný klient a formáty
summary: Klient REST Fio banky, čtení výpisů a XML platebních příkazů, které sdílejí všechny moduly Fio.
verified: 19.0.1.2.1
family: account_fio#api
---

Implementuje API Fio jednou pro všechny moduly Fio: volání REST, u nichž se každá zdokumentovaná chyba změní na srozumitelné hlášení, formáty výpisů Fio XML a JSON, XML platebních příkazů (`importIB.xsd`) s tuzemskými, SEPA a zahraničními příkazy, čtení odpovědi banky na odeslání a číselník platebních titulů České národní banky. Token odstraňuje z každého hlášení a záznamu v logu.

Nemá obrazovku ani nastavení. Instaluje se jako závislost modulů Fio a potřebuje knihovnu Pythonu `requests`.
