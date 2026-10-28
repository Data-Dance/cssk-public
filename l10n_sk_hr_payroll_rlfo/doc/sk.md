---
title: SK RLFO — prihlásenie a odhlásenie zamestnancov
summary: Prihlášky a odhlášky zamestnancov do Sociálnej poisťovne zadané ako dávka udalostí a vyexportované do XML overeného voči oficiálnej schéme.
verified: 19.0.1.2.1
---

## Na čo slúži {#purpose}

Zamestnávateľ zamestnanca pred začatím práce prihlási do **Sociálnej
poisťovne** a po zániku poistenia ho odhlási. Tlačivom je *Registračný list
fyzickej osoby* (**RLFO**); modul vytvára jeho elektronickú dávku za
zamestnancov (schéma *RLZEC*) — jeden súbor s ľubovoľným počtom prihlášok
a odhlášok.

Na rozdiel od výkazov poistného sa RLFO **nezostavuje z výplatných pások**.
Udalosti zadávate sami; modul doplní typ vzťahu a osobné údaje zamestnanca,
vygeneruje XML a overí ho. Z modulu
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
používa len export, overenie a uchovanie podanej kópie, takže mzdové jadro
nepotrebuje — typ vzťahu však navrhne správne len vtedy, keď je nainštalovaný
niektorý zo slovenských mzdových modulov (pozri
[príručku slovenských miezd](module:l10n_sk_hr_payroll_base#employees)).

## Právny rámec {#legal}

Odkazy sú na [zákon o sociálnom poistení](law:sk/2003/461).

- **Prihlásenie a odhlásenie.** Podľa
  [§ 231 ods. 1 písm. b)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-b)
  zamestnávateľ prihlási zamestnanca na nemocenské, dôchodkové poistenie
  a poistenie v nezamestnanosti (zamestnanca podľa § 4 ods. 2 len na
  dôchodkové poistenie) **pred vznikom týchto poistení, najneskôr pred
  začatím výkonu činnosti**, odhlási ho **do ôsmich dní od zániku** týchto
  poistení a zruší prihlásenie, ak poistný vzťah nevznikol.
- **Prerušenie.** Prerušenie poistenia sa oznamuje do ôsmich dní —
  [§ 231 ods. 1 písm. d)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-d).
  Túto udalosť modul nevytvára.
- Tlačivo a spôsob zasielania určuje Sociálna poisťovňa —
  [§ 231 ods. 2](law:sk/2003/461#paragraf-231.odsek-2).

## Nastavenie {#setup}

- *IČO*, 8 až 12 číslic, na formulári spoločnosti.
- *Variabilný symbol Sociálnej poisťovne*, presne 10 číslic — vyplňte ho
  priamo vo formulári RLFO. Ukladá sa na spoločnosti a je spoločný s modulmi
  MVP, VPP a ELDP, takže sa zadáva raz. Na jeho zmenu treba právo upravovať
  spoločnosti.
- Pri zamestnancovi: **rodné číslo** v poli *Identifikačné č* (9 alebo 10
  číslic) a dátum narodenia (*Birthday*). Priezvisko a meno sa berú z mena
  zamestnanca: **posledné slovo je priezvisko**, všetko pred ním meno — mená
  zamestnancov píšte v poradí *Meno (mená) Priezvisko*. Ak je nainštalovaný
  `hr_employee_firstname`, použijú sa jeho samostatné polia pre meno a
  priezvisko.

## Zostavenie dávky {#usage}

*Mzdové hlásenia → SK RLFO (registrácie)*, potom *Nové*. *Rok* a *Mesiac*
dávku len pomenúvajú, udalosti neobmedzujú.

V časti *Registračné udalosti* pridajte riadok za každú udalosť:

| Stĺpec | Čo zadať |
|---|---|
| *Zamestnanec* | zamestnanca |
| *Typ udalosti* | *Prihláška* (`PA`) alebo *Odhláška* (`OD`) |
| *Typ vzťahu (typZec)* | navrhne sa zo zmluvy zamestnanca, dá sa zmeniť — pozri nižšie |
| *Vznik poistenia (datVznikPoist)* | povinný pri oboch typoch udalosti |
| *Zánik poistenia (datZaniku)* | povinný pri odhláške |

Typ vzťahu sa navrhne podľa polí zmluvy *Typ dohody* a *Pravidelný mesačný
príjem*:

| Zmluva | Pravidelný príjem | Nepravidelný príjem |
|---|---|---|
| pracovný pomer | ZEC | ZEC |
| DoVP | ZECD1 | ZECD1N |
| DoPČ | ZECD2 | ZECD2N |
| DoBPŠ | ZECD3 | ZECD3N |

*ZECN* (zamestnanec s nepravidelným príjmom) možno zvoliť ručne. Všetky kódy
dohôd vrátane DoBPŠ sa odhlasujú vetvou schémy pre dohody.

Potom **Generovať**. XML sa overí voči `RLZEC-v2026.xsd` a priloží; nahrajte
ho na portál Sociálnej poisťovne a kliknite na **Označiť ako odoslané**.
Odhláška sa zapíše do vetvy podľa typu vzťahu (dohoda, nepravidelný príjem
alebo pracovný pomer s pravidelným príjmom).

Generovanie sa zastaví, ak dávka nemá žiadnu udalosť, ak zamestnanec nemá
platné rodné číslo alebo ak chýba dátum, ktorý udalosť vyžaduje.

## Obmedzenia {#limitations}

- **Len dva typy udalostí:** prihláška a odhláška. Zmenu, prerušenie
  a zrušenie prihlásenia treba podať cez portál.
- **Zo zmluvy sa doplní len typ vzťahu.** Dátumy sa zadávajú ručne
  a nekontrolujú sa voči zmluve ani dátumu nástupu či odchodu; pri nástupe
  alebo odchode zamestnanca sa udalosť sama nevytvorí — dodržanie lehôt je na
  vás.
- Typ vzťahu sa navrhne pri výbere zamestnanca a neskôr sa voči skutočnému
  rozsahu poistenia znova nekontroluje.
- Bez samostatných polí pre meno sa za priezvisko berie len posledné slovo:
  dvojslovné priezvisko ako *Anna Mária Nová Kováčová* skontrolujte v XML.
- Kontaktné údaje v súbore sú telefón a e-mail spoločnosti a meno užívateľa,
  ktorý dávku generuje.
- Dodáva sa len vzor RLZEC 2026. Overenie voči schéme kontroluje tvar súboru,
  nie údaje.
