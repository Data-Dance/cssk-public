---
title: Kontrolný výkaz DPH (KV DPH)
summary: Slovenský kontrolný výkaz DPH — oddiely A.1 až D.2 vypočítané z účtovníctva, skontrolované podľa požiadaviek tlačiva a exportované ako XML Finančnej správy vo vzore platnom pre dané obdobie.
verified: 19.0.2.4.0
---

## Na čo slúži {#purpose}

Platiteľ DPH podáva **kontrolný výkaz DPH** za každé zdaňovacie obdobie, za
ktoré podáva daňové priznanie. Uvádza v ňom jednotlivo vyhotovené aj prijaté
faktúry, aby mohla finančná správa spárovať daň dodávateľa s odpočtom
odberateľa.

Tento modul je slovenská časť spoločného kontrolného výkazu. Pridáva
slovenské oddiely, pravidlá zaradenia dokladov do oddielov, kontroly, ktoré
vyžaduje úradné tlačivo, a XML šablóny pre všetky vzory od roku 2014. Postup
práce — založenie výkazu, výpočet, export, označenie ako podaného, opravy —
opisuje [spoločná príručka](module:l10n_cssk_kv_kh_base#usage).

Vyžaduje slovenskú účtovú osnovu Odoo (`l10n_sk`) a funguje v edícii
Community aj Enterprise.

## Právny rámec {#legal}

Ak nie je uvedené inak, odkazy sú na [zákon o DPH](law:sk/2004/222).

- **Kto a kedy.** Platiteľ je povinný podať kontrolný výkaz elektronickými
  prostriedkami za každé zdaňovacie obdobie, za ktoré je povinný podať
  daňové priznanie, do 25 dní po skončení zdaňovacieho obdobia —
  [§ 78a ods. 1](law:sk/2004/222#paragraf-78a.odsek-1). Nepodáva ho za
  obdobie, v ktorom v priznaní neuvádza žiadne údaje o plneniach, alebo len
  dodania oslobodené podľa § 43 alebo § 47 bez odpočtu, prípadne len s
  odpočtom dane pri dovoze.
- **Obsah.** [§ 78a ods. 2](law:sk/2004/222#paragraf-78a.odsek-2) určuje
  členenie: údaje z každej faktúry, ktorú bol platiteľ povinný vyhotoviť o
  zdaniteľnom plnení, vrátane prenosu daňovej povinnosti podľa § 69 ods. 12
  písm. f) až j) (oddiely A.1, A.2); údaje z prijatých faktúr, pri ktorých je
  platiteľ osobou povinnou platiť daň ako príjemca alebo si odpočítava daň
  uplatnenú iným platiteľom (B.1, B.2); opravy faktúr (C.1, C.2) a ostatné
  zdaniteľné plnenia (D.1, D.2).
- **Ktoré faktúry treba vyhotoviť.** Povinnosť vyhotoviť faktúru vzniká voči
  inej zdaniteľnej osobe alebo právnickej osobe, ktorá nie je zdaniteľnou
  osobou — [§ 72 ods. 1 písm. a)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-a).
  Dodania súkromným osobám sa preto jednotlivo neuvádzajú, idú do súhrnov
  oddielu D.
- **Tovar s prenosom daňovej povinnosti.** Pri tovare podľa
  [§ 69 ods. 12](law:sk/2004/222#paragraf-69.odsek-12) písm. f) a g)
  (obilniny a technické plodiny z kapitol 10 a 12, kovy z kapitoly 72 a
  položiek 7301, 7308, 7314) sa uvádzajú aj prvé štyri číslice číselného kódu
  colného sadzobníka a množstvo
  ([§ 78a ods. 5](law:sk/2004/222#paragraf-78a.odsek-5)); pri písm. h) a i)
  (mobilné telefóny, integrované obvody) druh a množstvo tovaru.
- **Zjednodušené faktúry** sa uvádzajú súhrnom základov dane, dane a
  odpočítanej dane. Ak celková suma odpočítanej dane zo zjednodušených faktúr
  dosiahne za obdobie **3 000 eur**, uvádzajú sa súhrny v členení podľa
  dodávateľov — [§ 78a ods. 6](law:sk/2004/222#paragraf-78a.odsek-6).
- **Oddiel D.** Obraty evidované pokladnicou **eKasa** sa uvádzajú celkovou
  sumou podľa sadzieb (D.1), ostatné plnenia neuvedené inde súhrnom základov a
  dane podľa sadzieb (D.2) —
  [§ 78a ods. 8](law:sk/2004/222#paragraf-78a.odsek-8).
- **Opravy.** Chybu zistenú pred uplynutím lehoty opraví **opravný**
  kontrolný výkaz, na pôvodný sa neprihliada. Chybu zistenú po uplynutí
  lehoty opraví **dodatočný** kontrolný výkaz, v ktorom sa uvedú len
  doplnené alebo opravené údaje —
  [§ 78a ods. 12](law:sk/2004/222#paragraf-78a.odsek-12). Na výzvu daňového
  úradu treba nedostatky podaného výkazu odstrániť do piatich pracovných dní
  ([§ 78a ods. 13](law:sk/2004/222#paragraf-78a.odsek-13)).
- **Pokuty.** Za nepodanie, oneskorené podanie alebo neúplné či nesprávne
  údaje uloží daňový úrad pokutu do 10 000 eur, pri opakovanom porušení do
  100 000 eur — [§ 78a ods. 15](law:sk/2004/222#paragraf-78a.odsek-15).
- **Tlačivo.** Vzor ustanovuje predpis Ministerstva financií SR a kontrolný
  výkaz sa podáva vo formáte XML podľa opisu dátového rozhrania zverejneného
  finančným riaditeľstvom; na výkaz doručený inak sa neprihliada —
  [§ 78a ods. 16](law:sk/2004/222#paragraf-78a.odsek-16).

## Vzory tlačiva {#forms}

Finančná správa zverejňuje ku každému vzoru samostatnú XSD a staré ponecháva.
Obdobie sa podáva vo vzore, ktorý platil pre toto obdobie, takže dodatočný
kontrolný výkaz za rok 2022 sa podáva ešte vo vzore 2016. Modul obsahuje
všetky štyri, každý ako záznam verzie s vlastnou šablónou a schémou:

| Verzia | Obdobia | Koreň XML | Schéma | Rozdiel |
|---|---|---|---|---|
| KV DPH 2014 | 1. 1. 2014 – 31. 3. 2016 | `KVDPH` | `kv_dph_2014.xsd` | jeden oddiel B.3 pre všetky zjednodušené faktúry |
| KV DPH 2016 | 1. 4. 2016 – 30. 6. 2023 | `KVDPH_2016` | `kv_dph_2016.xsd` | B.3 rozdelený na B.3.1 a B.3.2 |
| KV DPH 2023 | 1. 7. 2023 – 31. 12. 2024 | `KVDPH_2023` | `kv_dph_2023.xsd` | rovnaké oddiely, nový koreň a menný priestor |
| KV DPH 2025 | od 1. 1. 2025 | `KVDPH_2025` | `kv_dph_2025.xsd` | rovnaké oddiely, nový koreň a menný priestor |

Pri zakladaní výkazu sa ponúkne len verzia platná pre jeho obdobie. Všetky
štyri schémy boli 19. 8. 2026 porovnané bajt po bajte s kópiami zverejnenými
Finančnou správou. Súbor schémy neuvádza, kedy bol upravený, takže neskoršiu
úpravu už zverejneného súboru modul sám nezistí.

## Nastavenie {#setup}

Okrem [spoločného nastavenia](module:l10n_cssk_kv_kh_base#setup):

- **Dane s prenosom daňovej povinnosti.** Pri inštalácii modul označí nákupné
  dane slovenskej osnovy s prenosom daňovej povinnosti — tuzemský prenos,
  nadobudnutie tovaru z iného členského štátu a s modulom
  [module:l10n_sk_vat_return](module:l10n_sk_vat_return) aj služby prijaté z
  EÚ — a pre každú slovenskú spoločnosť vytvorí predajnú daň **0 % Prenos
  daňovej povinnosti (§69 ods. 12, A.2)**. Túto daň používajte na faktúrach
  za plnenia podľa § 69 ods. 12; práve ona ich zaradí do A.2.
- **Identifikácia odberateľov.** Či sa vyhotovená faktúra uvedie jednotlivo v
  A.1, alebo v súhrne D.2, závisí od toho, či je odberateľ zdaniteľnou
  osobou. Odoo také pole nemá, preto modul považuje odberateľa s IČ DPH
  **alebo** IČO za podnikateľa a každého iného za súkromnú osobu. Doplňte
  IČO tuzemských odberateľov-podnikateľov vrátane živnostníkov, inak sa ich
  faktúry spočítajú do D.2.
- **Tovar podľa § 69 ods. 12.** Vo formulári produktu, karta *Účtovníctvo*,
  blok **Kontrolný výkaz DPH**: pri takom tovare nastavte *Tovar podľa § 69
  ods. 12 (KV DPH A.2)* na písm. f), g), h) alebo i) a pri f) a g) aj
  *Číselný kód tovaru (KV DPH)*. Ak kód chýba, použije sa colný kód produktu
  (HS / Intrastat), ak je nainštalovaný niektorý modul, ktorý ho poskytuje.
  Kód musí patriť do kapitol, ktoré zákon pre danú kategóriu uvádza. Tento
  tovar fakturujte v kilogramoch, tonách, metroch alebo kusoch — iné jednotky
  tlačivo neprijme. Pri ostatných plneniach podľa § 69 ods. 12, napríklad
  stavebných prácach podľa písm. j), pole nechajte prázdne; A.2 pri nich nesie
  len základ dane.
- **Zjednodušené faktúry.** Na dodávateľskej faktúre zaškrtnite pri bločkoch a
  iných zjednodušených faktúrach *Zjednodušená faktúra (KV DPH B.3)* vedľa
  dátumu faktúry. Prijatý doklad bez partnera sa posudzuje rovnako.
- **Pokladnice eKasa (D.1).** V denníku, do ktorého sa účtujú tržby
  pokladnice eKasa, otvorte *Rozšírené nastavenia* a v bloku *Kontrolný výkaz* nastavte **Prepis sekcie kontrolného výkazu** na `D.1`. Každý
  riadok s DPH tohto denníka sa potom vykáže ako obrat z eKasy v D.1 namiesto
  D.2. Faktúry podnikateľom vystavujte cez bežný predajný denník, aby sa
  naďalej dostali do A.1.

## Oddiely {#sections}

Ako modul napĺňa jednotlivé oddiely. Doklad s viacerými sadzbami dane dáva
jeden riadok za každú sadzbu.

| Oddiel | Čo sa doň dostane |
|---|---|
| A.1 | Vyhotovené faktúry so slovenskou DPH v nenulovej sadzbe odberateľovi s IČ DPH alebo IČO. Plnenia s nulovou sadzbou a oslobodené plnenia (vývoz, § 28 – 42) sa vynechajú. |
| A.2 | Vyhotovené faktúry s predajnou daňou s prenosom daňovej povinnosti (§ 69 ods. 12). Pri tovare podľa písm. f) – i) aj číselný kód alebo druh tovaru, množstvo a mernú jednotku. |
| B.1 | Prijaté faktúry s nákupnou daňou s prenosom daňovej povinnosti: tuzemský prenos, nadobudnutie tovaru z iného členského štátu, služby prijaté z EÚ. |
| B.2 | Ostatné prijaté faktúry s DPH, s číslom faktúry **dodávateľa** (*Referencia faktúry*). |
| B.3.1 / B.3.2 | Prijaté zjednodušené faktúry: jeden súhrn v B.3.1, kým je z nich **odpočítaná** daň za obdobie pod 3 000 eur ([§ 78a ods. 6](law:sk/2004/222#paragraf-78a.odsek-6)); od 3 000 eur odpočítanej dane súhrny podľa dodávateľov v B.3.2. Bloček s odpočtom 50 % sa započíta polovicou. Do marca 2016 jeden súhrn v B.3. |
| C.1 | Dobropisy a ťarchopisy vyhotovené odberateľom, ktorí sú zdaniteľnými osobami, s číslom opravovanej faktúry. Ťarchopis vykáže kladný rozdiel. |
| C.2 | Prijaté dobropisy a ťarchopisy s číslom opravovanej faktúry; aj opravy odpočítanej dane podľa § 53b zaznamenané modulom `l10n_sk_par53b`. |
| D.1 | Obraty z eKasy: riadky s DPH denníkov, ktorých sekcia kontrolného výkazu je nastavená na `D.1` (pozri [Nastavenie](#setup)). |
| D.2 | Zdaniteľné plnenia odberateľom bez IČ DPH aj IČO (alebo bez partnera) a dobropisy k nim: súhrn základov a dane v základnej sadzbe (20 % a viac) a v znížených sadzbách. |

Mimo výkazu zostávajú dodania tovaru a služieb do iného členského štátu
(patria do súhrnného výkazu) a dodania odberateľovi z EÚ **bez** slovenskej
DPH. Dodanie odberateľovi z EÚ, pri ktorom sa účtuje slovenská DPH —
typicky súkromnej osobe —, je tuzemské plnenie a uvedie sa v A.1 alebo D.2.

**Dátumy a sumy.** Deň dodania (*Den*) je *Dátum zdaniteľného plnenia*, inak
dátum faktúry; pri dani splatnej až platbou dátum platby. Odpočítaná daň v
B.1, B.2, C.2 a B.3 je tá časť dane, ktorú jej rozúčtovanie posiela na účet
DPH: daň pri vozidle s odpočtom 50 % vykáže polovicu. Koeficient podľa § 50
sa zohľadní rovnako, ale len ak je nastavený v rozúčtovaní dane.

Ťarchopis sa považuje za opravu, ak je vystavený tlačidlom **Debit Note**
(modul `account_debit_note`), ktoré ho prepojí s opravovanou faktúrou.

**Ručná oprava riadku.** Každá záložka oddielu okrem D.2 má na riadkoch
prepínač **Prepísať**. Po zaškrtnutí sa dajú upraviť sumy; opravené sumy
prežijú prepočet a znova sa použijú na riadok s rovnakou identitou. D.2
vykazuje stĺpce podľa sadzieb, ktoré sa prepísať nedajú.

## Druhy podania a opravy {#usage}

Typy výkazu sú **Riadny** (R), **Opravný** (O) a **Dodatočný** (D). Výkaz
pripravte a exportujte podľa [spoločnej príručky](module:l10n_cssk_kv_kh_base#usage).
Slovenské osobitosti:

- **Opravný** pred uplynutím lehoty: vytvorte ho z podaného výkazu tlačidlom
  *Dodatočný / opravný*, zvoľte *Opravný* a vypočítajte. Obsahuje celý zoznam
  ako pôvodný výkaz.
- **Dodatočný** po uplynutí lehoty: rovnaké tlačidlo, typ *Dodatočný*. Pri
  výpočte modul porovná nový výsledok s posledným známym úplným stavom obdobia
  a ponechá len rozdiely: nový alebo zmenený riadok s *kódom opravy* 2 a
  pôvodné hodnoty zmeneného alebo zrušeného riadku s *kódom opravy* 1.
  Nezmenené riadky vypadnú. Druhý dodatočný výkaz sa porovnáva so stavom po
  prvom, takže reťazené opravy zostanú konzistentné.

Pred vytvorením súboru export zastaví a vymenuje chybné doklady, ak:

- riadok v A.2, B.2 alebo B.3.2 nemá IČ DPH druhej strany alebo má iné ako
  slovenské (tieto oddiely prijmú len `SK` + 10 číslic);
- číslo dokladu je dlhšie ako 32 znakov, ktoré tlačivo dovoľuje (medzery sa
  odstránia automaticky; číslo sa neskracuje, lebo finančná správa ho páruje
  s podaním dodávateľa);
- riadok v A.1, A.2, B.1 alebo B.2 nemá deň dodania;
- riadok v C.1 alebo C.2 nemá číslo opravovanej faktúry (zadajte ho na
  dobropise ako *Original document number*; pri dodávateľskom dobropise sa
  číta aj *Zdrojový dokument*, ak neobsahuje číslo nákupnej objednávky);
- riadok A.2 s tovarom podľa písm. f) alebo g) nemá číselný kód alebo má kód
  mimo zákonom určených kapitol, alebo má riadok s tovarom podľa § 69 ods. 12
  jednotku, ktorú nemožno previesť na kg, t, m ani ks.

XML obsahuje IČ DPH, názov a adresu spoločnosti, druh výkazu a obdobie (rok a
mesiac alebo rok a štvrťrok).

## Obmedzenia {#limitations}

- **D.1 (eKasa) sa neodvodzuje z dokladov.** Vykazujú sa tam len denníky
  nastavené na `D.1`; každý iný predaj cez pokladnicu bez identifikovaného
  odberateľa-podnikateľa sa vykáže v **D.2**.
- **Ťarchopisy** sa dostanú do C.1 / C.2, len ak sú prepojené s opravovanou
  faktúrou (tlačidlo *Debit Note*). Ťarchopis vystavený ako bežná faktúra sa
  stále vykáže v A.1 / B.2.
- Rozdelenie medzi A.1 a D.2 závisí od toho, či má partner zapísané IČ DPH
  alebo IČO. Odberateľ-podnikateľ bez oboch sa spočíta do D.2; export pri
  odberateľoch v D.2, ktorí sú označení ako spoločnosť alebo už boli uvedení
  v A.1, zapíše upozornenie, to sa však na obrazovke nezobrazí.
- Trojstranný obchod a samozdanenie dane pri dovoze nie sú označené ako
  prenos daňovej povinnosti (čaká sa na potvrdenie účtovníka), takže sa v B.1
  neobjavia.
- Hranica 5 000 eur na faktúre pri mobilných telefónoch a integrovaných
  obvodoch podľa § 69 ods. 12 písm. h) a i) sa nekontroluje; kategóriu
  nastavte len pri tovare, ktorý ju spĺňa.
- Atribút `ONP` v C.1 / C.2 (oprava pri nedobytnej pohľadávke, od vzoru 2023)
  sa nevypĺňa nikdy.
- Pravidlá zaradenia sú najlepším možným odhadom; najmä zoznam tovarov podľa
  § 69 ods. 12 a oddiel D.1 ešte musí potvrdiť slovenský účtovník. Každý
  výkaz pred podaním skontrolujte.
