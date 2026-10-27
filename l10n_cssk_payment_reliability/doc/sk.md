---
title: CZ/SK kontrola spoľahlivosti dodávateľa
summary: Pred úhradou dodávateľovi overí v registroch finančnej správy jeho spoľahlivosť a bankový účet, na ktorý platíte, a výsledok ponechá na faktúre a úhrade ako doklad.
verified: 19.0.1.3.0
---

## Na čo slúži {#purpose}

V oboch krajinách môže platiteľ, ktorý nakupuje od dodávateľa, zaplatiť
namiesto neho daň, ktorú dodávateľ neodviedol — na Slovensku ide o **ručenie
za daň**, v Česku o *ručení za nezaplacenou daň*. Dve okolnosti, ktoré
ručenie zakladajú, sa dajú pred úhradou overiť vo verejných registroch:

- či finančná správa dodávateľa neoznačila (SK: zoznam platiteľov, u ktorých
  nastali dôvody na zrušenie registrácie; CZ: *nespolehlivý plátce*);
- či je bankový účet, na ktorý platíte, **zverejnený** v zozname bankových
  účtov dodávateľa.

Modul sa registrov opýta pri zaúčtovaní dodávateľskej faktúry alebo úhrady
dodávateľovi, odpoveď s časovou pečiatkou zapíše na doklad a pri riziku
zobrazí upozornenie. Zaúčtovanie ani úhradu **nikdy nezablokuje**:
rozhodnutie ostáva na vás a záznam ukazuje, čo register v tom čase uvádzal.

Samotný modul žiadne pripojenie k registru nemá. Údaje dodáva modul pre
príslušnú krajinu:

| Dodávateľ | Modul | Register |
|---|---|---|
| český | [module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) | webová služba ADIS Ministerstva financií ČR (register platiteľov DPH) |
| slovenský | [module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability) | otvorené dáta Finančnej správy SR |

Bez modulu pre krajinu dodávateľa skončí každá kontrola stavom
*Neoverené / nedostupné*, bez upozornenia.

## Právny rámec {#legal}

**Slovensko** — [zákon o DPH](law:sk/2004/222):

- Podľa [§ 69 ods. 13](law:sk/2004/222#paragraf-69.odsek-13) platiteľ,
  ktorému je dodaný tovar alebo služba, ručí za daň uvedenú na faktúre, ktorú
  dodávateľ nezaplatil, ak vedel alebo vedieť mal a mohol, že daň nebude
  zaplatená. Dostatočným dôvodom je podľa
  [písm. c)](law:sk/2004/222#paragraf-69.odsek-13.pismeno-c) aj úhrada na iný
  účet, ako je bankový účet dodávateľa, ktorý bol **v deň uskutočnenia
  platby zverejnený** v zozname bankových účtov; dňom platby je deň, keď ste
  banke zadali platobný príkaz.
- Zoznam bankových účtov zverejňuje finančné riaditeľstvo podľa
  [§ 6 ods. 6](law:sk/2004/222#paragraf-6.odsek-6).
- Podľa [§ 69 ods. 14](law:sk/2004/222#paragraf-69.odsek-14) finančné
  riaditeľstvo zverejňuje platiteľov, u ktorých nastali dôvody na zrušenie
  registrácie podľa § 81 ods. 3 písm. b) druhého bodu (opakované nepodanie
  priznania alebo kontrolného výkazu, nezaplatenie dane, nezastihnuteľnosť na
  adrese sídla a pod.).
- Ručenie sa uplatňuje podľa [§ 69b](law:sk/2004/222#paragraf-69b).
  [§ 69c](law:sk/2004/222#paragraf-69c) umožňuje odberateľovi zaplatiť daň z
  faktúry priamo na účet správcu dane vedený pre dodávateľa (osobitný spôsob
  úhrady dane).
- **Index daňovej spoľahlivosti** (vysoko spoľahlivý / spoľahlivý / menej
  spoľahlivý) určuje daňový úrad podľa
  [§ 53d daňového poriadku](law:sk/2009/563#paragraf-53d) a zoznam sa
  zverejňuje podľa [§ 52 ods. 17](law:sk/2009/563#paragraf-52.odsek-17).
  Nepatrí medzi dôvody podľa § 69 ods. 13; modul ho zobrazuje ako doplňujúcu
  informáciu.

**Česko** — [zákon o DPH, § 106a, § 109, § 109a](law:cz/2004/235):

- § 106a: správca dane rozhodne, že platiteľ, ktorý závažným spôsobom porušil
  svoje povinnosti, je *nespolehlivým plátcem*.
- § 109 ods. 2: má sa za to, že príjemca o nezaplatení dane vedel — a ručí za
  ňu —, okrem iného ak je dodávateľ zverejnený ako nespoľahlivý platiteľ
  (písm. a)) alebo ak sa platí bezhotovostne na **iný účet, ako je účet
  dodávateľa zverejnený správcom dane** (písm. c) bod 2).
- § 98 písm. d): zverejňujú sa účty, ktoré platiteľ určil na zverejnenie.
- § 109a: príjemca môže daň zaplatiť priamo správcovi dane dodávateľa
  (*zvláštní způsob zajištění daně*).

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Dodávateľské faktúry**,
nastavenie **Kontrola spoľahlivosti dodávateľa (CZ/SK)**. Je predvolene
zapnuté pre každú spoločnosť; ak chcete kontrolovať len ručne, vypnite ho pre
danú spoločnosť.

Kontrola beží len v spoločnostiach, ktorých daňovou krajinou je Slovensko
alebo Česko. Nainštalujte modul pre každú krajinu, z ktorej máte dodávateľov;
slovenský potrebuje aj API kľúč (pozri [nižšie](#sk-provider)).

Dodávateľ musí mať údaj, podľa ktorého register vyhľadáva:

| Dodávateľ | Potrebné na kontakte |
|---|---|
| český | krajina Česko a *IČ DPH* (`CZ12345678`) |
| slovenský | krajina Slovensko (alebo *IČ DPH* začínajúce `SK`), *IČ DPH* pre účty a zoznam na zrušenie registrácie, *IČO* pre index spoľahlivosti |

Účet, na ktorý platíte, sa so zoznamom z registra porovnáva ako **IBAN**. Účet
českého dodávateľa môže byť zadaný aj v tuzemskom tvare (`19-2000145399/0800`);
český poskytovateľ ho najprv prevedie na IBAN.

## Kedy sa kontroluje {#checks}

- **Pri zaúčtovaní dodávateľskej faktúry alebo dobropisu** — automaticky, ak
  je nastavenie zapnuté.
- **Pri zaúčtovaní odchádzajúcej úhrady dodávateľovi** — automaticky, voči
  účtu, na ktorý úhrada skutočne ide. Práve od úhrady ručenie závisí a medzi
  faktúrou a úhradou môžu prejsť týždne.
- **Denne** — naplánovaná akcia *Supplier reliability: re-check unpaid bills
  (CZ/SK)* znova overí zaúčtované faktúry, ktoré ešte nie sú uhradené (alebo
  sú uhradené len čiastočne) a naposledy boli overené pred viac ako 7 dňami,
  najviac 200 naraz, od najstarších.
- **Ručne** — tlačidlo **Skontrolovať spoľahlivosť dodávateľa** pod bankovým
  účtom príjemcu na dodávateľskej faktúre a pod bankovým účtom dodávateľa na
  úhrade. Funguje v každom stave dokladu vrátane návrhu, aj keď je
  automatická kontrola vypnutá.
- **Na kontakte** — *Actions → Check tax reliability* v zozname alebo na
  formulári kontaktu zistí len hodnotenie, pre spoločnosť každého označeného
  kontaktu.

Každá kontrola, ktorá hodnotenie získa, ho zapíše aj na kontakt dodávateľa ako
**Daňová spoľahlivosť** s časom kontroly, vedľa jeho *IČ DPH*.

Register, ktorý neodpovie, zaúčtovanie nikdy nezastaví; doklad potom ukáže
*Neoverené / nedostupné*.

## Čo uvidíte {#results}

Na dodávateľskej faktúre (a na úhrade) pri bankovom účte:

| Pole | Význam |
|---|---|
| Kontrola bankového účtu | *Účet na platbu je zverejnený*, *Účet na platbu NIE JE zverejnený*, *Nie je nastavený bankový účet* alebo *Neoverené / nedostupné* |
| Spoľahlivosť dodávateľa | hodnotenie z registra, pozri moduly pre krajiny nižšie |
| Zoznam na zrušenie registrácie (*VAT Deregistration Listing*) | vyplnené, ak je dodávateľ v zozname platiteľov, u ktorých nastali dôvody na zrušenie registrácie (Slovensko) |
| Registrované účty (pri kontrole) | účty, ktoré register v tej chvíli uvádzal (len na faktúre) |
| Spoľahlivosť overená dňa | kedy bol záznam vytvorený |

Na začiatku dokladu sa zobrazí upozornenie a rovnaký text sa zapíše do
chatteru, ak:

- účet, na ktorý platíte, **nie je** medzi zverejnenými účtami — s osobitným
  znením, ak dodávateľ nezverejnil žiadny účet;
- hodnotenie je *Menej spoľahlivý* alebo *Nespoľahlivý*;
- dodávateľ je v zozname na zrušenie registrácie.

Každá nová kontrola záznam na doklade prepíše; staršie upozornenia ostávajú v
chatteri. Polia záznamu sa nedajú upravovať a pri duplikovaní faktúry sa
neprenášajú.

Ako s upozornením naložíte, je na vás: zaplaťte na zverejnený účet, alebo
zaplaťte daň priamo správcovi dane dodávateľa (§ 69c SK / § 109a CZ) a zvyšok
dodávateľovi.

## Český register (ADIS) {#cz-provider}

[module:l10n_cz_payment_reliability](module:l10n_cz_payment_reliability) sa
pýta webovej služby Ministerstva financií ČR *rozhraní CRP DPH* (verejná
časť registra platiteľov DPH) na dodávateľov s krajinou Česko. Nepotrebuje
účet ani kľúč. Jedna požiadavka odpovie na obe otázky:

| Odpoveď ADIS | Spoľahlivosť dodávateľa |
|---|---|
| nespolehlivý plátce = ANO | Nespoľahlivý (upozornenie) |
| nespolehlivý plátce = NE | Spoľahlivý |
| nenájdený (nie je platiteľ) | Nie je platiteľ DPH; bankový účet je *Dodávateľ nie je platiteľ DPH*, bez upozornenia, lebo neplatiteľ účty nezverejňuje a § 109 sa naň nevzťahuje |

Zverejnené účty prichádzajú v tuzemskom tvare (predčíslie–číslo/kód banky);
modul ich, rovnako ako účet zadaný na faktúre v tomto tvare, pred porovnaním
prevedie na IBAN. Účty zverejnené v inom tvare
(zahraničné IBAN) sa porovnávajú tak, ako sú zverejnené. Český register
zoznam na zrušenie registrácie nemá, takže toto pole pri českých
dodávateľoch ostáva prázdne.

## Slovenský register (otvorené dáta FS SR) {#sk-provider}

[module:l10n_sk_payment_reliability](module:l10n_sk_payment_reliability)
používa službu otvorených dát Finančnej správy
(`opendata.financnasprava.sk`), ktorá vyžaduje bezplatný API kľúč. Požiadajte
oň tam a zadajte ho v *Účtovníctvo → Konfigurácia → Nastavenia* pri
nastavení **Kontrola spoľahlivosti dodávateľa (CZ/SK)** do poľa **API kľúč
otvorených dát FS SR**. Kľúč je spoločný pre všetky spoločnosti databázy. Bez
neho je každá kontrola slovenského dodávateľa *Neoverené / nedostupné*.

| Otázka | Dátová sada | Hľadá sa podľa |
|---|---|---|
| zverejnené bankové účty | `ds_dph_iban` (zoznam bankových účtov platiteľov DPH) | IČ DPH |
| spoľahlivosť | `ds_iz_ran` (index daňovej spoľahlivosti) | IČO |
| zoznam na zrušenie registrácie | `ds_dphz` (platitelia, u ktorých nastali dôvody na zrušenie registrácie) | IČ DPH |

| Index daňovej spoľahlivosti | Spoľahlivosť dodávateľa |
|---|---|
| vysoko spoľahlivý | Vysoko spoľahlivý |
| spoľahlivý | Spoľahlivý |
| menej spoľahlivý | Menej spoľahlivý (upozornenie) |
| nie je v indexe | Neznáme / neskontrolované |

Pred hľadaním v zozname na zrušenie registrácie sa modul služby opýta, či sa
v tejto dátovej sade dá hľadať podľa IČ DPH. Ak nie, pole ostane prázdne a
kontrola sa považuje za nedostupnú, nie za čistý výsledok.

## Obmedzenia {#limitations}

- **Len upozorňuje, nikdy neblokuje.** Nič vám nebráni zaúčtovať ani
  zaplatiť na nezverejnený účet.
- **Prázdny slovenský zoznam vedie k upozorneniu.** Ak slovenský zoznam pre
  IČ DPH na kontakte neuvádza žiadny účet, upozornenie povie, že dodávateľ
  žiadny nezverejnil. Pri platiteľovi je to práve prípad ručenia; dátová sada
  však nerozlíši platiteľa bez účtu od subjektu, ktorý platiteľom nie je
  (napríklad osoba registrovaná podľa § 7 alebo § 7a). Pred tým, ako sa na
  upozornenie spoľahnete, overte registráciu dodávateľa. Českého dodávateľa,
  ktorého ADIS nevedie ako plátcu, modul označí *Neoverené / nedostupné*.
- **Tuzemský tvar účtu** rozpozná len pri českých dodávateľoch. Slovenský účet
  zadajte ako IBAN.
- **Deň platby.** Zákon sa pozerá na zoznam v deň zadania platobného
  príkazu. Modul kontroluje pri zaúčtovaní úhrady v Odoo; ak príkaz banke
  odošlete neskôr, skontrolujte znova.
- **Dodávatelia z iných krajín** sa nekontrolujú. Dodávateľ bez krajiny
  (český register) alebo bez údaja, ktorý register potrebuje, skončí stavom
  *Neoverené / nedostupné*, bez upozornenia.
- **Daňová spoľahlivosť** na kontakte je posledné hodnotenie, ktoré niektorá
  kontrola získala; záznamom o tom, čo register uvádzal v danej chvíli, ostáva
  stav na faktúre a úhrade.
- Názov slovenskej dátovej sady pre zoznam na zrušenie registrácie
  (`ds_dphz`) nebol overený voči živej službe; ak je nesprávny, pole jednoducho
  ostane prázdne.
- Kontrola zaznamenáva, čo uvádzal register; nepreukazuje, že dodávateľ daň
  zaplatí, ani že ste o riziku nemohli vedieť inak.
