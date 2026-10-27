---
title: Platobný režim — úhrada pri zaúčtovaní
summary: Platobný režim môže zaregistrovať úhradu hneď pri zaúčtovaní faktúry — pri predaji zaplatenom na mieste v hotovosti alebo kartou.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Keď odberateľ zaplatí pri pulte v hotovosti alebo kartou, faktúra je
uhradená v okamihu, keď vznikne. Úhradu registrovať zvlášť je len príležitosť
na ňu zabudnúť — a otvorená faktúra sa potom objaví v pohľadávkach aj v
upomienkach.

Modul pridá do platobných režimov OCA (`account_payment_mode`) jednu voľbu:
faktúra, ktorej platobný režim ju má, sa **pri zaúčtovaní automaticky uhradí
v plnej výške** v denníku určenom platobným režimom.

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Payment Modes* (modul nemá slovenský preklad,
preto sú jeho označenia anglické). Vytvorte alebo otvorte platobný režim,
napríklad *Hotovosť* alebo *Karta*:

| Pole | Hodnota |
|---|---|
| Payment Type | Inbound pre faktúry odberateľom |
| Link to Bank Account | **Fixed** |
| Fixed Bank Journal | denník, do ktorého peniaze prichádzajú — pokladnica pri hotovosti, zúčtovací denník kariet pri kartách |
| **Register payment on validation** (*registrovať úhradu pri zaúčtovaní*) | zaškrtnuté |

Začiarkavacie políčko sa zobrazí, len keď je *Link to Bank Account* nastavené
na *Fixed*, a režim s ním nemožno uložiť bez pevného denníka.

Platobný režim nastavte na faktúre (pole *Payment Mode*) alebo ako
predvolený platobný režim odberateľa na kontakte, aby ho nové faktúry dostali
samy.

## Čo sa stane pri zaúčtovaní {#usage}

Keď sa zaúčtuje faktúra, ktorej platobný režim má voľbu **Register payment on
validation**:

- vytvorí sa úhrada na **celú zostávajúcu sumu** a spáruje sa s faktúrou,
  cez štandardného sprievodcu Odoo na registráciu úhrady — rovnaká úhrada,
  akú by ste zaregistrovali ručne;
- v pevnom denníku platobného režimu;
- s **dátumom faktúry** (ak chýba, s dátumom účtovania).

Faktúra je potom *Zaplatené*, alebo *V platbe*, ak denník používa účet
neidentifikovaných príjmov a čaká na bankový výpis.

Rovnako to funguje pri dobropisoch odberateľom, prijatých faktúrach a
pokladničných dokladoch s takým platobným režimom. Faktúra, ktorá je už
uhradená alebo na nej nič nezostáva, zostane bez zmeny. Viac faktúr
zaúčtovaných naraz dostane každá vlastnú úhradu.

## Obmedzenia {#limitations}

- Úhrada je vždy na celú sumu. Pri čiastočne zaplatenom predaji použite
  platobný režim bez tejto voľby a úhradu zaregistrujte sami.
- Úhrada má dátum faktúry, nie okamihu zaúčtovania. Ak zaúčtujete faktúru so
  starším dátumom, aj úhrada bude mať starší dátum.
- Ak sa úhrada nedá vytvoriť — napríklad denník nemá vhodný spôsob platby —
  nezaúčtuje sa ani faktúra.
- Modul úhradu len zaznamená. Nevystaví pokladničný doklad z registračnej
  pokladnice a nekomunikuje s platobným terminálom.
