---
title: SK Inventarizácia — inventúrny súpis a inventarizačný zápis
summary: Inventarizácia podľa zákona o účtovníctve ako záznamy v Odoo — tri dni inventúry, inventúrne súpisy s množstvom a cenou a inventarizačný zápis s porovnaním so stavom v účtovníctve.
verified: 19.0.1.2.0
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

Zaúčtuje aj inventarizačné rozdiely — manká, schodky a prebytky — ako účtovný
zápis v návrhu s dátumom v overovanom období, prepojený s inventarizáciou.
Opravné položky a iné úpravy ocenenia nie sú inventarizačnými rozdielmi
([§ 30 ods. 6](law:sk/2002/431#paragraf-30.odsek-6)) a zostávajú na
účtovníkovi.

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
     pri fyzickej inventúre účet, na ktorom sa majetok vedie (použije sa pri
     zaúčtovaní rozdielu);
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

## Zaúčtovanie inventarizačných rozdielov {#differences}

Záložka **Inventarizačné rozdiely (§ 30 ods. 5 až 7)** premení rozdiely súpisov na účtovný zápis.

1. **Každému súpisu dajte účet.** *Účet* na súpise je účet, na ktorom sa inventarizovaný majetok vedie (211 pri pokladnici, 132 pri tovare). Pri dokladovej inventúre tam už je; pri fyzickej inventúre ho doplňte, lebo návrh z neho vychádza.
2. Kliknite na **Navrhnúť vyúčtovanie rozdielov**. Za každý súpis, ktorého rozdiel ešte nie je vysvetlený, pribudne jeden riadok: *Manko / schodok*, ak je skutočný stav nižší ako účtovný, *Prebytok*, ak je vyšší — na celú sumu a s navrhnutými účtami (pozri tabuľku nižšie).
3. **Upravte riadky.** Manko rozdeľte na časť do vašej normy prirodzených úbytkov (*Úbytok do normy*) a časť nad ňu. Pridajte riadok *Náhrada od zodpovednej osoby* na sumu, ktorú od nej požadujete, a vyplňte *Partner*. Ktorýkoľvek účet zmeňte, ak sa vaša osnova alebo váš prípad líši. Sumy sú vždy kladné: smer určuje druh. *Zostáva vyúčtovať* na súpise ukazuje, čo riadky ešte nevysvetľujú.
4. **Rozdiel, ktorý sa odtiaľto neúčtuje** (majetok vyradený v evidencii majetku, zásoby upravené v module Sklad, rozdiel doložený vlastným dokladom): na súpise zaškrtnite *Rozdiel sa tu neúčtuje* a uveďte dôvod. Dôvod sa vytlačí v zápise.
5. Kliknite na **Zaúčtovať rozdiely**. Tlačidlo sa ponúkne, keď je každý rozdiel buď celý vysvetlený, alebo označený ako neúčtovaný. Vznikne jeden účtovný zápis **v návrhu**, v *Denníku pre rozdiely* (prvý interný denník, ak nezvolíte iný), s dátumom *dňa, ku ktorému bola inventúra vykonaná*, a s číslom inventarizácie ako referenciou. Účtovník ho skontroluje a zaúčtuje v Účtovníctve; otvorí ho tlačidlo *Účtovné zápisy* hore.

Stav *Rozdiely* v súhrne má hodnoty *Na vyúčtovanie*, *Pripravené na zaúčtovanie*, *Zápis v návrhu* alebo *Zaúčtované*.

### Navrhované účty {#difference-accounts}

Návrhy vychádzajú z postupov účtovania v podvojnom účtovníctve ([opatrenie MF SR č. 23054/2002-92](law:sk/2002/740)). Sú to návrhy: oba účty zostávajú upraviteľné.

| Súpis vedený na účte | Manko / schodok | Úbytok do normy | Prebytok |
|---|---|---|---|
| 211, 213 (peniaze, ceniny) | 335 / 21x — § 11 ods. 1 písm. b): schodok sa účtuje ako pohľadávka voči hmotne zodpovednej osobe, nie do nákladov | — | 21x / 668 |
| 112, 132 a ostatné účty skupín 11 a 13 | 549 / 1xx (§ 43 ods. 2 písm. d), § 68 ods. 8) | 501 / 11x, 504 / 13x | 1xx / 648 |
| 121 až 124 (zásoby vlastnej výroby) | 549 / 12x (§ 43 ods. 3 písm. b)) | 61x / 12x | 12x / 61x |
| 01x, 02x (odpisovaný dlhodobý majetok) | bez návrhu | — | 0xx / 384 (§ 21 ods. 2) |
| 03x (neodpisovaný dlhodobý majetok) | 549 / 03x | — | 03x / 648 (§ 11 ods. 4) |
| ostatné (pohľadávky, záväzky, vlastné imanie) | bez návrhu | — | bez návrhu |

*Náhrada od zodpovednej osoby* navrhuje 378 / 648 (§ 55 ods. 9 písm. a)).

Kde sa nič nenavrhne, zápis sa nevytvorí, kým súvzťažný účet nezvolíte sami. Tri prípady potrebujú viac než tento zápis:

- **Dlhodobý majetok.** Pri manku odpisovaného majetku sa zostatková cena účtuje cez oprávky (§ 36 ods. 4 písm. e)) a novo zistený majetok treba zaradiť v reálnej hodnote. Oboje urobte v evidencii majetku a súpis označte ako neúčtovaný; riadok na účte triedy 0 má upozornenie.
- **Zásoby oceňované modulom Sklad.** Ak účet zásob vedie Odoo samo, opravte množstvo v Sklade, ktorý rozdiel zaúčtuje. Riadok na takom účte má upozornenie, lebo rozdiel by sa inak zaúčtoval dvakrát.
- **Spôsob B účtovania zásob.** Stav zásob sa ku koncu roka účtuje podľa inventarizácie (112 / 501, 132 / 504), takže manko je preúčtovanie: ako *Účet* dajte 501 alebo 504 a ako súvzťažný účet 549.

Prebytok nakupovaných zásob spôsobený preukázateľne chybným účtovaním výdaja sa účtuje v prospech skupiny 50 namiesto 648 (§ 11 ods. 2); zmeňte súvzťažný účet.

Zápis neobsahuje DPH ani úpravu základu dane z príjmov. Manko presahujúce prijaté náhrady nie je daňovým výdavkom ([§ 21 ods. 2 písm. e)](law:sk/2003/595#paragraf-21.odsek-2.pismeno-e) zákona o dani z príjmov) a DPH odpočítaná z odcudzeného tovaru sa odvádza podľa [§ 53 ods. 5](law:sk/2004/222#paragraf-53.odsek-5) zákona o DPH (549 / 343); oboje zostáva na účtovníkovi.

### Zrušenie zaúčtovania {#difference-reversal}

**Zrušiť zaúčtovanie rozdielov** zápis v návrhu vymaže a zaúčtovaný zápis stornuje. Storno má rovnaký dátum ako zápis, takže zostáva v overovanom období. **Späť na návrh** na inventarizácii urobí to isté skôr, než doklad znova otvorí, lebo súpisy sa budú meniť. Riadky vyúčtovania zostávajú a možno ich zaúčtovať znova.

Riadky, z ktorých vznikol zápis, nemožno meniť ani mazať, kým sa zaúčtovanie nezruší; rovnako ich súpis ani inventarizáciu. Ak sa súpis po zaúčtovaní zmení, upozornenie hore oznámi, že zaúčtované sumy už nesedia.

**Uzamknuté obdobia.** Rozdiely patria do obdobia, za ktoré sa stav overuje ([§ 30 ods. 7](law:sk/2002/431#paragraf-30.odsek-7)). Odoo samo pri zaúčtovaní posunie zápis s dátumom v uzamknutom období na prvý otvorený deň. Pri týchto zápisoch to modul namiesto toho odmietne: vytvorenie, zaúčtovanie aj storno sa zastavia s hlásením, kým obdobie neodomknete.

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
- Úpravy ocenenia (opravné položky, § 26 a 27) sa neúčtujú; zaúčtuje ich
  účtovník podľa zápisu.
- Zaúčtovanie rozdielov nevyraďuje ani nezaraďuje dlhodobý majetok, neupravuje
  množstvá v module Sklad a neúčtuje DPH; pozri
  [Zaúčtovanie inventarizačných rozdielov](#differences).
- Zápis rozdielov je len v mene spoločnosti a ukončenie inventarizácie
  zaúčtovanie rozdielov nevyžaduje.
- Protokoly o zaradení a vyradení majetku nie sú súčasťou tohto modulu: sú v module [module:l10n_sk_asset_protocol_base](module:l10n_sk_asset_protocol_base), ktorý potrebuje register majetku.
