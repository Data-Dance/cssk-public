---
title: SK účtovná závierka (Úč POD)
summary: Účtovná závierka podnikateľa v podvojnom účtovníctve — súvaha a výkaz ziskov a strát zostavené z účtovníctva a exportované ako oficiálny súbor UZPODv14, k tomu prehľad peňažných tokov, prehľad zmien vlastného imania a poznámky.
verified: 19.0.1.7.4
---

## Na čo slúži {#purpose}

Slovenská spoločnosť, ktorá vedie podvojné účtovníctvo, uzatvára každý rok
**účtovnou závierkou**. Malé a veľké účtovné jednotky podávajú jej výkazy ako
jeden elektronický dokument **Účtovná závierka Úč POD** (XML vzor
*UZPODv14*), ktorý obsahuje:

- **súvahu** (*Úč POD 1-01*, riadky 001 – 145, aktíva v stĺpcoch brutto /
  korekcia / netto) a
- **výkaz ziskov a strát** v druhovom členení (*Úč POD 2-01*, riadky 01 – 61).

Modul tento dokument poskytuje na spoločnom mechanizme opísanom v
[module:l10n_cssk_fs_base](module:l10n_cssk_fs_base) — zostavený z účtovných
zápisov, skontrolovaný, exportovaný a overený voči oficiálnej schéme
finančnej správy. Navyše pridáva:

- **prehľad peňažných tokov** (nepriama metóda) a **prehľad zmien vlastného
  imania** ako pracovné výkazy;
- **poznámky** ako formulár so štandardnými textami, z ktorého vznikne PDF;
- **záznam podania** Úč POD s opravnými závierkami.

## Právny rámec {#legal}

Ak nie je uvedené inak, odkazy sú na [zákon o účtovníctve](law:sk/2002/431).

- **Súčasti.** Účtovná závierka v sústave podvojného účtovníctva obsahuje
  súvahu, výkaz ziskov a strát a poznámky —
  [§ 17 ods. 3](law:sk/2002/431#paragraf-17.odsek-3). Oba výkazy uvádzajú
  bežné a bezprostredne predchádzajúce účtovné obdobie —
  [§ 18 ods. 3 a 4](law:sk/2002/431#paragraf-18.odsek-3).
- **Veľkostné skupiny.** Spoločnosti sa triedia na mikro, malú a veľkú
  účtovnú jednotku podľa celkovej sumy majetku, čistého obratu a priemerného
  prepočítaného počtu zamestnancov —
  [§ 2 ods. 5 až 8](law:sk/2002/431#paragraf-2.odsek-5). Hlavička Úč POD
  uvádza malú alebo veľkú účtovnú jednotku; mikro účtovná jednotka podáva iné
  tlačivo (*Úč MÚJ*), ktoré tento modul nevytvára.
- **Usporiadanie.** Usporiadanie a obsahové vymedzenie položiek ustanovuje
  ministerstvo financií opatrením —
  [§ 4 ods. 2](law:sk/2002/431#paragraf-4.odsek-2): pre malé účtovné jednotky
  opatrenie č. MF/23378/2014-74, pre veľké účtovné jednotky a subjekty
  verejného záujmu opatrenie č. MF/23377/2014-74. Šablóna poznámok v tomto
  module vychádza z opatrenia pre malé účtovné jednotky.
- **Druh závierky.** Závierka zostavená pri uzavretí kníh k poslednému dňu
  účtovného obdobia je riadna, pri ostatných uzavretiach mimoriadna —
  [§ 17 ods. 6](law:sk/2002/431#paragraf-17.odsek-6); priebežnú závierku
  účtovná jednotka zostavuje v priebehu obdobia, ak to vyžaduje osobitný
  predpis — [§ 18 ods. 1](law:sk/2002/431#paragraf-18.odsek-1).
- **Uloženie.** Riadnu a mimoriadnu závierku účtovná jednotka ukladá v
  registri účtovných závierok najneskôr do šiestich mesiacov od dátumu, ku
  ktorému sa zostavuje, ak osobitný predpis neustanovuje inak —
  [§ 23a ods. 3](law:sk/2002/431#paragraf-23a.odsek-3) — a doručuje ju
  elektronicky cez portál finančného riaditeľstva —
  [§ 23b ods. 1](law:sk/2002/431#paragraf-23b.odsek-1).

## Nastavenie {#setup}

Hlavička Úč POD sa berie zo spoločnosti. Skontrolujte na spoločnosti a jej
kontakte:

| Údaj | Pole |
|---|---|
| DIČ | *DIČ* (ak je nainštalovaný slovenský základný modul), inak *Tax ID*; predpona `SK` sa odstráni |
| IČO | *IČO* |
| SK NACE | *NACE (main activity)* na kontakte spoločnosti |
| Obchodné meno, adresa, telefón, e-mail | kontakt spoločnosti; *číslo* domu je číslo na konci poľa *Ulica*, *Ulica 2* sa použije, len ak obsahuje iba číslo |
| Zápis v obchodnom registri | *Obchodný register* |

**Rozdelenie finančných výnosov a nákladov podľa prepojenia (voliteľné).**
Riadky IX, X, XI a N výkazu ziskov a strát oddeľujú sumy voči prepojeným
účtovným jednotkám a v rámci podielovej účasti od ostatných. Číslo účtu ich
nerozlíši, preto modul inštaluje šesť značiek účtov (*VZS IX.1 …*,
*VZS IX.2 …*, *VZS X.1 …*, *VZS X.2 …*, *VZS XI.1 …*, *VZS N.1 …*). Priraďte
značku účtom 665 / 666 / 662 / 562, na ktorých sa také sumy účtujú.
Spoločnosť, ktorá neoznačí nič, má všetko v riadkoch „ostatné“, čo je pri
samostatnej účtovnej jednotke správne.

Ostatné nastavenie — priradenie účtov, verzie — opisuje
[príručka mechanizmu](module:l10n_cssk_fs_base#setup).

## Príprava Úč POD {#usage}

*Účtovníctvo → Výkazy → Zákonné výkazy → Súvaha* (alebo *Výkaz ziskov a
strát* — je to ten istý dokument), *Nový*. Predvyplní sa verzia *Účtovná
závierka podnikateľov (UZPODv14)*; druh výkazu je *Účtovná závierka (súvaha +
výkaz ziskov a strát)*.

Vyplňte tri údaje hlavičky, ktoré sa pri tejto verzii zobrazia:

- **Veľkostná trieda** — *Malá* alebo *Veľká účtovná jednotka*;
- **Druh závierky** — *Riadna*, *Mimoriadna* alebo *Priebežná*;
- **Poznámky priložené** — zaškrtnite, ak sa s ňou podávajú poznámky.

Kliknite na **Vypočítať** a potom výkaz skontrolujte, rozpadnite na doklady a
opravte podľa [príručky mechanizmu](module:l10n_cssk_fs_base#review).
Ponuka Súvaha zobrazuje riadky súvahy, ponuka Výkaz ziskov a strát riadky
výkazu ziskov a strát.

**Ako sa počítajú niektoré riadky:**

- **A.VIII. Výsledok hospodárenia za účtovné obdobie** (r. 100) je pohyb
  tried 5 a 6 za obdobie, takže súvaha je vyrovnaná ešte pred uzavretím
  výsledku a rovná sa r. 61 výkazu ziskov a strát.
- **Účet 431** (výsledok hospodárenia v schvaľovaní) zámerne nie je v žiadnom
  riadku: v otvorenom účtovníctve stojí proti neuzavretému začiatočnému stavu
  tried 5 a 6. Zostatok, ktorý je skutočným výsledkom minulých rokov, nikdy
  neschváleným a nerozdeleným na 428 / 429, sa zobrazí v *Nepriradené účty*;
  kam patrí, rozhodne účtovník — modul ho nepreúčtuje.
- Účty, ktoré tlačivo uvádza na oboch stranách — 316, 336, 373, 398 a 481 —
  idú do riadku aktív alebo pasív podľa znamienka zostatku.
- Podsúvahové účty triedy 7 nepatria do žiadneho výkazu; ak majú zostatok,
  môžu sa zobraziť v *Nepriradené účty* a tam ich možno ignorovať.

## Export Úč POD {#export}

**Exportovať XML** na výkaze vytvorí dokument UZPODv14:

- sumy sú v **celých eurách**: riadky počítané z účtov sa zaokrúhlia a každý
  súčet sa prepočíta zo zaokrúhlených riadkov, takže súčty prejdú kontrolami
  portálu (obrazovka ponecháva centy);
- súbor sa overí voči oficiálnej schéme `uzpod-2014.xsd`;
- najprv sa spustia **kontrolné pravidlá** tlačiva: aktíva (r. 001) sa rovnajú
  pasívam (r. 079), na každom riadku aktív netto = brutto − korekcia a každý
  medzisúčet sa rovná súčtu svojich riadkov. Porušené pravidlo export zastaví
  a správa ho pomenuje. Odmietne sa aj výkaz, v ktorom sú aktíva aj pasíva
  nulové — to znamená, že sa do riadkov nedostal žiadny účet. Účty so
  zostatkom nad 100 €, ktoré sa nedostali do žiadneho riadku, sa ohlásia ako
  varovanie (*Účty nezachytené v žiadnom riadku výkazu*): export nezastavia,
  ale objavia sa na zázname ako žltý pruh navrchu formulára a v jeho
  chatteri, nielen v logu servera.
  Účet 431 sa tam objaví vždy, keď má zostatok.

Deň zostavenia v hlavičke je deň exportu. Podpisový záznam súčasťou súboru nie
je.

Súbor podajte na portáli finančnej správy a zaznamenajte cez **Označiť ako
podané** a **Podať** (pozri [príručku mechanizmu](module:l10n_cssk_fs_base#filing)).

## Záznam podania a opravná závierka {#filing-record}

*Účtovníctvo → Výkazy → Účtovná závierka UZPODv14 (SK)* obsahuje záznam
podania ku každej závierke s rovnakými údajmi hlavičky (*Druh závierky*,
*Veľkostná trieda*, *Poznámky priložené*). Sám nič nepočíta:

- **Vygenerovať XML (UZPODv14)** nájde výkaz Úč POD tej istej spoločnosti,
  obdobia a typu podania (ak neexistuje, vytvorí ho a vypočíta; ak je ešte v
  stave Návrh alebo Náhľad, prepočíta ho) a vytvorí z neho súbor s údajmi
  hlavičky zo záznamu. Podáva sa teda to, čo sa kontrolovalo, vrátane ručne
  zadaných súm. Platí rovnaká schéma aj kontrolné pravidlá; súbor sa priloží
  ako `UZPODv14-<dátum>.xml`.
- **Označiť ako podané** záznam uzamkne a uchová podanú kópiu; **Späť na
  návrh** ho znova otvorí.
- **Opravná závierka** (na podanom zázname) vytvorí opravné podanie
  prepojené s pôvodným. Ide o úplné nové zostavenie za obdobie, nie o rozdiely.
  Schéma UZPODv14 nemá označenie opravnej závierky, preto samotný súbor stále
  uvádza *riadna*; opravný charakter vyjadruje typ podania na portáli a názov
  súboru (`UZPODv14-opravna-<dátum>.xml`).

## Prehľad peňažných tokov a zmien vlastného imania {#prehlady}

V *Zákonné výkazy → Prehľad peňažných tokov* a *Prehľad zmien vlastného
imania*, verzie *Prehľad peňažných tokov 2025* a *Prehľad zmien vlastného
imania 2025*, platné od 1. 1. 2025:

- prehľad peňažných tokov rozdelí každý nepeňažný účet na prevádzkovú (A),
  investičnú (B) a finančnú (C) činnosť, takže A + B + C sa rovná zmene stavu
  peňažných prostriedkov; riadok *G. Kontrola* ukáže prípadný rozdiel;
- prehľad zmien vlastného imania číta začiatočný a konečný stav skupín
  41 – 43 a pohyby za rok; riadok *Kontrola* ukáže prípadný rozdiel.

Sú to pracovné výkazy pre poznámky. Ich XML export je vlastný štruktúrovaný
formát modulu — finančná správa pre ne samostatné tlačivo nezverejňuje — a nie
je určený na podanie.

## Poznámky {#poznamky}

*Účtovníctvo → Výkazy → Poznámky k závierke (SK)*. Záznam za obdobie s
článkami poznámok na kartách:

- **Čl. I — Všeobecné**: opis činnosti, dátum schválenia predchádzajúcej
  závierky, priemerný prepočítaný počet zamestnancov;
- **Čl. III — Zásady a odpisy**: nepretržité pokračovanie v činnosti, spôsob
  oceňovania, zmeny metód, prahy DDHM a DNM a odpisový plán;
- **Čl. II, IV–VII — Texty**: ostatné články.

Texty sú predvyplnené štandardným znením pre malú účtovnú jednotku bez náplne,
upravujete len výnimky. **Načítať odpisový plán z majetku** vyplní odpisový
plán z majetku spoločnosti (správa majetku v Enterprise), zoskupený podľa
doby odpisovania, a nahradí ním existujúce riadky. Bez správy majetku alebo
bez akéhokoľvek majetku to oznámi a plán nechá tak, ako je; vtedy ho zadajte
ručne. **Vygenerovať PDF** vytvorí poznámky ako PDF, uloží ich k
záznamu a stiahne.

## Obmedzenia {#limitations}

- **Mikro účtovné jednotky** (Úč MÚJ) nie sú podporované; vybrať možno len
  malú a veľkú.
- **Poznámky** sú PDF v štruktúre pre malé účtovné jednotky; XML export
  poznámok neexistuje a poznámky veľkej účtovnej jednotky pokryté nie sú.
  Zaškrtnutie *Poznámky priložené* je na vás.
- Prehľad peňažných tokov a prehľad zmien vlastného imania nemajú verziu pred
  rokom 2025 a nie sú usporiadané riadok po riadku ako oficiálna tabuľka.
- Z Odoo sa nič nepodáva; súbor sa vytvorí, overí a zaeviduje.
- Priradenie riadkov vychádza z oficiálneho tlačiva a štandardnej slovenskej
  účtovej osnovy; sledujte *Nepriradené účty* a pred prvým podaním dajte
  priradenie odsúhlasiť účtovníkovi.
