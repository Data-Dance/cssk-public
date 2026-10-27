---
title: SK lízing a úvery (finančný prenájom)
summary: Slovenské predvolené účty pre finančný prenájom a úvery — 474, 474100, 562 a 022 — pre ten nástroj na úvery, ktorý beží vo vašej edícii.
verified: 19.0.1.0.4
---

## Na čo slúži {#purpose}

Auto alebo stroj obstaraný **finančným prenájmom** (lízingom) je od prvého
dňa majetkom nájomcu: zaradí sa na účet majetku, záväzok z nájmu na účet
474 a každá splátka sa delí na istinu a úrok. Odoo vie viesť splátkový
kalendár a účtovať splátky, ale ktorý program to robí, závisí od edície, a
ani jeden slovenské účty nepozná:

| Edícia | Nástroj | Prepájací modul |
|---|---|---|
| Community | OCA `account_loan` + `account_leasing` | [module:l10n_sk_account_loan_oca](module:l10n_sk_account_loan_oca) — pozri [Community](#community) |
| Enterprise | Odoo `account_loans` | [module:l10n_sk_account_loan_ee](module:l10n_sk_account_loan_ee) — pozri [Enterprise](#enterprise) |

Oba nástroje definujú tie isté modely rozdielne, preto môže byť
**nainštalovaný len jeden**; Odoo kombináciu odmietne.

Tento modul ([module:l10n_sk_account_loan_base](module:l10n_sk_account_loan_base))
obsahuje to, čo je slovenské a nezávisí od nástroja: štyri účty spoločnosti
a obrazovku ich nastavení. Prepájací modul pre váš nástroj sa nainštaluje
sám a tieto účty skopíruje na každý nový úver alebo lízing.

Patrí sem len finančný prenájom. **Operatívny prenájom** nie je úver:
nájomné je nákladom obdobia, v prípade potreby časovo rozlíšeným cez
[module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff).

## Právny rámec {#legal}

- **Účtovanie u nájomcu.** V deň prijatia sa majetok účtuje na príslušný
  účet majetku v ocenení rovnajúcom sa istine u nájomcu so súvzťažným
  zápisom v prospech účtu **474** *Záväzky z nájmu*
  ([§ 30a ods. 7 opatrenia 740/2002](law:sk/2002/740#paragraf-30a.odsek-7));
  v deň splatnosti platieb sa splatný finančný náklad účtuje na ťarchu účtu
  **562** *Úroky* v prospech 474
  ([§ 30a ods. 9](law:sk/2002/740#paragraf-30a.odsek-9)) a ku dňu závierky
  sa zaúčtuje aj úrok pripadajúci na obdobie od poslednej splatnosti
  ([§ 30a ods. 10](law:sk/2002/740#paragraf-30a.odsek-10)).
- **Daň z príjmov.** Finančný prenájom je obstaranie hmotného majetku na
  základe nájomnej zmluvy s dojednaným právom kúpy, ak vlastnícke právo
  prejde bez zbytočného odkladu po skončení nájmu a doba nájmu je najmenej
  **60 % doby odpisovania** podľa § 26 ods. 1 —
  [§ 2 písm. s) zákona o dani z príjmov](law:sk/2003/595#paragraf-2.pismeno-s).
  Nájomca majetok odpisuje počas doby odpisovania príslušnej odpisovej
  skupiny ([§ 26 ods. 8](law:sk/2003/595#paragraf-26.odsek-8); doby v
  [§ 26 ods. 1](law:sk/2003/595#paragraf-26.odsek-1)).
- **DPH.** Odovzdanie tovaru na základe nájomnej zmluvy, podľa ktorej sa za
  normálnych okolností vlastníctvo nadobudne najneskôr pri zaplatení
  poslednej splátky, je **dodaním tovaru**
  ([§ 8 ods. 1 písm. c) zákona o DPH](law:sk/2004/222#paragraf-8.odsek-1.pismeno-c)):
  prenajímateľ uplatní daň raz, z celej ceny, pri odovzdaní; nasledujúce
  splátky už ďalšiu DPH nenesú. Slová „za normálnych okolností“ platia od
  1. 1. 2025 a rozhodujúcou robia ekonomickú podstatu zmluvy, nie jej
  znenie. Prenájom, ktorý takým dodaním nie je, je službou zdaňovanou z
  každej splátky.

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Finančný prenájom (SK)**,
zobrazený len pri spoločnostiach so slovenskou osnovou:

| Nastavenie | Predvolené | Použitie |
|---|---|---|
| Lízing — dlhodobý záväzok | 474000 *Záväzky z nájmu* | časť záväzku splatná po viac ako roku |
| Lízing — časť splatná do jedného roka | 474100 *Lízing (bežná časť)* | časť splatná do roka; voči nej sa účtujú splátky |
| Lízing — úrokový náklad | 562000 *Úroky* | úrok v každej splátke |
| Prenajatý majetok | 022000 *Samostatné hnuteľné veci a súbory hnuteľných vecí* | účet, na ktorý sa prenajatý majetok zaradí (len nástroj Community) |

Účty sa vyplnia pri načítaní slovenskej osnovy a pri spoločnostiach, ktoré
ju už mali, pri inštalácii modulu — len ak sú ešte prázdne, takže voľbu
účtovníka nikdy neprepíšu. Sú predvolené: každý úver má vlastnú kópiu,
ktorú na ňom môžete zmeniť.

## Nástroj Community (OCA) {#community}

[module:l10n_sk_account_loan_oca](module:l10n_sk_account_loan_oca) sa
nainštaluje sám spolu s OCA `account_leasing`. Obrazovky OCA sú v
angličtine.

1. *Účtovníctvo → Účtovníctvo → Loans → Loans*, *Nový*. Zvoľte typ
   **Leasing**, prenajímateľa ako *Lender*, sumu, úrokovú sadzbu, počet a
   dĺžku období a dátum začiatku.
2. Pri slovenskej spoločnosti sú účty už vyplnené: *Long term account*
   474000, *Short term account* 474100, *Interests account* 562000 a na
   záložke *Leasing* účet prenajatého majetku 022000. Ak na formulári
   zmeníte spoločnosť, účty sa namiesto vymazania doplnia z novej
   spoločnosti. Nastavte *Loan product* a *Interest product*, ktoré sa
   použijú na faktúrach za splátky.
3. **Compute items** zostaví splátkový kalendár. **Post** zaúčtuje
   majetok: na ťarchu účtu prenajatého majetku, v prospech 474100 istinu
   splatnú do roka a v prospech 474000 zvyšok.
4. Generovanie zápisov vytvorí ku každej splátke prijatú faktúru od
   prenajímateľa — istinu na 474100, úrok na 562000 — a presun ďalšej časti
   záväzku zo 474000 na 474100.

**DPH na splátkach.** Pri slovenskej spoločnosti má karta *Leasing*
skupinu **Slovenský daňový režim** s poľami:

- *Režim DPH* — pri lízingovej zmluve povinné:
  - *Dodanie tovaru*: modul odstráni DPH zo všetkých riadkov faktúr za
    splátky, pretože pri prenájme, ktorý je dodaním tovaru, sa DPH uplatnila
    pri odovzdaní (pozri [Právny rámec](#legal)). Faktúru prenajímateľa za
    odovzdanie s celou DPH zaúčtujte samostatne ako bežnú prijatú faktúru.
  - *Dodanie služby*: faktúry za splátky si ponechajú dane produktov
    *Loan product* a *Interest product*.
- *Odpisová skupina predmetu* a doba nájmu v mesiacoch; ak je doba nájmu
  kratšia ako 60 % doby odpisovania skupiny, upozornenie oznámi, že nejde o
  finančný prenájom podľa § 2 písm. s). Minimum sa zaokrúhľuje nahor na celé
  mesiace: 60 % zo šiestich rokov skupiny 2 je 43,2 mesiaca, takže lízing v
  skupine 2 musí trvať aspoň 44 mesiacov. Ponúkajú sa skupiny 0 (dva roky)
  až 6.

Nový lízing začína bez režimu DPH a kým ho nikto nezvolí, faktúry za splátky
si dane ponechajú: odstrániť DPH je rozhodnutie, ktoré treba urobiť výslovne.

**Lízingy vytvorené pred verziou 19.0.1.0.3** mali predvolene vyplnené
*Dodanie tovaru*, pretože pole nebolo na formulári. Každý z nich otvorte a
režim potvrďte alebo zmeňte; zmena platí pre faktúry za splátky vytvorené
potom.

## Nástroj Enterprise {#enterprise}

[module:l10n_sk_account_loan_ee](module:l10n_sk_account_loan_ee) sa
nainštaluje sám spolu s modulom Odoo Enterprise `account_loans`.

*Účtovníctvo → Účtovníctvo → Majetok a záväzky → Úvery*, *Nový*. Pri
slovenskej spoločnosti sa nový úver otvorí s účtami *Dlhodobý účet* 474000,
*Krátkodobý účet* 474100 a *Účet nákladov* 562000. Enterprise sám kopíruje
účty z predchádzajúceho úveru spoločnosti, ak nejaký existuje; modul dopĺňa
len to, čo zostalo prázdne, takže po prvom úvere majú prednosť jeho účty.

Enterprise účet prenajatého majetku nepoužíva: úver prepája s majetkom cez
*Asset Group* a *Linked Assets*. Ani zaobchádzanie s DPH z modulu pre
Community tu neexistuje; úvery Enterprise účtujú účtovné zápisy, nie
faktúry za splátky.

## Obmedzenia {#limitations}

- Pri nástroji Enterprise sú slovenské polia lízingu (*Režim DPH*,
  *Odpisová skupina predmetu*, upozornenie na 60 %) na zázname úveru, no
  žiadny formulár ich nezobrazuje. Nič tam nemenia, keďže Enterprise faktúry
  za splátky nevytvára.
- Pri *Dodanie tovaru* sa DPH odstráni zo všetkých riadkov faktúr za
  splátky vrátane riadku úroku.
- Faktúru za odovzdanie s DPH, odpisovanie prenajatého majetku ani časové
  rozlíšenie úroku ku dňu závierky (§ 30a ods. 10) moduly neriešia; nástroj
  Community účtuje priamo na účet majetku a nevytvorí kartu majetku na
  odpisovanie.
- Či ide o finančný alebo operatívny prenájom a ako sa záväzok delí na
  dlhodobú a krátkodobú časť, rozhoduje váš účtovník; predvolené účty si s
  ním prejdite.
