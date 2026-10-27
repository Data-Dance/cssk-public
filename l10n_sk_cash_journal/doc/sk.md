---
title: Slovensko — peňažný denník
summary: Slovenský peňažný denník — členenie podľa opatrenia MF/27076/2007-74, priradenie slovenskej účtovej osnovy, peňažný denník v zákonnom usporiadaní a údaje pre DPFO typ B.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

Slovenská časť skupiny modulov peňažného denníka. Základ — ako z úhrad vznikajú
riadky, generovanie, kontrola, tlač — opisuje
[návod k peňažnému denníku CZ/SK](module:l10n_cssk_cash_journal_base). Tento
modul pridáva to, čo je slovenské:

- **členenie** zákonného peňažného denníka ako katalóg kategórií;
- **priradenie slovenskej účtovej osnovy** k týmto kategóriám, takže prvý
  denník je použiteľný bez ručného priraďovania štyridsiatich účtov;
- **peňažný denník v PDF** v zákonnom usporiadaní stĺpcov a tú istú mriežku
  ako prvý hárok tabuľky XLSX;
- **údaje pre daňové priznanie** k dani z príjmov fyzickej osoby (*DPFO typ
  B*).

Slúži pre **jednoduché účtovníctvo** aj pre **daňovú evidenciu**.

## Právny rámec {#legal}

- **Stĺpce.** Pre jednoduché účtovníctvo vymenúva § 4 ods. 6
  [opatrenia MF/27076/2007-74](law:sk/2007/628) prehľady, ktoré peňažný denník
  obsahuje: peňažné prostriedky v hotovosti a na účtoch v bankách, každé v
  členení na príjmy a výdavky; priebežné položky; príjmy zahrnované do základu
  dane v členení *„najmä na“* predaj tovaru, predaj výrobkov a služieb a ostatné
  príjmy; výdavky v členení na zásoby, služby, mzdy, poistné a príspevky,
  tvorbu sociálneho fondu a ostatné výdavky; a príjmy a výdavky, ktoré
  neovplyvňujú základ dane. Podľa § 4 ods. 3 sú prevody medzi pokladnicou a
  bankou, medzi pokladnicami a medzi bankovými účtami priebežnými položkami,
  podľa § 4 ods. 9 patria odpisy do ostatných výdavkov a podľa § 4 ods. 10 musia
  zápisy nadväzovať na zostatky jednotlivých účtov v banke a jednotlivých
  pokladníc.
- **Daňová evidencia.** Forma je voľná, ale príjmy a daňové výdavky treba
  evidovať *„v časovom slede v členení potrebnom na zistenie základu dane“* —
  [§ 6 ods. 11 zákona o dani z príjmov](law:sk/2003/595#paragraf-6.odsek-11).
  Postačí ten istý katalóg.
- **Poistné podnikateľa je na Slovensku daňový výdavok.** Poistné a príspevky
  hradené daňovníkom s príjmami podľa § 6 ods. 1 a 2 sú daňovým výdavkom —
  [§ 19 ods. 3 písm. i)](law:sk/2003/595#paragraf-19.odsek-3.pismeno-i). To je
  najzreteľnejší rozdiel oproti českému katalógu, kde je ten istý účet
  nedaňový.
- **Paušálne výdavky.** Daňovník s paušálnymi výdavkami vedie len evidenciu
  príjmov a evidenciu zásob a pohľadávok —
  [§ 6 ods. 10](law:sk/2003/595#paragraf-6.odsek-10).

## Nastavenie {#setup}

Nainštalujte modul. Nainštaluje spoločný základ, načíta katalóg a priradí
účtovú osnovu každej spoločnosti so sídlom na Slovensku. Spoločnosť, ktorá
slovenskú osnovu načíta neskôr, sa priradí v tej chvíli. Potom pokračujte
nastaveniami opísanými v
[spoločnom návode](module:l10n_cssk_cash_journal_base#setup) — spôsob vedenia
účtovníctva, rozdelenie čiastočnej úhrady, začiatok denníka.

Predvolené priradenie podľa začiatku čísla účtu:

| Účty | Kategória |
|---|---|
| 601, 602, 606, 607 | P2 Príjmy z predaja výrobkov a služieb |
| 604 | P1 Príjmy z predaja tovaru |
| 641 – 648, 661, 663, 665 – 668 | P3 Ostatné príjmy zahŕňané do základu dane |
| 662 (úroky) | PN9 — zdanené zrážkou, mimo základu podľa § 6 |
| 501, 504, 507, 11x, 13x | V1 Zásoby |
| 502, 503, 511, 512, 518 | V2 Služby |
| 521 – 523 | V3 Mzdy |
| 524, 525 / 526 | V5 Poistné za zamestnancov / V4 Poistné podnikateľa |
| 527 | V6 Tvorba sociálneho fondu |
| 528, 531, 532, 538, 544, 548, 562, 563, 568, 569 | V9 Ostatné výdavky |
| 513, 543, 545, 549 | VN9 — reprezentácia, dary, pokuty, manká: nedaňové, kým neprenesiete, čo daňovým výdavkom je |
| 01x – 04x | VN2 Nákup dlhodobého majetku — výdavkom nie je kúpa, ale odpis |
| 551 | Z1 Odpisy (nepeňažné) |
| 591, 595 | VN4 Daň z príjmov |
| 343 | VN3 Odvod DPH pri výdaji, PN3 Nadmerný odpočet pri príjme |
| 231, 461, 479 | VN5 Splátka úveru pri výdaji, PN2 Prijatý úver pri príjme |
| 491 | VN1 Osobná spotreba pri výdaji, PN1 Vklad podnikateľa pri príjme |
| 261 | C1 Priebežné položky |

**Zámerne nepriradené:** 311 a 321 (modul cez ne dohľadá faktúru), 314 a 324
(preddavky — stĺpec závisí od toho, za čo sú, preto sa nespárovaný preddavok
označí na kontrolu) a vnútorné či oceňovacie účty, za ktorými nikdy nie je
úhrada. Kategória *Z2 Úprava základu dane* nie je priradená žiadnemu účtu;
priraďte ju účtu, na ktorý účtujete úpravy základu dane.

Pred prvou závierkou priradenie skontrolujte voči vlastnej osnove a s
účtovníkom; je to východisko.

## Kategórie {#categories}

| Kód | Kategória | Ovplyvňuje základ dane |
|---|---|---|
| P1, P2, P3 | Príjmy z predaja tovaru / výrobkov a služieb / ostatné | áno |
| PN1, PN2, PN3, PN9 | Vklad podnikateľa, prijatý úver, nadmerný odpočet DPH, ostatné | nie |
| V1 – V6, V9 | Zásoby, služby, mzdy, poistné podnikateľa, poistné zamestnávateľa, sociálny fond, ostatné | áno |
| VN1 – VN5, VN9 | Osobná spotreba, nákup dlhodobého majetku, odvod DPH, daň z príjmov, splátka úveru, ostatné | nie |
| C1 | Priebežné položky | — |
| Z1, Z2 | Odpisy, úprava základu dane (nepeňažné) | áno |

## Peňažný denník {#book}

*Účtovníctvo → Účtovníctvo → Peňažný denník → Tlač*, výstup **PDF**, vytlačí
pri slovenskej spoločnosti denník v zákonnom usporiadaní:

- **Pokladnica**, **Banka**, **Priebežné položky** a **DPH**, každé so stĺpcom
  *príjem* a *výdaj*, s hrubou sumou, ktorá sa pohla;
- stĺpce členenia — Predaj tovaru, Predaj výrobkov a služieb, Ostatné príjmy,
  Príjmy neovplyvňujúce ZD, Zásoby, Služby, Mzdy, Poistné a príspevky,
  Sociálny fond, Ostatné výdavky, Výdavky neovplyvňujúce ZD — so sumou bez DPH;
  storno je záporné vo vlastnom stĺpci;
- **Zostatok pokladnica** a **Zostatok banka** po každom riadku, od
  počiatočného stavu v hlavnej knihe k predchádzajúcemu dňu.

Vlastná kategória padne do *Ostatných príjmov* / *Ostatných výdavkov* alebo do
zodpovedajúceho stĺpca neovplyvňujúceho základ dane. Nepeňažné riadky (odpisy)
sa objavia len v *Ostatných výdavkoch*. Zostatok banky zahŕňa aj účty
neuhradených príjmov a platieb a dočasný bankový účet Odoo, takže sedí pred
importom výpisov aj po ňom.

Výstup **Tabuľka** obsahuje tú istú mriežku ako prvý hárok *Peňažný denník*,
za ním zoznam riadkov a súčty za kategórie.

## Údaje pre DPFO typ B {#dpfo}

*Účtovníctvo → Účtovníctvo → Peňažný denník → DPFO typ B — údaje z denníka*:
zvoľte obdobie (predvolene aktuálny rok) a kliknite na **Vypočítať**.

| Tabuľka | Čo zobrazí |
|---|---|
| Tabuľka 1 | r. 2 (a ďalšie riadky podľa § 6, ak kategória nesie ich kód), každý ako dva údaje: stĺpec 1 príjmy a stĺpec 2 výdavky; **r. 10** príjmy spolu a výdavky spolu — len riadky ovplyvňujúce základ dane, vrátane nepeňažných; *Základ dane* = rozdiel |
| Tabuľka 1a (daňová evidencia) / 1b (paušálne výdavky) | stavy na začiatku a na konci obdobia z hlavnej knihy: nehmotný majetok, hmotný majetok (zostatková cena), zásoby (trieda 1), pohľadávky (31x), záväzky (32x, kladne), finančný majetok (21x, 22x, 25x, 26x). Pri spôsobe vedenia *Paušálne výdavky* sa zobrazia len zásoby a pohľadávky ako tabuľka 1b. |
| Kontrola | DPH v prijatých a v uhradených platbách; priebežné položky príjem − výdaj, ktoré by mali byť ku koncu roka blízko nuly |

Ak obdobie obsahuje riadky na kontrolu, upozornenie oznámi, že údaje nie sú
úplné. Údaje slúžia na kontrolu a prepísanie do priznania; XML sa tu
nevytvára.

## Obmedzenia {#limitations}

- Všetky kategórie príjmov a výdavkov sú označené ako r. 2 (živnosť).
  Podnikateľ s príjmami z iného zdroja podľa § 6 ich na obrazovke prečíslovať
  nemôže — kód v daňovom priznaní sa vo formulári kategórie nezobrazuje.
- Súčet pod stĺpcom *Hodnota* sčíta nesúvisiace riadky; nevšímajte si ho.
- Položka menu je viditeľná v každej spoločnosti vrátane českých.
- Čísla a znenie riadkov DPFO zodpovedajú tlačivu, ako ho modul pozná;
  overte ich voči tlačivu na príslušný rok.
- Knihu pohľadávok a knihu záväzkov, ktoré jednoduché účtovníctvo vyžaduje
  ([§ 15 ods. 1 zákona o účtovníctve](law:sk/2002/431#paragraf-15.odsek-1)),
  modul nevytvára.
