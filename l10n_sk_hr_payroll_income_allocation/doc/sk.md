---
title: Register historických sociálnych základov
summary: Overené fondové základy a dátumované poistné pri dodatočnom príjme; podklad pre vyplácajúcu pásku a ZECN vo VPP.
verified: 19.0.1.2.0
---

## Účel {#purpose}

Rozpočítanie príjmu po zániku poistenia do mesiacov posledného roka podľa
[§139b](law:sk/2003/461#paragraf-139b). Fondy zamestnanca a zamestnávateľa sú
samostatné. Presné zlomky zostávajú pre ďalší doplatok; základy a poistné sú
zaokrúhlené po mesiacoch. Mesiac s doloženým zaplatením z maxima sa vylúči,
prebytok pri blízkom maxime sa neprerozdelí. Úrazový fond je bez stropu.

## Postup {#operation}

V mzdových výkazoch vytvorte register. Vyplňte dátumy, pridelené IČPV, hrubý
doplatok a odkazy na podklady. **Pripraviť editovateľnú históriu** vytvorí
riadky mesiac × fond. Pri každom overte poistenie, presný neznížený základ,
pôvodný vymeriavací základ, nominálnu uplatnenú OOP, efektívny strop, skutočné
zaplatenie z maxima a podklad. Príprava neurčuje právny nárok. Bez podkladu pri
každom riadku sa výpočet zablokuje. Je to editovateľný náhradný postup pre
históriu mimo Odoo; automatický import potvrdených pások je ďalšia etapa.

Vypočítajte základy, doplňte overenie štandardného krytia bez osobitných úľav a
vypočítajte poistné. OOP, maximum aj sadzby sa čítajú z natívnych dátumovaných
parametrov pre historický mesiac. Uzamknutie na rok2027 bolo odstránené.
Chýbajúci historický parameter vyvolá chybu; nové právne hodnoty treba ďalej
overovať a udržiavať. Efektívny strop môže byť nižší než zákonné maximum.

Voliteľný skrytý JSON ledger zostáva pre API. Nesmie sa kombinovať s riadkami.
Oba vstupy pokrývajú všetkých dvanásť fondov a všetky mesiace vrátane nepoistených.

## Podklady a nadväznosť {#integration}

Výpočet archivuje vstupy, výsledky a kontrolné súčty. Reset zachová prílohy;
vypočítané riadky nemožno meniť. Zmena parametrov zneplatní opakovanie.

Cieľ: **historické podklady → základy → poistné → natívna páska, daň, zdravotné
a účtovanie → fondový ZECN vo VPP**. Fondové riadky majú napájať VPP a ten istý
register vyplácajúcu pásku. Obyčajné mzdové pravidlá ani ochrana obdobia vzťahu
sa týmto modulom nevypínajú.

Zatiaľ chýba automatický import histórie, rozhodovanie o nárokoch, osobitné
úľavy, záporné opravy, daň, zdravotné, zaúčtovanie pásky, oficiálny VPP a prijatie
úradom. Modul samostatne neuzatvára #12. Syntetické budúce parametre v testoch
preverujú dátumový mechanizmus, nie budúce zákonné hodnoty.
