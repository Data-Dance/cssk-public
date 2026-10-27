---
title: Peňažný denník CZ/SK
summary: Peňažný denník odvodený z bežného účtovníctva v Odoo — každá úhrada sa stane dátumovaným, očíslovaným riadkom v príslušnom členení, pre živnostníkov s daňovou evidenciou alebo jednoduchým účtovníctvom.
verified: 19.0.1.6.3
---

## Na čo slúži {#purpose}

Živnostník, ktorý nevedie podvojné účtovníctvo, musí aj tak zaznamenávať
príjmy a výdavky **v okamihu ich úhrady** a v členení, ktoré potrebuje daňové
priznanie — v **peňažnom denníku**. Odoo samo o sebe vedie len podvojné
účtovníctvo.

Modul ho nenahrádza. Faktúry, úhrady, import bankových výpisov aj DPH robíte v
Odoo ako doteraz; peňažný denník je **samostatná, uložená kniha vygenerovaná zo
zaúčtovaných dokladov**:

- samotná faktúra do denníka nič nezapíše — riadok vytvorí až **úhrada**;
- úhrada sa cez párovanie dohľadá k faktúre, ktorú uhradila, takže riadok nesie
  **kategóriu** toho, čo sa skutočne predalo alebo kúpilo (tovar, služby,
  mzdy…), nie len „banka“;
- DPH z každej úhrady je v samostatnom stĺpci, oddelene od sumy, ktorá vstupuje
  do základu dane z príjmov;
- riadky sú v rámci roka očíslované v časovom slede a zostávajú tak, kým denník
  znova nevygenerujete.

Toto je spoločný základ. Národný katalóg kategórií, tlač denníka v národnom
usporiadaní a údaje pre daňové priznanie dodáva modul krajiny:

- [module:l10n_sk_cash_journal](module:l10n_sk_cash_journal) — Slovensko;
- [module:l10n_cz_cash_journal](module:l10n_cz_cash_journal) — Česko.

Nainštalujte modul svojej krajiny; tento modul sa nainštaluje s ním.

## Právny rámec {#legal}

Ani jedna krajina nepredpisuje softvér; zákon určuje obsah evidencie.

- **Slovensko — daňová evidencia.** Daňovník, ktorý uplatňuje preukázateľne
  vynaložené daňové výdavky, môže viesť evidenciu o príjmoch a daňových
  výdavkoch *„v časovom slede v členení potrebnom na zistenie základu dane“*,
  ako aj o majetku, zásobách, pohľadávkach a záväzkoch —
  [§ 6 ods. 11 zákona o dani z príjmov](law:sk/2003/595#paragraf-6.odsek-11).
  Pri paušálnych výdavkoch vedie len evidenciu príjmov a evidenciu zásob a
  pohľadávok — [§ 6 ods. 10](law:sk/2003/595#paragraf-6.odsek-10).
- **Slovensko — jednoduché účtovníctvo.** Účtovnými knihami sú peňažný denník,
  kniha pohľadávok, kniha záväzkov a pomocné knihy; peňažný denník obsahuje
  stav peňažných prostriedkov v hotovosti a na účtoch v bankách, príjmy a
  výdavky v členení potrebnom na zistenie základu dane a priebežné položky —
  [§ 15 ods. 1 a 2 zákona o účtovníctve](law:sk/2002/431#paragraf-15.odsek-1).
  Stĺpce určuje § 4 [opatrenia MF/27076/2007-74](law:sk/2007/628).
- **Česko — daňová evidence.** Evidencia príjmov a výdavkov *„v členění
  potřebném pro zjištění základu daně“* a majetku a dlhov —
  [§ 7b zákona o daních z příjmů](law:cz/1992/586). Pojem *peněžní deník*
  patrí jednoduchému účtovníctvu podľa
  [§ 13b zákona o účetnictví](law:cz/1991/563), ktoré
  [§ 1f toho istého zákona](law:cz/1991/563) umožňuje len niektorým neziskovým
  subjektom, živnostníkovi nie.

## Nastavenie {#setup}

### Nastavenia

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Peňažný denník**:

| Nastavenie | Účel |
|---|---|
| Spôsob vedenia účtovníctva | Podvojné účtovníctvo (predvolené), daňová evidencia, jednoduché účtovníctvo (len slovenské spoločnosti — českej spoločnosti sa odmietne) alebo paušálne výdavky. Denník sa dá vygenerovať pri každom spôsobe; nastavenie rozhoduje len o tom, ktorú tabuľku zostatkov zobrazia údaje pre slovenské daňové priznanie. |
| Rozdelenie čiastočnej úhrady | Ako sa čiastočná úhrada rozdelí medzi základ dane a DPH: **pomerne** (predvolené, konvencia Odoo), **najprv DPH** alebo **najprv základ**. Zvoľte jeden spôsob vo vnútornom predpise a dodržte ho celý rok; pri úplnej úhrade dávajú všetky tri rovnaký výsledok. |
| Priradenie účtov | Tlačidlo *Priradiť účty ku kategóriám peňažného denníka* vyplní kategóriu na každom účte, ktorý pozná priradenie krajiny. Nikdy neprepíše už nastavenú kategóriu a dá sa spustiť znova po doplnení účtov. |
| Začiatok peňažného denníka | Prvý deň, od ktorého denník vedie. Staršie úhrady ignoruje — použite pri začatí v priebehu roka. |

### Kategórie na účtoch

Odkiaľ riadok berie kategóriu, sa určuje **na účte**. Otvorte účet
(*Účtovníctvo → Konfigurácia → Účtový rozvrh*) a jeho záložku **Peňažný
denník**:

- **Kategória peňažného denníka** — kategória pre úhrady cez tento účet.
- **Kategória peňažného denníka (príjem)** — len pre účty, cez ktoré peniaze
  idú oboma smermi a každý smer patrí do iného stĺpca: na účet úveru príde úver
  a odchádzajú z neho splátky, cez účet DPH sa daň odvádza a vracia sa nadmerný
  odpočet. Ak jedna kategória pokryje oba smery, nechajte ju prázdnu.

Modul krajiny priradí národnú účtovú osnovu automaticky — pri inštalácii a
znova pri každom načítaní osnovy — ale vyplní len prázdne polia. Účty
pohľadávok, záväzkov a preddavkov sa zámerne nepriraďujú; pozri
[ako vznikajú riadky](#rows).

Jednotlivý riadok faktúry môže kategóriu účtu prepísať: v *Účtovníctvo →
Účtovníctvo → Položky účtovnej knihy* zobrazte voliteľný stĺpec *Kategória
peňažného denníka* a nastavte ju na riadku — napríklad pri faktúre, ktorá je
sčasti tovar a sčasti služby.

### Samotné kategórie

*Účtovníctvo → Účtovníctvo → Peňažný denník → Kategórie* (len pre správcov
účtovníctva) zobrazí katalóg dodaný modulom krajiny. Každá kategória má
**druh** — príjem, výdavok alebo priebežná položka — a dva príznaky:

- **Ovplyvňuje základ dane** — vypnutý pri výbere podnikateľa, úvere, odvode
  DPH či zaplatenej dani z príjmov;
- **Nepeňažné** — pre zápisy, pri ktorých sa nepohli peniaze, ale do denníka
  patria, typicky odpisy (pozri [nižšie](#non-cash)).

**Kód v daňovom priznaní** určuje riadok daňového priznania fyzickej osoby,
do ktorého kategória vstupuje (SK DPFO typ B tabuľka 1, CZ Příloha č. 1);
nastavuje ho národný modul a podľa neho sa zoskupujú
[údaje pre daňové priznanie](#tax-return).

Priebežná položka nesmie ovplyvňovať základ dane ani byť nepeňažná; formulár
to odmietne. Môžete pridať vlastné kategórie; kód musí byť v rámci krajiny
jedinečný.

## Generovanie denníka {#usage}

*Účtovníctvo → Účtovníctvo → Peňažný denník → Generovať*: zvoľte obdobie a
kliknite na **Generovať**.

- Riadky obdobia sa vymažú a znova vytvoria zo **zaúčtovaných** dokladov, takže
  opakované spustenie dá rovnaký denník.
- **Riadky označené *Ručne*** a riadky **k dátumu uzamknutia účtovníctva alebo
  skôr** zostanú. Obdobie celé uzavreté dátumom uzamknutia sa vygenerovať nedá.
- Celý rok sa prečísluje `2026/00001`, `2026/00002`, … v časovom slede.

Nič sa nedeje samo: úhrada zaúčtovaná dnes sa v denníku objaví pri najbližšom
generovaní. Výsledok sa otvorí v zozname *Peňažný denník* s filtrom **Tento
rok**.

## Ako vznikajú riadky {#rows}

Riadok vznikne pri každom pohybe peňazí na účte bankového alebo pokladničného
denníka, na účtoch neuhradených príjmov a platieb Odoo, na dočasnom bankovom
účte a na účte interných prevodov — v ľubovoľnom účtovnom denníku, takže sa
započíta aj oprava v *Rôznych operáciách*, ktorá pohne peniazmi. Tie isté
peniaze sa započítajú **raz**: úhrada už spárovaná s riadkom bankového výpisu
sa objaví cez výpis, nie dvakrát.

Od peňazí sa modul cez párovanie dostane k tomu, čo sa uhradilo:

- **Faktúra.** Úhrada sa rozdelí podľa riadkov a sadzieb DPH dokladu, takže
  faktúra za tovar a služby dá dva riadky. Čiastočná úhrada sa delí podľa
  nastavenia *Rozdelenie čiastočnej úhrady*.
- **Priamy zápis** — bankový poplatok, platba daňovému úradu — dostane
  kategóriu protiúčtu.
- **Vrátená suma** (dobropis, vrátenie od dodávateľa) je **storno**: zníži
  vlastný stĺpec, namiesto toho aby sa objavila v opačnom. Predaj 1 000 a
  dobropis 200 znamená príjem 800, nie príjem 1 000 a výdavok 200.
- **Prevod medzi vlastnou bankou a pokladnicou** je priebežná položka, nie
  príjem ani výdavok.
- **Úhrada na pohľadávke alebo záväzku bez dokladu** — obvykle preddavok — sa
  zaradí do kategórie účtu, ak ju má, inak sa označí na kontrolu. Stĺpec závisí
  od toho, za čo preddavok je, a to viete len vy. Zálohová faktúra zaúčtovaná na
  účet konečného plnenia nesie kategóriu toho účtu.

Každý riadok má sumu, ktorá vstupuje do základu dane (u platiteľa DPH bez
dane), a samostatne **DPH**; u neplatiteľa časť DPH chýba.

### Nepeňažné riadky {#non-cash}

Odpis je výdavok, pri ktorom sa banka nepohne, zatiaľ čo úhrada za samotný
majetok výdavkom nie je. Každý zaúčtovaný riadok na účte s kategóriou
označenou **Nepeňažné** sa stane riadkom bez peňažného stĺpca, mimo bankových
a pokladničných denníkov. Započíta sa do základu dane, nie do peňažných súčtov.
Stornovaný alebo dobropisovaný odpis je **storno**: stĺpec odpisov znižuje,
nepripočíta sa k nemu.

## Riadky na kontrolu {#review}

Modul nič neodhaduje. Keď nevie rozhodnúť, riadok aj tak zapíše so sumou,
ale zvýrazní ho a označí **Na kontrolu** s dôvodom:

| Dôvod | Čo urobiť |
|---|---|
| Účet … nemá kategóriu peňažného denníka. | Nastavte kategóriu na účte (alebo na riadku dokladu) a denník znova vygenerujte. |
| Peniaze prišli / odišli cez …, ktorý má kategóriu … | Cez účet idú peniaze oboma smermi: nastavte na ňom *Kategóriu peňažného denníka (príjem)*. |
| Platba na … nie je spárovaná s dokladom — preddavok? | Priraďte účtu kategóriu alebo spárujte úhradu s faktúrou a denník znova vygenerujte. |
| Peniaze na ceste cez … bez kategórie priebežnej položky. | Priraďte účtu kategóriu priebežnej položky. |
| Reťazec párovania je dlhší ako 5 krokov; vyriešte ho ručne. | Dohľadajte a opravte párovanie ručne. |

*Účtovníctvo → Účtovníctvo → Peňažný denník → Na kontrolu* ich zobrazí všetky.
Opravte príčinu — účet, riadok dokladu, párovanie — a denník **znova
vygenerujte**, namiesto úpravy riadku: upravený vygenerovaný riadok sa pri
ďalšom generovaní nahradí.

Riadok môžete pridať aj ručne v zozname *Peňažný denník*. Zaškrtnite na ňom
**Ručne**, inak ho najbližšie generovanie vymaže.

## Tlač {#print}

*Účtovníctvo → Účtovníctvo → Peňažný denník → Tlač*: zvoľte obdobie a výstup.

- **PDF** — denník v národnom usporiadaní z modulu krajiny. Bez neho vás
  tlačidlo upozorní; vytlačte radšej tabuľku.
- **Tabuľka** — zošit XLSX so všetkými riadkami obdobia (číslo, dátum, doklad,
  partner, kategória, druh, peniaze, príjem, výdaj, DPH, storno, základ dane,
  nepeňažné, kontrola) a hárkom **súčtov za kategórie**. Slovenský modul pridá
  na začiatok hárok so zákonným usporiadaním.

## Údaje pre daňové priznanie {#tax-return}

Moduly krajín z denníka pripravia údaje, ktoré žiada priznanie k dani z príjmov
fyzických osôb: príjmy a výdavky z denníka a stavy na začiatku a na konci roka
z hlavnej knihy. Pozri
[údaje pre DPFO typ B](module:l10n_sk_cash_journal#dpfo) a
[údaje pre českú Přílohu č. 1](module:l10n_cz_cash_journal#priloha).

## Obmedzenia {#limitations}

- **Denník je len taký dobrý ako priradenie účtov.** Každý nepriradený účet
  vytvára riadky na kontrolu; pred každou tlačou skontrolujte *Na kontrolu*.
- **Generuje sa ručne.** Denník sám nové úhrady nesleduje.
- **Úprava vygenerovaného riadku nevydrží.** Generovanie ho nahradí. Ak ho
  označíte *Ručne*, váš riadok zostane, ale generovanie vedľa neho aj tak
  vytvorí nový riadok pre tú istú úhradu — opravte preto radšej účet alebo
  riadok dokladu.
- **Ručne pridaný riadok dostane číslo až pri najbližšom generovaní.**
- **Kategórie na účtoch nie sú za spoločnosť.** Spoločnosti so spoločnou
  osnovou zdieľajú aj priradenie; riešením je prepísanie na riadku dokladu.
- **Len peňažný denník.** Knihu pohľadávok, knihu záväzkov ani evidenciu
  majetku, ktoré jednoduché účtovníctvo a daňová evidencia tiež vyžadujú, modul
  nevytvára; stavy ku koncu roka berie z hlavnej knihy.
- Údaje pre daňové priznanie sú pomôcka na kontrolu a prepísanie do priznania,
  nie podanie.
