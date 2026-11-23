---
title: SK RLFO — prihlásenie a odhlásenie zamestnancov
summary: Prihlášky a odhlášky zamestnancov do Sociálnej poisťovne a oznámenie OOP z dohody, zadané ako dávka udalostí a vyexportované do XML overeného voči oficiálnej schéme.
verified: 19.0.1.4.1
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
- **Štatutári s účasťou.** Pri prihlásení zamestnávateľ oznamuje, či je
  zamestnanec štatutárnym orgánom alebo členom štatutárneho orgánu
  s **najmenej 50 % účasťou na majetku zamestnávateľa**, a každú zmenu tejto
  skutočnosti do ôsmich dní —
  [§ 231 ods. 1 písm. o)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-o).
  V prihláške je to prvok `zamSUcastou`.
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
udalosti neobmedzujú, ale určujú vzor: dávka za január 2027 a neskôr sa
vygeneruje v schéme RLZEC 2027, skoršia v RLZEC 2026.

V časti *Registračné udalosti* pridajte riadok za každú udalosť:

| Stĺpec | Čo zadať |
|---|---|
| *Zamestnanec* | zamestnanca |
| *Typ udalosti* | *Prihláška* (`PA`), *Odhláška* (`OD`) alebo *Zmena (OOP z dohody)* (`ZM`) |
| *Typ vzťahu (typZec)* | navrhne sa zo zmluvy zamestnanca, dá sa zmeniť — pozri nižšie |
| *Vznik poistenia (datVznikPoist)* | povinný pri oboch typoch udalosti |
| *Zánik poistenia (datZaniku)* | povinný pri odhláške |
| *Zmena platí od (datUplatnenia)* | povinný pri zmene |
| *Oznámenie uplatnenia OOP (datOznUplatnOop)* | prihláška alebo zmena pri dohode: deň, keď pracovník oznámil uplatnenie OOP; navrhne sa zo zmluvy |
| *OOP z dôvodu MD/OD/RD (uplatnOopMdOdRd)* | OOP si uplatňuje osoba na materskej, otcovskej alebo rodičovskej dovolenke; navrhne sa zo zmluvy |
| *Oznámenie ukončenia OOP (datOznUkoncUplatnOop)* | zmena: deň, keď pracovník oznámil, že si OOP ďalej neuplatňuje (skrytý stĺpec) |
| *Skončenie MD/OD/RD (datSkonceniaMdOdRd)* | zmena: posledný deň dovolenky (skrytý stĺpec) |
| *Štatutár s účasťou 50 % a viac* | pri prihláške: *Neoverené* (predvolené), *Nie je štatutárnym orgánom ani jeho členom s najmenej 50 % účasťou* alebo *Štatutárny orgán alebo jeho člen s najmenej 50 % účasťou* |
| *Doklad o účasti* | pri prihláške: odkiaľ odpoveď pochádza a k akému dátumu — výpis z obchodného registra, rozhodnutie spoločníkov alebo „bežný zamestnanec, bez štatutárnej funkcie“ |

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

Stav účasti je skutočnosť ku dňu prihlásenia a zadáva sa pri každej udalosti.
Neberie sa z políčka zamestnanca *Oslobodený od garančného poistenia*, ktoré
sa neskôr môže zmeniť. Po vygenerovaní dávky sú obe polia zamknuté; na opravu
vráťte dávku do konceptu.

### Odvodová odpočítateľná položka z dohody {#oop}

Zamestnávateľ oznamuje uplatnenie odvodovej odpočítateľnej položky na dohode
a jeho ukončenie najneskôr v prvý pracovný deň po dni, keď mu to pracovník
oznámil
([§ 231 ods. 1 písm. e)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-e)).

- **Uplatnenie pri vzniku dohody:** vyplňte *Oznámenie uplatnenia OOP* na
  prihláške.
- **Uplatnenie alebo ukončenie neskôr:** pridajte riadok *Zmena (OOP z
  dohody)* s dňom, od ktorého zmena platí, a s príslušným dátumom oznámenia —
  uplatnenia alebo ukončenia.
- **Rodič na materskej, otcovskej alebo rodičovskej dovolenke** (DoVP a
  DoPČ, od roku 2027): zaškrtnite aj *OOP z dôvodu MD/OD/RD*. Keď sa
  dovolenka skončí, podajte zmenu s poľom *Skončenie MD/OD/RD*. Obe polia má
  až vzor RLZEC 2027, preto musí byť dávka za január 2027 alebo neskôr;
  uplatnenie oznámené v decembri 2026 na január patrí do dávky za január
  2027.

Uplatnenie, dôvod a dátum oznámenia sa navrhnú z polí zmluvy *OOP z dohody*,
*Dôvod OOP* a *Oznámenie o OOP doručené*; skontrolujte ich, neskôr sa znova
nenačítajú. Polia OOP sa dajú použiť len pri typoch vzťahu pre dohody.

Potom **Generovať**. XML sa overí voči schéme vzoru (`RLZEC-v2026.xsd` alebo
`RLZEC-v2027.xsd`) a priloží; nahrajte
ho na portál Sociálnej poisťovne a kliknite na **Označiť ako odoslané**.
Odhláška sa zapíše do vetvy podľa typu vzťahu (dohoda, nepravidelný príjem
alebo pracovný pomer s pravidelným príjmom).

Generovanie sa zastaví, ak dávka nemá žiadnu udalosť, ak zamestnanec nemá
platné rodné číslo, ak chýba dátum, ktorý udalosť vyžaduje, ak má prihláška
stav účasti *Neoverené* či žiadny doklad, ak zmena nič neoznamuje, alebo ak
je pole OOP vyplnené tam, kde ho tlačivo neprijíma (mimo dohody, dôvod
dovolenky pri DoBPŠ alebo pred vzorom 2027).

## Obmedzenia {#limitations}

- **Prihláška, odhláška a jediný druh zmeny:** OOP z dohody. Inú zmenu,
  prerušenie a zrušenie prihlásenia treba podať cez portál.
- **Polia OOP vychádzajú zo schémy a zo zákona, nie zo zverejneného návodu
  na vyplnenie.** V čase písania (november 2026) Sociálna poisťovňa zverejnila
  schému RLZEC 2027 a popis zmien, ale nie pokyny k dvom novým poliam.
  Kontroly portálu môžu vyžadovať kombináciu, ktorú modul nevytvára; prvé
  podanie porovnajte s formulárom na portáli.
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
- Zmena stavu účasti po prihlásení je *zmena*, ktorú modul nevytvára.
- Dodávajú sa vzory RLZEC 2026 a 2027. Overenie voči schéme kontroluje tvar
  súboru, nie údaje.
