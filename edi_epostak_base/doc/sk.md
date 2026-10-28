---
title: ePošťák — základ
summary: Zaregistruje ePošťák ako poskytovateľa EDI, obsahuje prepínač testovacieho a produkčného prostredia a ID firmy a kontroluje Peppol adresy, s ktorými sa volá ePošťák.
verified: 19.0.1.1.0
family: edi_epostak_peppol#setup
---

Zaregistruje poskytovateľa **ePošťák** na EDI správach, pridá do *Nastavenia → EDI* prepínač prostredia (*ePošťák Environment*: Sandbox / Production, pre celú databázu) a **ID firmy** každej spoločnosti (*ePošťák Firm ID*), vyzdvihuje doklady každej spoločnosti ako táto spoločnosť, pri vzniku každej správy na ňu zapíše prostredie a správy ePošťáka odosiela naplánovanou akciou, bez fronty úloh. Údaje na smerovanie v sieti Peppol číta zo samotného dokladu a zrozumiteľným hlásením odmietne spoločnosť, ktorej Peppol adresa chýba alebo pod schémou 0245 neobsahuje desaťmiestne DIČ. Pridáva aj naplánovanú akciu *ePošťák: Poll Inbound Documents*.

Inštaluje sa s modulom [module:edi_epostak_peppol](module:edi_epostak_peppol); sám sa nikam nepripája — pripojenie zabezpečuje [module:edi_epostak_connector_sapi](module:edi_epostak_connector_sapi).
