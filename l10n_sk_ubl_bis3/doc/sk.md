---
title: Slovensko — Peppol BIS Billing 3.0 (eFaktúra)
summary: Vyhotovuje slovenské elektronické faktúry vo formáte Peppol BIS Billing 3.0, identifikuje slovenské subjekty v sieti Peppol podľa DIČ a zapisuje variabilný symbol tam, kde ho hľadá banka platiteľa.
verified: 19.0.3.3.1
---

## Na čo slúži {#purpose}

Odoo vie zapísať faktúru ako súbor Peppol BIS Billing 3.0 (UBL 2.1,
EN 16931), ale bez tohto modulu tento formát slovenským odberateľom neponúkne
a slovenské subjekty v sieti Peppol neidentifikuje správne. Modul tieto
medzery dopĺňa:

- pridá formát **Slovensko (Peppol BIS 3.0)** a nastaví ho ako predvolený pre
  každý slovenský kontakt;
- slovenský subjekt identifikuje v sieti Peppol schémou **0245 s jeho DIČ** —
  nie podľa IČ DPH (schéma 9950), ako to robí Odoo, ani podľa IČO, ktoré Odoo
  pod schému 0245 dosadzuje;
- **odmietne export** faktúry, keď vaša spoločnosť alebo slovenský odberateľ
  nemá vyplnené DIČ, a pomenuje kontakt, ktorý treba opraviť;
- zapíše **variabilný symbol** do identifikátora platby v súbore
  (*PaymentID*, BT-83), podľa ktorého banka platiteľa platbu páruje.
- zapíše **dátum dodania** do súboru ako dátum vzniku daňovej povinnosti
  (*TaxPointDate*, BT-7) a z prijatých faktúr ho číta späť; samotné Odoo
  tento prvok z dátumu dodania faktúry nikdy nevyplní.

Samotný súbor je čistý Peppol BIS Billing 3.0 bez národného rozšírenia.
Modul súbor vytvorí; na jeho **odoslanie** cez Peppol je potrebný prístupový
bod, napríklad služba Peppol od Odoo alebo modul
[module:edi_base_peppol](module:edi_base_peppol) s poskytovateľom ako
[module:edi_epostak_peppol](module:edi_epostak_peppol). Oznamovanie údajov z
faktúr Finančnej správe je úlohou prístupového bodu, nie tohto modulu.

Modul sa nainštaluje sám, keď je nainštalovaná slovenská účtová osnova aj
modul Odoo pre UBL/CII.

## Právny rámec {#legal}

Elektronická fakturácia tuzemských plnení sa na Slovensku stáva povinnou
**1. januára 2027** podľa [§ 85o zákona o DPH](law:sk/2004/222#paragraf-85o)
v znení účinnom od toho dňa (dnes platné úplné znenie obsahuje len tie časti
§ 85o, ktoré už nadobudli účinnosť):

- **Kto a kedy (§ 85o ods. 2).** Platiteľ, ktorý počnúc 1. januárom 2027
  dodá tovar alebo službu s miestom dodania v tuzemsku zdaniteľnej osobe so
  sídlom, miestom podnikania alebo prevádzkarňou v tuzemsku — alebo
  nezdaniteľnej právnickej osobe so sídlom v tuzemsku — alebo prijme platbu
  pred takým dodaním, je povinný vyhotoviť elektronickú faktúru. Neplatí to
  pri plneniach oslobodených od dane podľa § 28 až 43 a 47 a pri
  zjednodušenej faktúre. Vyhotovenie elektronickej faktúry nepodlieha
  súhlasu príjemcu; jej zaslanie inak než doručovacou službou áno.
- **Čo je elektronická faktúra (§ 85o ods. 4).** Doklad s náležitosťami
  podľa § 74 ods. 1, vyhotovený, zaslaný a prijatý vo formáte, ktorý umožňuje
  automatizované spracovanie, a v dátovej štruktúre podľa technickej normy
  pre elektronickú fakturáciu a zoznamu jej syntaxí.
- **Opravy (§ 85o ods. 5).** Doklad, ktorý takú faktúru mení, musí byť tiež
  elektronickou faktúrou, obsahovať poradové číslo pôvodnej faktúry a údaje,
  ktoré sa menia, a byť zaslaný rovnakou cestou.

Či konkrétna faktúra pod povinnosť patrí, je otázka zákona, nie formátu:
modul ponúka formát pre každý slovenský kontakt a výber, čo odoslať,
ponecháva na vás.

## Nastavenie {#setup}

1. **Vyplňte DIČ** vašej spoločnosti a slovenských kontaktov — pole **DIČ**
   z modulu [module:l10n_sk_base](module:l10n_sk_base). Z IČ DPH sa nikdy
   neodvodzuje — modul to kedysi robil a prestal, pretože chybné odvodenie
   vytvorí platne vyzerajúci identifikátor, ktorý patrí niekomu inému.
2. **Skontrolujte adresu Peppol kontaktu.** Karta *Fakturácia* na kontakte,
   skupina *Zákaznícke faktúry*: **Peppol e-adresa (EAS)** má byť *SK Daňové
   identifikačné číslo (DIČ)* (kód 0245) a vedľa neho DIČ. Pole **formát
   e-faktúry** je viditeľné len v režime vývojára a vyplní sa samo.
3. **Bankový účet spoločnosti** má byť IBAN, na ktorý má odberateľ platiť;
   do súboru sa zapíše ako obvykle.
4. **Variabilný symbol.** Ak je nainštalovaný modul
   [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   použije sa jeho variabilný symbol — pozri
   [platobné symboly na faktúrach](module:l10n_cssk_payment_symbols#invoices).

## Identifikátor Peppol: 0245 + DIČ {#participant}

Ako dostane adresu Peppol slovenský kontakt (s krajinou Slovensko alebo s
IČ DPH začínajúcim na SK):

| Kontakt | Adresa Peppol |
|---|---|
| Nový, s DIČ | **0245** : DIČ — aj spoločnosť založená vo formulári spoločnosti s vyplneným DIČ |
| Nový, bez DIČ | to, čo vypočíta Odoo — pri platiteľovi DPH 9950 : IČ DPH — kým sa DIČ nevyplní; export sa medzitým odmieta |
| Už na 0245 | koncový bod nasleduje DIČ, keď ho zmeníte |
| Už na 9950 alebo inej skôr zvolenej schéme | **bez zmeny** — modul neprepíše schému, ktorú mohol niekto zvoliť zámerne |

Posledný riadok je dôležitý pre kontakty, ktoré existovali skôr, než sa im
vyplnilo DIČ: zostanú na 9950 aj po vyplnení DIČ, a keďže DIČ už majú,
export ich nezastaví. Ich presun je zámerný a opakovateľný krok: v
*Kontaktoch* (v zozname alebo vo formulári) označte kontakty a zvoľte
*Actions → Peppol: použiť 0245 + DIČ*. Akcia je dostupná správcom
účtovníctva (*Účtovníctvo / Administrátor*). Presunie každý označený
slovenský kontakt, ktorý má DIČ a ktorého koncový bod je prázdny alebo
presne taký, aký Odoo odvodilo z IČ DPH; ručne zadaný koncový bod a kontakt
bez DIČ nechá tak. Rovnaký presun sa raz spustil sám pri aktualizácii modulu
na verziu 19.0.2.0.0, keď väčšina DIČ ešte nebola vyplnená — spustite ho
preto po doplnení chýbajúcich DIČ (napríklad modulom
[module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk)).
Rovnako sa opraví spoločnosť, ktorá vznikla na schéme 9950 pred verziou
19.0.3.2.0: akciu spustite na jej kontakte.

Pri založení spoločnosti modul rovnaký presun vykoná na kontakte, ktorý pre
ňu Odoo vytvorí, takže spoločnosť uložená s DIČ dostane hneď 0245.
Spoločnosť založená k existujúcemu kontaktu si ponechá jeho schému.

## Čo súbor obsahuje {#export}

- Štandardný obsah Peppol BIS Billing 3.0, ktorý vytvára Odoo: strany,
  IČ DPH, riadky, rozpis DPH, IBAN, prenesenie daňovej povinnosti, kde sa
  uplatní.
- **PaymentID (BT-83)** — variabilný symbol: variabilný symbol faktúry, ak je
  nainštalovaný modul platobných symbolov, inak jej referencia platby, inak
  číslo faktúry; zredukované na číslice, ponechaných posledných 10.
- **TaxPointDate (BT-7)** — dátum dodania z poľa *Dátum dodania* faktúry, na
  faktúrach aj dobropisoch. Prijatá faktúra s týmto prvkom vyplní to isté pole
  na dodávateľskej faktúre.
- PDF faktúry vložené do súboru.
- Názov súboru `INV_2026_00042_ubl_bis3_sk.xml` (číslo faktúry s `/`
  nahradeným).

Pred vytvorením súboru export overí, že **vaša spoločnosť aj odberateľ**, ak
sú slovenskí, majú DIČ. Ak nie, zastaví sa so správou, ktorá pomenuje kontakt
a schému, pod ktorou je práve zverejnený. Kontakt registrovaný pod inou
schémou prejde, ak má DIČ vyplnené.

## Obmedzenia {#limitations}

- Modul vytvára len súbor. Prenos cez Peppol a oznamovanie údajov z faktúr
  Finančnej správe zabezpečuje prístupový bod.
- Kontakty, ktoré boli na 9950 pred vyplnením DIČ, tam zostanú, kým na nich
  niekto nespustí *Peppol: použiť 0245 + DIČ*; neskoršie vyplnenie DIČ ho
  nespustí automaticky.
- Nerozhoduje, ktoré faktúry treba podľa § 85o poslať elektronicky; formát
  ponúka pre každý slovenský kontakt.
- Pri odinštalovaní sa formát z kontaktov odstráni; ich adresy Peppol
  zostanú.
