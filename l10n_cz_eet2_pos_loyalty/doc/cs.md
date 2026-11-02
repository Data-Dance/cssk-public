---
title: Místo prodeje — česká EET 2.0 pro dárkové karty a elektronické peněženky
summary: Oznamuje nabití a čerpání dárkových karet a elektronických peněženek u pokladny ve dvou zvláštních položkách EET 2.0, takže každé nabití i každé čerpání je evidovanou tržbou.
verified: 19.0.1.0.1
family: l10n_cz_eet2_pos#scope
---

Dárková karta nebo elektronická peněženka je platební prostředek použitelný jen v omezené síti a zákon o evidenci tržeb považuje jak její **nabití**, tak **každé čerpání** u pokladny za evidovanou tržbu. Datová zpráva pro ně má dvě položky: částku určenou k následnému čerpání (*urceno_cerp_zuct*) při nabití a částku čerpanou (*cerp_zuct*) při uplatnění, obě započtené i do celkové částky. Zákazník, který si na peněženku nabije 1 000 Kč a hotově koupí nápoj za 50 Kč, se oznámí jako tržba 1 050 s 1 000 určenými k čerpání; pozdějších 300 Kč zaplacených z peněženky se oznámí jako tržba 300 z ní čerpaných. Vratka je totéž se záporným znaménkem.

Tento modul plní tyto položky z věrnostních programů Místa prodeje: řádek prodeje dárkové karty či elektronické peněženky je nabitím, řádek uplatnění čerpáním a objednávka uhrazená celá z peněženky se eviduje, přestože u pultu žádné peníze nemění majitele. Poukaz na jeden konkrétní výrobek nebo službu prostředkem omezené sítě není — jeho prodej je běžnou tržbou a jeho uplatnění není platbou —, takové poukazy proto veďte jako běžné produkty, ne jako dárkové karty.

Nainstaluje se sám, jsou-li nainstalovány [module:l10n_cz_eet2_pos](module:l10n_cz_eet2_pos) i věrnostní modul Místa prodeje, a žádné vlastní nastavení nemá.
