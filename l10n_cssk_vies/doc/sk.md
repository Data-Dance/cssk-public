---
title: CZ/SK VIES — priame overenie a doklad o overení
summary: Overuje IČ DPH z iných členských štátov priamo v systéme VIES Európskej komisie, bez Odoo IAP, a každé overenie aj s číslom overenia uchová ako doklad.
verified: 19.0.2.1.0
---

## Na čo slúži {#purpose}

Dodanie tovaru do iného členského štátu je oslobodené od dane len vtedy, ak
je nadobúdateľ identifikovaný pre daň v inom členskom štáte a toto IČ DPH
vám oznámil. Overenie čísla v systéme **VIES** (systém výmeny informácií o
DPH Európskej komisie) je spôsob, ako to preukázať.

Odoo overuje IČ DPH cez vlastnú službu IAP a uchováva len príznak áno/nie.
Tento modul:

- volá službu VIES Európskej komisie **priamo**, bez účtu Odoo a kreditov IAP;
- robí **kvalifikované** overenie — s vašou spoločnosťou ako žiadateľom —, na
  ktoré VIES vráti **číslo overenia**, identifikátor konkrétneho overenia;
- uchováva **každé overenie** — dátum, výsledok, číslo overenia, názov a
  adresu podľa VIES, kto overoval a za ktorú spoločnosť — ako needitovateľný
  záznam na kontakte;
- kontakty denne overuje znova.

## Právny rámec {#legal}

Podmienky oslobodenia, pre ktoré IČ DPH odberateľa rozhoduje:

- **Slovensko** — [§ 43 ods. 1 zákona o DPH](law:sk/2004/222#paragraf-43.odsek-1):
  dodanie je oslobodené, ak je nadobúdateľom zdaniteľná osoba (alebo
  právnická osoba, ktorá nie je zdaniteľnou osobou) identifikovaná pre daň v
  inom členskom štáte **a toto identifikačné číslo pre daň oznámila
  dodávateľovi**.
- **Česko** — [§ 64 odst. 1 zákona o DPH](law:cz/2004/235): dodanie osobe
  registrovanej k dani v inom členskom štáte je oslobodené, ak táto osoba
  **oznámila platiteľovi svoje DIČ**, tovar sa odošle do iného členského štátu
  a platiteľ dodanie uvedie v súhrnnom hlásení.

Žiadny z týchto zákonov nepredpisuje VIES ani číslo overenia ako formu
dôkazu; je to doklad, ktorý si správca dane zvyčajne vyžiada, keď sa neskôr
ukáže, že číslo odberateľa bolo neplatné.

## Nastavenie {#setup}

1. Vaša spoločnosť musí mať vyplnené vlastné **IČ DPH**. Číslo overenia vydá
   VIES len pri kvalifikovanom overení, ktoré IČ DPH žiadateľa potrebuje.
2. *Účtovníctvo → Konfigurácia → Nastavenia*, blok **Dane**, nastavenie
   **Overiť číslo DPH**: zaškrtnite **Použiť priame EU VIES (bez IAP)**.
   Nastavuje sa pre každú spoločnosť zvlášť.

So zaškrtnutou voľbou ide vlastné overenie Odoo (spúšťa sa pri zadaní IČ DPH,
ak je zapnuté *Overiť číslo DPH*) namiesto IAP priamo na Európsku komisiu a
pre spoločnosť beží denné obnovovanie. Tlačidlo **Overiť teraz** opísané nižšie
funguje bez ohľadu na voľbu.

## Overenie kontaktu {#usage}

Na formulári kontaktu je pod IČ DPH riadok **VIES**:

- **Overiť teraz** — kontakt uloží a jeho IČ DPH hneď overí vo VIES za
  spoločnosť, v ktorej práve pracujete. Výsledok oznámi notifikácia: *Platné
  vo VIES* s číslom overenia, *Neplatné vo VIES* alebo *VIES neodpovedal*.
- zelená fajka alebo červený krížik — aktuálny výsledok; kliknutím otvoríte
  záložku **VIES**. Pomlčka znamená, že spoločnosť kontakt ešte neoverila.

Záložka **VIES** (zobrazí sa, keď má kontakt IČ DPH):

| Skupina | Polia |
|---|---|
| Overenie | *Overené vo VIES dňa*, *Číslo overenia VIES*, *Dátum požiadavky VIES* (dátum, ktorý overeniu pridelí VIES), *Posledná chyba VIES* (len po overení, na ktoré VIES neodpovedal) |
| Ako je zapísané vo VIES | *Názov zapísaný vo VIES*, *Adresa zapísaná vo VIES*, *Zhoda názvu vo VIES* (či sa názov vo VIES zhoduje s názvom kontaktu) |

Tieto polia ukazujú posledné zodpovedané overenie **aktuálnej spoločnosti**.
Pod nimi je úplný zoznam overení všetkých spoločností, ku ktorým máte prístup,
s dátumom, výsledkom, číslom overenia a používateľom. Neplatné odpovede sú
červené, chyby sivé.

Záznamy nemôže nikto upravovať. Mazať ich môžu len administrátori.

## Denné obnovovanie {#refresh}

Naplánovaná akcia **VIES: obnoviť priame overenia (CZ/SK)** beží raz denne. Za
každú spoločnosť so zapnutým priamym VIES overí kontakty najvyššej úrovne,
ktorých IČ DPH začína predponou iného členského štátu EÚ než štátu
spoločnosti (vrátane `EL` pre Grécko a `XI` pre Severné Írsko), ktoré sú
spoločné alebo patria tejto spoločnosti a ktoré táto spoločnosť neoverila za
posledných 7 dní
— najviac 200 za spoločnosť a beh, s krátkou pauzou medzi požiadavkami, lebo
VIES obmedzuje počet požiadaviek. Každý výsledok sa zaznamená a aktualizuje
výsledok VIES na kontakte.

## Keď VIES neodpovie {#faults}

VIES často odpovie, že národný systém je nedostupný alebo preťažený. Taká
odpoveď (`MS_UNAVAILABLE`, `MS_MAX_CONCURRENT_REQ`,
`GLOBAL_MAX_CONCURRENT_REQ`, `SERVICE_UNAVAILABLE`, `TIMEOUT`, `BUSY`) alebo
žiadna odpoveď sa zaznamená ako **No answer** (bez odpovede). Číslo nikdy
neoznačí za neplatné a nikdy nenahradí posledný skutočný doklad; denné
obnovovanie to skúsi znova po 7 dňoch. Každá iná záporná odpoveď sa považuje
za neplatnosť.

## Obmedzenia {#limitations}

- **Neuložený kontakt sa overí, ale nezaznamená.** Automatické overenie, ktoré
  Odoo spustí pri zadaní IČ DPH, sa zaznamená aj s číslom overenia ako každé
  iné — no pri novom kontakte ho nie je ku komu priradiť, kým sa neuloží. Ak
  doklad potrebujete hneď, po uložení stlačte *Overiť teraz*.
- **Bez vlastného IČ DPH nie je číslo overenia.** Ak spoločnosť nemá
  vyplnené IČ DPH, VIES odpovie platné / neplatné, ale číslo overenia nevráti.
- **Denné obnovovanie sa neobmedzuje na odberateľov.** Každá spoločnosť so
  zapnutým priamym overením overuje všetky spoločné aj vlastné kontakty
  najvyššej úrovne so zahraničným IČ DPH z EÚ, či s nimi obchoduje alebo nie.
  Tuzemské IČ DPH a kontakty iných spoločností vynecháva.
- **Výsledok je spoločný, doklad nie.** Fajka alebo krížik je jedna hodnota
  na kontakt podľa toho, ktorá spoločnosť overovala naposledy; číslo overenia
  a údaje z registra sú za každú spoločnosť zvlášť.
- Overenie dokazuje, čo VIES v tej chvíli odpovedal. Ostatné podmienky
  oslobodenia (preprava, súhrnný výkaz) nepokrýva.
