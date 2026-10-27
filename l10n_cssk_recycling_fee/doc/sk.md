---
title: Recyklačný poplatok CZ/SK (recyklačný poplatok / recyklační příspěvek)
summary: Poplatok za spätný zber elektrozariadení a batérií podľa platného cenníka organizácie zodpovednosti výrobcov, uvedený pri každom riadku faktúry, ako to vyžaduje zákon, a sčítaný po kategóriách na hlásenie organizácii.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Výrobca, distribútor alebo predajca elektrozariadení platí organizácii
zodpovednosti výrobcov (v Česku kolektívnemu systému) poplatok za každý kus
alebo kilogram uvedený na trh a oba štáty vyžadujú, aby sa pri predaji
uvádzal. Pri prenosných batériách platí opak: náklady na spätný zber sa
oddelene uvádzať **nesmú**.

Modul to dopĺňa do Odoo nad modulom OCA `account_ecotax`, ktorý už pozná
klasifikácie ekologického poplatku, viac klasifikácií na produkt a
podriadený riadok poplatku ku každému riadku faktúry. Pridáva to, čo je
české a slovenské:

- **sadzby s platnosťou od – do** pre každú klasifikáciu, v mene organizácie
  (EUR alebo CZK), vyberané podľa dátumu faktúry;
- klasifikáciu viazanú na **trh** (SK alebo CZ), ktorú použijú len
  spoločnosti z tohto štátu;
- poplatok **vytlačený pod každým riadkom faktúry** v zákonnom znení a súčet
  za doklad;
- **prenosné batérie** sa vypočítajú a vykážu, ale nikdy nevytlačia;
- **prehľad za obdobie** po kategóriách na hlásenie organizácii.

Strana objednávok je opísaná v časti [Predajné objednávky](#sales-orders).

## Právny rámec {#legal}

**Slovensko** — [zákon č. 79/2015 Z. z. o odpadoch](law:sk/2015/79):

- [§ 34 ods. 1 písm. d)](law:sk/2015/79#paragraf-34.odsek-1.pismeno-d):
  výrobca elektrozariadení je povinný pri predaji elektrozariadenia uvádzať
  *„na jeho obale alebo etikete alebo na daňovom či inom obdobnom doklade
  vyhotovenom pri jeho predaji výšku recyklačného poplatku“* určeného na
  úhradu nákladov na zber, prepravu a spracovanie elektroodpadu z domácností.
- [§ 37 ods. 1 písm. a)](law:sk/2015/79#paragraf-37.odsek-1.pismeno-a):
  distribútor uvádza pri predaji recyklačný poplatok, ak ho uviedol výrobca.
- [§ 46 ods. 2](law:sk/2015/79#paragraf-46.odsek-2) a
  [§ 48 ods. 1 písm. d)](law:sk/2015/79#paragraf-48.odsek-1.pismeno-d): pri
  prenosných batériách a akumulátoroch sa náklady na zber, spracovanie a
  recykláciu nesmú uvádzať oddelene.

**Česko** — [zákon č. 542/2020 Sb., o výrobcích s ukončenou
životností](law:cz/2020/542):

- **§ 73 odst. 1**: výrobca, distribútor a posledný predajca nového
  elektrozariadenia uvádzajú náklady na spätný odber, spracovanie, využitie a
  odstránenie na kus alebo kilogram **oddelene od ceny**, *„zejména formou
  samostatného údaje na daňovém dokladu“*. **§ 99 odst. 1** to isté ukladá pri
  pneumatikách.
- **§ 73 odst. 2**: uvedená suma nesmie prevýšiť náklady známe výrobcovi pri
  uvedení na trh; pri kolektívnom systéme je to príspevok, ktorý mu výrobca
  platí. Preto sa sadzba berie z cenníka systému.
- **§ 73 odst. 3**: povinnosti podľa cenových predpisov nie sú dotknuté.
- **§ 85 odst. 3**: pri nových prenosných batériách sa tieto náklady
  *„nesmějí … uvádět odděleně“*.
- **§ 125 odst. 2 písm. i) a l)**: neuvedenie nákladov, uvedenie vyššej sumy
  alebo ich uvedenie pri prenosných batériách je priestupok.
- Metodický pokyn Ministerstva životného prostredia ČR k § 73 a § 99 (revízia
  z 26. 10. 2021) žiada poplatok pri každej položke daňového dokladu a vo
  vzorových faktúrach ho zahŕňa do jednotkovej ceny; modul sa týmto
  spôsobom riadi.

Ani jeden zákon nepredpisuje samostatný riadok faktúry, preto modul ponúka
oboje: poplatok **zahrnutý** v cene s uvedením pri riadku (predvolené),
alebo **navyše** ako samostatný riadok.

## Nastavenie {#setup}

1. **Klasifikácie** — *Účtovníctvo → Konfigurácia → Ecotax → Classification*,
   jedna za každú položku cenníka vašej organizácie. Popisy sú v angličtine
   (modul ešte nemá slovenský preklad):
   - **Scheme Country** (štát systému) — SK alebo CZ. Za zákonný recyklačný
     poplatok sa považuje len klasifikácia so štátom; bez neho sa správa
     presne ako v module OCA.
   - **Ecotax Type** (spôsob výpočtu) — *Fixed* (za kus) alebo *Weight based*
     (za kg); **Category** (kategória), **Ecotax collector** (organizácia
     zodpovednosti výrobcov), **Product Status** (*Domestic* = z domácností,
     *Professional* = iné ako z domácností).
   - **Dated Rates** (sadzby) — *Valid From*, *Valid To* (prázdne pre
     platnú sadzbu) a *Rate* bez DPH v mene klasifikácie (doplní sa podľa
     štátu: EUR, CZK). Dve sadzby jednej klasifikácie sa nesmú prekrývať.
     Pôvodné polia OCA s jednou sumou sú len na čítanie a ukazujú dnešnú
     sadzbu; denná naplánovaná akcia ich prepne, keď začne platiť nová.
   - **Show on Documents** (uvádzať na dokladoch) — pri **prenosných
     batériách** odznačte.
2. **Produkty** — na záložke *Účtovníctvo* pridajte klasifikáciu
   (klasifikácie); produkt predávaný v oboch štátoch môže mať slovenskú aj
   českú a každá spoločnosť použije len svoju. Pri klasifikácii za kg
   vyplňte **hmotnosť** v kg. Distribútor môže na riadku klasifikácie
   produktu zadať **pevnú sumu** — poplatok, ktorý skutočne zaplatil jeho
   dodávateľ, v mene klasifikácie; tá potom nahradí cenník.
3. **Spôsob uvádzania** — *Účtovníctvo → Konfigurácia → Nastavenia*, blok
   **Recycling Fee**: *Included in the price* (zahrnutý v cene, predvolené)
   alebo *Separate line on top of the price* (samostatný riadok navyše).

Modul vytvorí **kategórie** ekologického poplatku — šesť kategórií
elektrozariadení (EEE1 – EEE6) a päť kategórií batérií (prenosné, LMT,
automobilové SLI, priemyselné, do elektrických vozidiel). **Cenníky
nedodáva**: sú vecou každej organizácie.

## Na faktúre {#invoice}

Každý riadok odberateľskej faktúry dostane poplatok podľa:

- sadzby platnej v **deň vyhotovenia faktúry** (kým nie je vyplnený, podľa
  účtovného dátumu);
- množstva prepočítaného na vlastnú mernú jednotku produktu (riadok
  predávaný po tuctoch znamená dvanásť kusov);
- pri klasifikácii za kg hmotnosti produktu; poplatok za kus sa zaokrúhli na
  dve desatinné miesta meny;
- prepočtu kurzom ku dňu faktúry, ak je faktúra v inej mene ako sadzba.

Pod popisom riadku vytlačená faktúra uvedie v národnom znení podľa štátu
klasifikácie:

    z toho recyklačný poplatok 3,60 € (0,90 €/ks)
    z toho recyklační příspěvek 100,00 Kč (0,50 Kč/kg × 2,000 kg = 1,00 Kč/ks)

a ďalej *bez DPH*, ak cena riadku obsahuje DPH, a pri faktúre v inej mene
pôvodnú sumu s kurzom. Doklad uzatvára riadok *Recyklačný poplatok spolu
bez DPH* / *Recyklační příspěvek celkem bez DPH*. Anglický stĺpec a súčet
*Eco Part* z modulu OCA sa na takých dokladoch skryjú. Poplatky klasifikácií
s odznačeným *Show on Documents* sa nevytlačia ani nezapočítajú do súčtu.

**Zaúčtovanie.** Pri zaúčtovaní sa poplatok ešte raz vypočíta ku
konečnému dátumu faktúry a odberateľská faktúra alebo dobropis, ktorého
klasifikácia **nemá k tomuto dátumu platnú sadzbu**, sa odmietne (ak nejde o
pevnú sumu). Po zaúčtovaní je poplatok zmrazený: neskoršia zmena cenníka
alebo hmotnosti ho neprepíše; vrátenie faktúry do konceptu ho vypočíta
nanovo.

## Prehľad pre organizáciu {#report}

*Účtovníctvo → Výkazy → Manažment → Recycling Fees* ukazuje kusy, kilogramy a
poplatok zo **zaúčtovaných odberateľských faktúr a dobropisov** (dobropisy so
záporným znamienkom) podľa štátu, kategórie, klasifikácie, organizácie a
obdobia, v mene organizácie bez ohľadu na menu faktúry. K dispozícii je
kontingenčná tabuľka, zoznam a graf; filtre pre SK, CZ, z domácností a
profesionálne. Prenosné batérie sú zahrnuté.

*Tlač → Recycling Fees (XLSX)* vyexportuje vybrané riadky: súhrnný hárok
podľa štátu, organizácie, kategórie, klasifikácie, druhu (z domácností /
profesionálne) a spôsobu výpočtu a druhý hárok s riadkami faktúr.

## Predajné objednávky {#sales-orders}

S aplikáciou Predaj a modulom OCA `account_ecotax_sale` sa sám nainštaluje
[module:l10n_cssk_recycling_fee_sale](module:l10n_cssk_recycling_fee_sale) a
pridá:

- **Poplatky na riadkoch objednávky**, vypočítané podľa sadzby platnej v
  **deň objednávky**, s rovnakým výberom trhu a prepočtom jednotiek. Faktúra
  ich vypočíta znova k svojmu dátumu, lebo zákon hovorí o daňovom doklade.
- **Pevná suma** z produktu sa prenesie z objednávky na faktúru.
- **Režim „navyše“.** Ak je zvolené *Separate line on top of the price*,
  nastavte v tom istom bloku **Recycling Fee Product** (produkt typu
  služba). Tlačidlo **Update Recycling Fee** na objednávke pridá jeden riadok
  za každú klasifikáciu a sadzbu DPH, s cenou rovnou súčtu poplatkov a s DPH
  tovaru, ku ktorému patrí (daň zahrnutá v cene sa dopočíta navrch, lebo
  cenník je bez DPH). Použije sa výnosový účet produktu poplatku, jeho dane
  nie. Opätovným stlačením sa riadky vytvoria nanovo; po ich vyfakturovaní
  tlačidlo odmietne. Prenosné batérie riadok nedostanú.

## Obmedzenia {#limitations}

- Sadzba sa vyberá podľa **dátumu faktúry**, kým český § 73 odst. 2 viaže
  sumu na okamih uvedenia na trh. Distribútor, ktorý predáva starší tovar
  cez zmenu cenníka, by mal použiť pevnú sumu na produkte.
- Cenníky sa nedodávajú; zadajte cenník svojej organizácie.
- Prehľad vychádza z odberateľských faktúr. Ak sa tovar dodá v jednom
  období a fakturuje v inom, zosúlaďte to v hlásení. Dodania do iných
  členských štátov a vývoz sú zahrnuté a treba ich vylúčiť, ak ich
  organizácia nezapočítava.
- V režime „navyše“ vznikajú samostatné riadky poplatku len z **predajnej
  objednávky**; faktúra vytvorená bez objednávky uvedie poplatok pri riadku,
  ale riadok poplatku nemá, takže sa navyše neúčtuje.
- Ponuky a objednávky uvedenie pri riadku netlačia; tlačí ho faktúra.
- Kategória pneumatík sa nedodáva; pneumatiky (český § 99) sa dajú nastaviť
  rovnako.
- Používateľské rozhranie je v angličtine; zákonné texty na faktúre sú po
  slovensky alebo po česky.
