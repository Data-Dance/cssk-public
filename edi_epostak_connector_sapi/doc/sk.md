---
title: ePošťák — konektor (SAPI-SK 1.0)
summary: Pripojenie k prístupovému bodu ePošťák — prihlasovacie údaje, odosielanie, vyzdvihovanie prijatých dokladov, stav doručenia a kontrola dosiahnuteľnosti v sieti Peppol.
verified: 19.0.1.1.2
family: edi_epostak_peppol#statuses
---

Komunikuje s ePošťákom cez rozhranie SAPI-SK 1.0: prihlási sa pomocou **Client ID** a **Client Secret** aktívneho prostredia, odošle každý doklad Peppol (*Sent* znamená prevzatý na prenos, nie doručený), vyzdvihne doklady čakajúce na vašu Peppol adresu a potvrdí ich až po uložení a každých 30 minút sa ePošťáka pýta, či boli odoslané doklady doručené (*Done*) alebo zlyhali (*Error*). Pridáva tlačidlo **Test Connection**, riadok **Last inbound poll** s tlačidlom **Poll inbound now**, aktivitu To-Do po opakovanom zlyhaní vyzdvihovania, nastavenia *Transfer Tuning* a tlačidlo **Check Peppol reachability** na kontaktoch.

Inštalujte ho spolu s modulom [module:edi_epostak_peppol](module:edi_epostak_peppol); celé nastavenie opisuje [návod k ePošťáku](module:edi_epostak_peppol#setup).
