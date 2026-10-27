---
title: Zálohové faktúry (predaj)
summary: Zálohová (preddavková) faktúra ako samostatný doklad, faktúra ku každej prijatej platbe a odpočet preddavku na vyúčtovacej faktúre.
verified: 19.0.2.8.0
---

## Na čo slúži {#purpose}

Preddavok sa v slovenskej aj českej praxi rieši tromi dokladmi:

1. **zálohová (preddavková) faktúra** — výzva na platbu; nie je účtovným ani
   daňovým dokladom a neúčtuje sa;
2. **faktúra k prijatej platbe** (v praxi aj *daňový doklad k prijatej
   platbe*) — vyhotovuje sa po prijatí peňazí, lebo daňová povinnosť vzniká
   dňom prijatia platby;
3. **vyúčtovacia faktúra** — celé plnenie, od ktorého sa odpočíta preddavok
   aj daň z neho už priznaná, takže sa DPH odvedie len raz.

Zálohové platby v štandardnom Odoo zaúčtujú faktúru za preddavok hneď. Tento
modul namiesto toho vedie zálohovú faktúru ako samostatný doklad podobný
cenovej ponuke s číslami `ADV00001`, `ADV00002`…, ktorý zákazník uhradí cez
QR kód, zákaznícky portál alebo prevodom. Do účtovníctva sa dostane až platba
a faktúra k nej.

Modul je nezávislý od krajiny. Slovenské a české účty nastavia lokalizačné
doplnky opísané v časti [Lokalizačné doplnky](#localization). Strana
dodávateľa je v module
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice).

## Právny rámec {#legal}

**Slovensko** — [zákon o DPH](law:sk/2004/222):

- Ak je platba prijatá pred dodaním tovaru alebo služby, vzniká daňová
  povinnosť z prijatej platby dňom jej prijatia —
  [§ 19 ods. 4](law:sk/2004/222#paragraf-19.odsek-4).
- Platiteľ je povinný vyhotoviť faktúru pri prijatí platby pred dodaním
  tovaru alebo služby inej zdaniteľnej osobe alebo právnickej osobe —
  [§ 72 ods. 1 písm. f)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-f) a
  [písm. g)](law:sk/2004/222#paragraf-72.odsek-1.pismeno-g) — a to do 15 dní
  odo dňa prijatia platby **alebo** do konca kalendárneho mesiaca, v ktorom
  bola platba prijatá —
  [§ 73 ods. 1 písm. b)](law:sk/2004/222#paragraf-73.odsek-1.pismeno-b).
- Faktúra obsahuje dátum prijatia platby, ak ho možno určiť a ak sa líši od
  dátumu vyhotovenia —
  [§ 74 ods. 1 písm. d)](law:sk/2004/222#paragraf-74.odsek-1.pismeno-d).

**Česko** — [zákon č. 235/2004 Sb., o dani z přidané hodnoty](law:cz/2004/235):

- § 20a odst. 2: prijatím úplaty pred uskutočnením plnenia vzniká povinnosť
  priznať daň ku dňu jej prijatia — okrem prípadu, keď plnenie ešte nie je
  známe dostatočne určito; podľa § 20a odst. 3 to znamená poznať aspoň tovar
  alebo službu, sadzbu dane a miesto plnenia.
- § 28 odst. 1 písm. d) ukladá vystaviť k takej úplate daňový doklad,
  § 28 odst. 8 lehotu 15 dní odo dňa vzniku povinnosti.
- § 36 odst. 2: základom dane je prijatá úplata znížená o daň.
- § 37a: na vyúčtovaní je základom rozdiel medzi celým plnením a už
  zdanenými preddavkami; ak je záporný, použije sa sadzba a kurz z preddavkov.

## Nastavenie {#setup}

*Predaj → Konfigurácia → Nastavenia*, blok **Fakturácia**:

| Nastavenie | Účel |
|---|---|
| Denník daňových dokladov k preddavkom | Denník, do ktorého idú faktúry k prijatým platbám. Pri inštalácii modul vytvorí pre aktuálnu spoločnosť všeobecný denník **TDADV** a nastaví ho. |
| Zúčtovací účet preddavkov | Párovateľný účet, na ktorom sa stretne platba s faktúrou k nej, napr. 324001. |
| Účet prijatých preddavkov (krátkodobé) | Nesie preddavok bez DPH až do vyúčtovania, napr. 324000. |
| Účet prijatých preddavkov (dlhodobé) | To isté pre preddavky označené ako *Dlhodobý preddavok*, napr. 475000. |

Bez lokalizačného doplnku vyplňte tri účty sami.

Pred prvým preddavkom skontrolujte aj:

- **Bankový účet spoločnosti** — zálohová faktúra vytlačí bankový účet
  spoločnosti, prednostne v mene objednávky, a ak sú v nastaveniach
  fakturácie zapnuté QR kódy, aj platobný QR kód.
- **Produkt *Advance*** (v preklade *Preddavok*) — vznikne pri prvom
  preddavku a je produktom
  všetkých riadkov preddavku, ak nezvolíte *Zahrnúť objednané položky* (pozri
  [nižšie](#create)). Jeho dane z predaja určujú DPH takých preddavkov.

### Lokalizačné doplnky {#localization}

[module:l10n_cz_sale_order_advance_invoice](module:l10n_cz_sale_order_advance_invoice)
a
[module:l10n_sk_sale_order_advance_invoice](module:l10n_sk_sale_order_advance_invoice)
vyplnia uvedené nastavenia každej spoločnosti s českou alebo slovenskou
účtovou osnovou — pri inštalácii a znova vždy, keď sa osnova načíta neskôr,
napríklad pre novú spoločnosť:

| Úloha | Účet | Slovenský názov | Český názov |
|---|---|---|---|
| Zúčtovací účet (vytvorí ho doplnok, párovateľný) | 324001 | Prijaté preddavky – zúčtovanie (daňový doklad) | Přijaté zálohy – zúčtování (daňový doklad) |
| Prijaté preddavky, krátkodobé | 324000 | Prijaté preddavky | Přijaté provozní zálohy |
| Prijaté preddavky, dlhodobé | 475000 | Dlhodobé prijaté preddavky | Dlouhodobé přijaté zálohy |
| Denník TDADV | — | Faktúry k prijatým platbám | Daňové doklady k přijatým platbám |

Vyplnia sa len prázdne nastavenia; účty, ktoré ste zvolili sami, ostanú.

## Vystavenie zálohovej faktúry {#create}

Na potvrdenej objednávke kliknite na **Vytvoriť zálohovú faktúru** a zvoľte:

| Možnosť | Výsledok |
|---|---|
| Celá suma | jeden riadok *Preddavok* za každý riadok objednávky v sume jeho medzisúčtu |
| Percento z celkovej sumy | jeden riadok *Preddavok* na dané percento zo sumy bez DPH |
| Pevná suma | jeden riadok *Preddavok* na zadanú sumu bez DPH |
| **Zahrnúť objednané položky** | namiesto riadkov *Preddavok* produkty, množstvá a sadzby DPH z objednávky; pri percente alebo pevnej sume sa pomerne znížia jednotkové ceny, množstvá ostanú |

**Voľbu *Zahrnúť objednané položky* použite vždy, keď má objednávka inú
sadzbu DPH ako produkt *Preddavok* alebo keď kombinuje sadzby.** Bez nej má
každý riadok preddavku dane produktu *Preddavok* a rovnako aj faktúra k
platbe. Vyúčtovacia faktúra rozdiel vyrovná, takže sa DPH nestratí ani
nezaplatí dvakrát, ale daň z prijatej platby bola priznaná v nesprávnej
sadzbe.

Zálohová faktúra sa otvorí ako nový doklad prepojený s objednávkou. Na nej:

- **Dátum splatnosti** sa riadi platobnými podmienkami; **Bankový účet** a
  **QR kód platby** určujú, čo sa vytlačí.
- **Dlhodobý preddavok** pošle preddavok bez DPH na dlhodobý účet. Označte ho
  pred potvrdením preddavku.
- *Odoslať e-mailom* a *Tlačiť* vytvoria „Zálohovú faktúru“ s dátumom
  vystavenia a splatnosti, so sumami s DPH bez rozpisu dane a s bankovým
  účtom, číslom preddavku ako referenciou platby a QR kódom.

Objednávka dostane sekciu *Zálohové faktúry* s riadkom s nulovým množstvom za
každý preddavok, ktorý priebežne ukazuje jeho stav, dátum úhrady a faktúru k
platbe, a tlačidlo **Zálohové faktúry**. Zálohové faktúry sa nezobrazujú v
*Cenových ponukách* ani v *Objednávkach*. Majú vlastnú ponuku *Predaj →
Objednávky → Zálohové faktúry* a *Účtovníctvo → Zákazníci → Zálohové
faktúry*, kde sa dá vystaviť aj zálohová faktúra bez objednávky (pozri
[Preddavky bez objednávky](#standalone)).

Potvrdenie preddavku nikdy nevytvorí dodávku: tovar sa dodáva z pôvodnej
objednávky.

## Prijatie platby {#payment}

**Stav úhrady** preddavku (*Neuhradené*, *Čiastočne uhradené*, *Plne
uhradené*, *Preplatené*) sa riadi platbami, ktoré sú s ním prepojené. Obe
tlačidlá uvedené nižšie sa zobrazia, keď je preddavok odoslaný alebo
potvrdený a časť ešte nie je uhradená. Platba môže prísť štyrmi spôsobmi:

- **Online** cez zákaznícky portál, ak je nastavený poskytovateľ platieb —
  preddavok vyžaduje platbu ako online cenová ponuka. Platba sa zaúčtuje
  **na zúčtovací účet**.
- **Zaevidovať platbu** — zaznamená platbu v bankovom alebo pokladničnom
  denníku, zaúčtovanú **na zúčtovací účet**, a ak bol preddavok ešte ponukou,
  potvrdí ho. Suma nesmie prevýšiť neuhradenú časť.
- **Prepojiť manuálny prevod** — pripojí existujúcu prijatú platbu toho
  istého zákazníka, ktorá nie je spárovaná so žiadnou faktúrou. Ak bola
  zaúčtovaná na pohľadávku zákazníka, presunie ju prevodový zápis v denníku
  rôznych operácií na **zúčtovací účet**.
- **Z bankového výpisu**, automaticky alebo sprievodcom, s modulom
  [module:sale_order_advance_invoice_payment_match](module:sale_order_advance_invoice_payment_match).

## Faktúra k prijatej platbe {#tax-document}

Keď je preddavok čo i len čiastočne uhradený, **Stav zaúčtovania** sa zmení z
*Niet čo zaúčtovať* na **Čaká sa** a v hlavičke sa objaví **Vytvoriť
faktúru**. Tlačidlo vytvorí koncept faktúry k platbe na uhradenú sumu, ktorú
ešte nepokrýva skoršia faktúra k platbe. Každá splátka čiastočne uhradeného
preddavku tak môže mať vlastnú.

Faktúra k prijatej platbe:

- je faktúrou zákazníkovi v denníku TDADV, rozdelenou podľa sadzieb DPH v
  pomere riadkov preddavku;
- má ako dátum zdaniteľného plnenia **dátum prijatia platby** a riadok
  „Platba zálohovej faktúry ADV00042 prijatá dňa …“;
- účtuje sumu bez DPH na účet prijatých preddavkov (324000, pri dlhodobom
  preddavku 475000) a pohľadávku na **zúčtovací účet**;
- tlačí sa ako **Daňový doklad** s *Dátumom vystavenia*, *Dátumom úhrady*
  namiesto dátumu zdaniteľného plnenia a bez splatnosti, platobných údajov a
  QR kódu.

Skontrolujte ju a zaúčtujte. Zaúčtovanie ju na zúčtovacom účte spáruje s
platbami preddavku a stav sa zmení na **Zaúčtované**.

Zoznam preddavkov ukazuje lehotu v stĺpci *Dátum splatnosti zaúčtovania*,
po jej uplynutí na červeno. Riadi sa krajinou spoločnosti (pozri
[Právny rámec](#legal)):

| Krajina | Lehota |
|---|---|
| Česko | 15 dní po platbe |
| Slovensko | 15 dní po platbe alebo posledný deň mesiaca platby, podľa toho, čo nastane neskôr (pri platbách pred rokom 2016 15 dní) |
| iná | 15 dní po platbe |

## Vyúčtovanie {#final-invoice}

Objednávku vyfakturujte ako obvykle (*Vytvoriť faktúru* na objednávke). Každý
uhradený preddavok sa pridá pod bežné riadky do sekcie *Zálohové faktúry* ako
záporný riadok:

- **Časť pokrytá zaúčtovanými faktúrami k platbe**: suma bez DPH, ktorú tieto
  faktúry priznali, na účte prijatých preddavkov s ich DPH, takže sa daň
  priznaná z platby vráti. Faktúry vo viacerých sadzbách sa odpočítajú po
  riadku za každú sadzbu.
- **Prijatá časť, ktorú nepokrýva zaúčtovaná faktúra k platbe**: suma s DPH,
  bez dane, na výnosový účet produktu *Preddavok*. DPH z tejto časti potom
  vyrubí sama vyúčtovacia faktúra.

Odpočíta sa len to, čo bolo **prijaté**: čiastočne uhradený preddavok sa
odpočíta v uhradenej výške, nie v plnej. Faktúra k platbe v koncepte
nepokrýva nič. Preddavok sa odpočíta, až keď je na ňom niečo uhradené, a len spolu s bežnými
riadkami pripravenými na fakturáciu. Ak sa zatiaľ nedá fakturovať nič iné,
napríklad preto, že nič nebolo dodané, Odoo oznámi, že nie je čo fakturovať.

**Cudzia mena.** Odpočet sa prepočíta kurzom, ktorým boli priznané jeho
faktúry k platbe, a rovnako aj časť plnenia, ktorú preddavok uhradil. Len
zvyšok plnenia sa prepočíta kurzom vyúčtovacej faktúry. Plne predplatené
plnenie tak vyjde s nulovou DPH a na pohľadávke nič neostane, ako to pre
Česko vyžaduje § 37a.

## Preddavky bez objednávky {#standalone}

Zálohová faktúra vystavená priamo z ponuky *Zálohové faktúry* nemá
objednávku. Na jej vyúčtovanie otvorte vyúčtovaciu faktúru zákazníkovi, kým je
konceptom, a kliknite na **Prepojiť zálohové faktúry**. Ponúknu sa potvrdené
preddavky toho istého zákazníka, na ktorých je niečo uhradené a ktoré
neodpočítava iná faktúra. Každý sa pridá presne ako na vyúčtovaní
objednávky: časť pokrytá zaúčtovanými faktúrami k platbe bez DPH so stornom
dane, po riadku za každú sadzbu, a zvyšok prijatej sumy s DPH bez dane.

## Obmedzenia {#limitations}

- Faktúra k platbe nevznikne po úhrade sama: kliknite na **Vytvoriť
  faktúru**, alebo ju nechajte vytvoriť doplnok na párovanie výpisov.
- Platba pripojená cez *Prepojiť manuálny prevod* sa presunie na zúčtovací
  účet, len kým je jej riadok pohľadávky otvorený a spoločnosť má denník
  rôznych operácií iný než denník faktúr k platbám. Inak riadok faktúry k
  platbe na zúčtovacom účte spárujte s platbou sami.
- Bez faktúry k platbe sa odpočet zúčtovacieho účtu nedotkne a platba na ňom
  ostane, kým ju nevyrovnáte ručným zápisom. Daňová povinnosť pritom v oboch
  krajinách vzniká prijatím platby (v Česku s výnimkou § 20a odst. 2 pre
  plnenie, ktoré ešte nie je známe dostatočne určito).
- Bez voľby *Zahrnúť objednané položky* majú preddavok aj faktúra k platbe
  sadzbu DPH produktu *Preddavok*, nie objednávky.
- Prenesenie daňovej povinnosti a plnenia do iného členského štátu nemajú
  osobitné spracovanie: nevyhotovujte faktúru k platbe tam, kde platba
  daňovú povinnosť nezakladá.
