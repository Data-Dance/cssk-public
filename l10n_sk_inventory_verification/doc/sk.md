---
title: SK Inventarizácia — inventúrny súpis a inventarizačný zápis
summary: Inventarizácia podľa zákona o účtovníctve ako záznamy v Odoo — tri dni inventúry, inventúrne súpisy s množstvom a cenou a inventarizačný zápis s porovnaním so stavom v účtovníctve.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Pred zostavením účtovnej závierky musí účtovná jednotka overiť, či stav
majetku, záväzkov a rozdielu majetku a záväzkov v účtovníctve zodpovedá
skutočnosti — vykonať **inventarizáciu**. Jej výsledkom sú **inventúrne
súpisy** (zistený skutočný stav) a **inventarizačný zápis** (porovnanie so
stavom v účtovníctve).

Modul tieto záznamy vedie v Odoo: jeden doklad inventarizácie, pod ním
ľubovoľný počet inventúrnych súpisov a na samotnej inventarizácii údaje
inventarizačného zápisu. Pri dokladovej inventúre účtu načíta účtovný stav z
hlavnej knihy. Oba záznamy sa tlačia do PDF.

Inventarizáciu eviduje a preukazuje, inventarizačné rozdiely však
**nezaúčtuje**: manká, prebytky, opravné položky a podobne vyplývajú zo zápisu
a zaúčtuje ich účtovník.

## Právny rámec {#legal}

Odkazy sú na [zákon o účtovníctve](law:sk/2002/431).

- **Kedy.** Podľa [§ 29 ods. 2](law:sk/2002/431#paragraf-29.odsek-2) sa
  inventarizácia vykonáva ku dňu, ku ktorému sa zostavuje riadna alebo
  mimoriadna účtovná závierka. Pri hmotnom majetku okrem zásob a peňažných
  prostriedkov v hotovosti možno podľa
  [§ 29 ods. 3](law:sk/2002/431#paragraf-29.odsek-3) zvoliť inú lehotu,
  najviac štyri roky; hotovosť sa inventarizuje vždy ku dňu závierky.
- **Ako.** Podľa [§ 30 ods. 1](law:sk/2002/431#paragraf-30.odsek-1) sa
  skutočný stav majetku hmotnej a nehmotnej povahy zisťuje **fyzickou
  inventúrou**; pri záväzkoch, rozdiele majetku a záväzkov a pri majetku, pri
  ktorom fyzickú inventúru vykonať nemožno, **dokladovou inventúrou**; ak je to
  možné, kombináciou oboch.
- **Inventúrny súpis** musí obsahovať údaje podľa
  [§ 30 ods. 2](law:sk/2002/431#paragraf-30.odsek-2), okrem iného *deň
  začatia inventúry, deň, ku ktorému bola inventúra vykonaná, a deň skončenia
  inventúry* (písm. b), stav majetku *s uvedením jednotiek množstva a ceny*
  (písm. c), miesto uloženia majetku (písm. d), meno, priezvisko a podpisový
  záznam hmotne zodpovednej osoby (písm. e), meno, priezvisko a podpisový
  záznam osôb zodpovedných za zistenie skutočného stavu (písm. i) a poznámky
  (písm. j).
- **Inventarizačný zápis** musí podľa
  [§ 30 ods. 3](law:sk/2002/431#paragraf-30.odsek-3) obsahovať obchodné meno
  a sídlo, výsledky porovnania skutočného stavu s účtovným stavom, výsledky
  posúdenia reálnosti ocenenia podľa [§ 26](law:sk/2002/431#paragraf-26) a 27
  a meno, priezvisko a podpisový záznam osôb zodpovedných za vykonanie
  inventarizácie.
- **Fyzická inventúra mimo dňa závierky.** Podľa
  [§ 30 ods. 4](law:sk/2002/431#paragraf-30.odsek-4) ju pri hmotnom majetku
  možno vykonať v posledných troch mesiacoch účtovného obdobia alebo v prvom
  mesiaci nasledujúceho, pri zásobách kedykoľvek v priebehu obdobia; stav ku
  dňu závierky sa potom preukáže úpravou o prírastky a úbytky.
- **Rozdiely.** Inventarizačný rozdiel je manko (pri peniazoch a ceninách
  schodok) alebo prebytok
  ([§ 30 ods. 5](law:sk/2002/431#paragraf-30.odsek-5)) a zaúčtuje sa do
  obdobia, za ktoré sa stav overuje
  ([§ 30 ods. 7](law:sk/2002/431#paragraf-30.odsek-7)).

## Nastavenie {#setup}

Nič sa nenastavuje. Doklady sa číslujú `INV/<rok>/001`, `INV/<rok>/002`, … z
jedného číselného radu spoločného pre všetky spoločnosti; rok je rokom
vytvorenia dokladu, nie overovaného obdobia.

Ponuka je *Účtovníctvo → Účtovníctvo → Inventarizácia*. Na Community sa
aplikácia volá *Fakturácia* a podponuka *Účtovníctvo* sa zobrazí len
používateľom s prístupom k úplným účtovným funkciám. Používatelia fakturácie
môžu inventarizácie vytvárať a upravovať, mazať ich môže len správca
účtovníctva.

## Postup inventarizácie {#usage}

1. **Založte inventarizáciu.** *Inventarizácia → Nové* a v bloku **Termíny
   (§ 30 ods. 2)** vyplňte *Deň začatia inventúry*, *Deň, ku ktorému bola
   inventúra vykonaná* (spravidla deň závierky) a *Deň skončenia inventúry*.
   Deň skončenia nesmie predchádzať dňu začatia. Tlačidlom **Začať** prejde
   doklad zo stavu *Návrh* do stavu *Prebieha*.
2. **Pridajte inventúrne súpisy** na karte **Inventúrne súpisy**, jeden
   súpis za sklad, pokladnicu, skupinu majetku či účet. *Pridať riadok*
   otvorí súpis vo vlastnom okne; pri každom:
   - *Názov* a *Druh inventarizácie*: **Fyzická inventúra** alebo
     **Dokladová inventúra**;
   - *Účet* — pri dokladovej inventúre účet, ktorého zostatok sa overuje;
   - *Miesto uloženia majetku*, *Hmotne zodpovedná osoba* (kontakt) a
     *Skutočný stav zistil* (používateľ).
3. **Zadajte položky** v tom istom okne: *Popis*, prípadne *Produkt*,
   *Množstvo*, *Jednotka* (voľný text) a *Cena za jednotku*. *Hodnota* je
   množstvo × cena a *Skutočný stav* súpisu je súčtom položiek. Výber produktu
   nič nepredvyplní, cenu zadajte sami. Kliknutím na súpis v zozname ho
   znova otvoríte.
4. **Účtovný stav.**
   - *Dokladová inventúra* s účtom: *Účtovný stav* je zostatok účtu zo
     **zaúčtovaných** dokladov s dátumom do dňa, ku ktorému bola inventúra
     vykonaná, vrátane. Prepočíta sa pri zmene účtu, tohto dňa alebo položiek.
     Neskôr zaúčtované doklady načíta tlačidlo **Načítať zostatok účtu** v
     súpise, alebo **Načítať účtovné stavy** v hlavičke inventarizácie pre
     všetky dokladové inventúry naraz.
   - *Fyzická inventúra*: *Účtovný stav* zadajte podľa skladovej či
     majetkovej evidencie.

   *Rozdiel* je *Skutočný stav* − *Účtovný stav*, za každý súpis aj spolu.
5. **Vyplňte zápis** na karte **Inventarizačný zápis (§ 30 ods. 3)**:
   *Výsledky porovnania skutočného a účtovného stavu*, *Posúdenie reálnosti
   ocenenia* a *Zodpovedný za vykonanie inventarizácie* (§ 30 ods. 3
   písm. d)).
6. Kliknite na **Ukončiť**. Odmietne sa, ak inventarizácia nemá žiadny súpis
   alebo ak na niektorom súpise chýba *Skutočný stav zistil* (§ 30 ods. 2
   písm. i). **Späť na návrh** ju kedykoľvek znova otvorí.

### Znamienka pri dokladovej inventúre {#signs}

Účtovný stav je zostatok má dať mínus dal, takže účty záväzkov a vlastného
imania vychádzajú **záporne**: záväzok voči dodávateľovi 500 na účte 321 sa
zobrazí ako −500. Potvrdené sumy takého účtu zadávajte so zápornou cenou
(napríklad množstvo 1, cena −500), aby *Rozdiel* porovnával porovnateľné.

## Tlačové výstupy {#reports}

Na inventarizácii *Tlač → Inventarizačný zápis* vytlačí zápis: názov a sídlo
účtovnej jednotky, deň, ku ktorému sa inventarizuje, tabuľku všetkých súpisov s
účtovným stavom, skutočným stavom, rozdielom a súčtami, text porovnania,
posúdenie reálnosti ocenenia (alebo *Neuvedené*) a riadky na podpis osoby
zodpovednej za vykonanie inventarizácie a za účtovnú jednotku.

Tlačidlo **Tlačiť inventúrne súpisy** v hlavičke inventarizácie vytlačí jej
súpisy, každý na samostatnú stranu: názov a sídlo účtovnej jednotky, tri dni
inventúry, druh, miesto uloženia a účet, položky s množstvom, jednotkou, cenou za
jednotku a hodnotou, súčty, poznámky a riadky na podpis hmotne zodpovednej
osoby a osoby, ktorá zistila skutočný stav.

Sídlom je adresa spoločnosti; fyzická osoba tam má mať bydlisko, a ak sa
líši, aj miesto podnikania.

Podpisové záznamy sú prázdne riadky na podpis na papieri; nič sa nepodpisuje
elektronicky.

## Obmedzenia {#limitations}

- Súpis nemá samostatné polia pre zoznam záväzkov, zoznam skutočného stavu
  rozdielu majetku a záväzkov ani odporúčania na posúdenie reálnosti ocenenia
  (§ 30 ods. 2 písm. f – h). Použite položky a *Poznámky*.
- *Zodpovedný za vykonanie inventarizácie* je jeden používateľ; § 30 ods. 3
  písm. d) hovorí o osobe alebo osobách zodpovedných za vykonanie
  inventarizácie a na ukončenie sa pole nevyžaduje.
- Pri dokladovej inventúre ručne prepísaný účtovný stav nevydrží —
  nasledujúci prepočet alebo načítanie ho nahradí.
- Pri fyzickej inventúre sa nič nenačítava zo skladu ani z evidencie majetku;
  účtovný stav sa zadáva ručne.
- Lehoty podľa § 29 ods. 3 a § 30 ods. 4 sa nekontrolujú a ukončená
  inventarizácia zostáva upraviteľná — stav *Ukončená* nič nezamyká.
- Rozdiely sa nezaúčtujú; manká, prebytky a úpravy ocenenia zaúčtuje
  účtovník podľa zápisu.
