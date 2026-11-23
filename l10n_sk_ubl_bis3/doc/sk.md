---
title: Slovensko — Peppol BIS Billing 3.0 (eFaktúra)
summary: Vyhotovuje slovenské elektronické faktúry vo formáte Peppol BIS Billing 3.0, identifikuje slovenské subjekty v sieti Peppol podľa DIČ a zapisuje variabilný symbol tam, kde ho hľadá banka platiteľa.
verified: 19.0.3.8.0
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

Samotný súbor je čistý Peppol BIS Billing 3.0 bez národného rozšírenia
a bez slovenského validačného pravidla navyše. Čo slovenské právo žiada nad
rámec štandardu, je v časti [Čo žiada transpozícia](#transposition).
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
| Na 9950, keď sa mu prvýkrát vyplní DIČ | **presunie sa na 0245 : DIČ** pri uložení DIČ, ak jeho koncový bod nebol zadaný ručne |
| Už na 0245 | koncový bod nasleduje DIČ, keď ho zmeníte |
| Na 9950 alebo inej schéme zvolenej, keď už DIČ bolo vyplnené | **bez zmeny** — modul neprepíše schému, ktorú mohol niekto zvoliť zámerne |

Kým kontakt nemá DIČ, schéma 0245 nie je možná, takže jeho 9950 je to, na čo
Odoo prešlo, nie voľba: vyplnenie DIČ — ručne alebo z registra — ho presunie.
DIČ zapísané mimo formulára (import priamo do databázy, staršia verzia modulu)
ho nepresunie a pre také kontakty je presun zámerný a opakovateľný krok: v
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
  faktúrach aj dobropisoch, ak sa líši od dátumu vyhotovenia; súbor bez neho
  znamená, že sú zhodné. Prijatá faktúra s týmto prvkom vyplní to isté pole
  na dodávateľskej faktúre.
- **CompanyLegalForm (BT-33)** — právna forma dodávateľa a zápis v registri
  (§ 3a Obchodného zákonníka), ak je nainštalovaný modul
  [module:l10n_sk_trade_registry](module:l10n_sk_trade_registry) a má ich pre
  vašu spoločnosť; inak sa prvok vynechá.
- **Company ID (BT-30 / BT-47)** — IČO slovenského dodávateľa alebo
  odberateľa z poľa *IČO* na kontakte, v schéme `0158`. IČ DPH sa uvádza len
  ako identifikátor na účely DPH. Slovenský kontakt bez IČO nemá v súbore
  žiadny identifikátor zákonnej registrácie.
- **BillingReference (BT-25 / BT-26)** — na dobropise alebo ťarchopise
  vytvorenom z faktúry číslo a dátum vystavenia tejto faktúry. Na ručne
  zadanom dobropise čísla zapísané v poli *Čísla pôvodných faktúr*, každé s
  dátumom, ak ide o vašu faktúru pre toho istého odberateľa.
- **Note (BT-22)** — obchodné podmienky faktúry. Na dobropise alebo
  ťarchopise je pred nimi dôvod zadaný v sprievodcovi, ako „Dôvod opravy: …“
  v jazyku odberateľa.
- **InvoiceTypeCode** — 380 pre faktúru, 383 pre ťarchopis; dobropis je
  samostatný typ dokladu s kódom 381.
- **OrderReference (BT-13)** — *Referencia zákazníka* z faktúry. Na dobropise
  alebo ťarchopise, ktorého referencia iba cituje pôvodnú faktúru, sa použije
  referencia pôvodnej faktúry, inak číslo dokladu.
- PDF faktúry vložené do súboru.
- Názov súboru `INV_2026_00042_ubl_bis3_sk.xml` (číslo faktúry s `/`
  nahradeným).

Pred vytvorením súboru export overí, že **vaša spoločnosť aj odberateľ**, ak
sú slovenskí, majú DIČ. Ak nie, zastaví sa so správou, ktorá pomenuje kontakt
a schému, pod ktorou je práve zverejnený. Kontakt registrovaný pod inou
schémou prejde, ak má DIČ vyplnené.

Tá istá kontrola zastaví export, keď slovenský dodávateľ alebo odberateľ nemá
ulicu, mesto alebo PSČ, a keď má pole *IČO* vyplnené hodnotou, ktorá nie je
IČO (najviac 8 číslic). Hlásenie uvedie kontakt a čo chýba.

Takéto kontakty nájdete skôr, než sa faktúra zastaví: otvorte **Kontakty** a
použite filter **E-faktúra by bola odmietnutá**. Zobrazí slovenské firmy bez
DIČ, s neúplnou adresou alebo s poľom *IČO*, ktoré nie je IČO.

Na dve veci modul iba upozorní žltým pruhom na faktúre a nikdy ju nezastaví:

- **Chýba bankový účet** na zatiaľ nezaplatenej odberateľskej faktúre: súbor
  potom neuvádza, kam zaplatiť. Nastavte *Banka príjemcu*, ak sa faktúra
  neplatí v hotovosti alebo kartou.
- **Chýba pôvodná faktúra** na ručne zadanom dobropise: vyplňte *Čísla
  pôvodných faktúr*, oddelené čiarkou. Pole sa zobrazuje na odberateľskom
  dobropise, ktorý nevznikol z faktúry.

## Čo žiada transpozícia {#transposition}

Finančná správa zverejňuje *Transpozície štandardu Peppol BIS v podmienkach
Slovenskej legislatívy*, zošit, ktorý pri každom termíne štandardu uvádza,
či ho slovenské právo vyžaduje, podmienene vyžaduje alebo nevyžaduje.
Vlastné validačné pravidlo nepridáva. Modul bol porovnaný s verziou
**1.13 (29. októbra 2026)**; súbor, jeho kontrolný súčet a postup kontroly
novšej verzie sú v súbore modulu `data/TRANSPOSITION_VERSION`.

| Termín | Čo hovorí transpozícia | Čo robí modul |
|---|---|---|
| BT-34, BT-49 elektronická adresa | vyžaduje sa, schéma 0245 = DIČ | 0245 + DIČ; bez DIČ sa export odmietne |
| BT-35/37/38, BT-50/52/53 adresa | vyžaduje sa (§ 74), hoci je v štandarde nepovinná | export sa odmietne, ak chýba ulica, mesto alebo PSČ |
| BT-30, BT-47 zákonná registrácia | vyžaduje sa, ak bolo IČO pridelené | IČO v schéme 0158 |
| BT-31, BT-48 identifikátor pre DPH | vyžaduje sa, ak bolo IČ DPH pridelené | IČ DPH z kontaktu |
| BT-7 dátum dodania | len ak sa líši od dátumu vyhotovenia a je známy | zapíše sa len vtedy |
| BT-8 kód dátumu vzniku daňovej povinnosti | nepoužívať | nikdy sa nezapíše |
| BT-33 právna forma a zápis dodávateľa v registri | podmienene vyžadované (§ 3a Obchodného zákonníka) | z modulu obchodného registra, ak je nainštalovaný |
| BT-25 predchádzajúca faktúra | nevyžaduje sa do 1. júla 2030 | zapíše sa na dobropise a ťarchopise vytvorenom z faktúry a z čísel zapísaných na ručne zadanom dobropise; ak nie je ani jedno, upozornenie |
| BT-83 informácie o platbe | variabilný symbol, najviac 10 číslic | variabilný symbol, posledných 10 číslic |
| BT-84 platobný účet | číslo účtu dodávateľa je povinné | bankový účet faktúry, ak ho má; ak ho nemá, **upozornenie** na faktúre, export sa neodmietne |
| BT-120 text dôvodu oslobodenia | vyžaduje sa pri oslobodenom plnení | z dane, ako ho vypĺňa Odoo; **nekontroluje sa** |
| BT-22 poznámka k faktúre | nesie zákonné formulácie bez vlastného poľa (napríklad uplatňovanie DPH na základe prijatia platby, § 68d) | obchodné podmienky faktúry a dôvod na dobropise alebo ťarchopise; zákonné formulácie sa automaticky **nepridávajú** |

## Obmedzenia {#limitations}

- Oslobodená daň bez textu dôvodu a chýbajúca zákonná formulácia sa
  nekontrolujú: faktúra odíde tak, ako je. Na faktúru bez bankového účtu a
  na dobropis bez pôvodnej faktúry modul upozorní, ale nezastaví ich.
- PSČ sa posiela tak, ako je zapísané, ceny s desatinnými miestami, ktoré
  drží Odoo, a import nerozlišuje ťarchopis (383) od faktúry.

- Modul vytvára len súbor. Prenos cez Peppol a oznamovanie údajov z faktúr
  Finančnej správe zabezpečuje prístupový bod.
- Nerozhoduje, ktoré faktúry treba podľa § 85o poslať elektronicky; formát
  ponúka pre každý slovenský kontakt.
- Pri odinštalovaní sa formát z kontaktov odstráni; ich adresy Peppol
  zostanú.
