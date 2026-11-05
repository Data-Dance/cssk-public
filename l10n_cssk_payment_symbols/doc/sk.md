---
title: Platobné symboly CZ/SK (VS/KS/SS)
summary: Variabilný, konštantný a špecifický symbol na faktúrach, platbách a bankových výpisoch a párovanie prijatých platieb podľa nich.
verified: 19.0.1.5.1
---

## Na čo slúži {#purpose}

Platiteľ v Česku a na Slovensku neoznačuje platbu voľným textom, ale číselnými
**platobnými symbolmi**:

| Symbol | Názov | Dĺžka | Bežné použitie |
|---|---|---|---|
| VS | variabilný symbol | najviac 10 číslic | číslo faktúry — to, čo má odberateľ uviesť pri platbe |
| KS | konštantný symbol | najviac 4 číslice | druh platby, napr. `0008` tovar, `0308` služby |
| SS | špecifický symbol | najviac 10 číslic | doplnkový identifikátor, ktorý vyžadujú niektorí príjemcovia (poisťovne, leasing) |

Samotné Odoo pozná len voľný text *Referencia platby*. Tento modul dáva trom
symbolom vlastné kontrolované polia, vyplní ich za vás, prenesie ich do
platobných QR kódov, platieb a bankových súborov, načíta ich späť z bankových
výpisov a — s jedným z doplnkových modulov — páruje prijaté platby s
faktúrami podľa variabilného symbolu.

Závisí len od modulu `account`, takže funguje v edícii Community aj Enterprise
a nepotrebuje zvyšok česko-slovenskej lokalizácie.

## Právny rámec {#legal}

Symboly sú v oboch krajinách **bankovou konvenciou**, nie zákonnou povinnosťou
pri bežných obchodných platbách:

- **Slovensko.** Pri SEPA úhrade sa symboly prenášajú v referencii platiteľa
  v tvare `/VS…/SS…/KS…`. Od 18. marca 2024 banky na základe odporúčania
  Národnej banky Slovenska čoraz častejšie pridávajú na začiatok otáznik:
  `?/VS…/SS…/KS…` (VS a SS najviac 10 číslic, KS 4). Modul číta obe podoby.
- **Česko.** Symboly kedysi vymedzovala vyhláška ČNB č. 62/2004 Sb. Tú zrušil
  [§ 7 vyhlášky č. 169/2011 Sb.](law:cz/2011/169), ktorá ich už nevymedzuje.
  Ostali ako konvencia bánk a súčasť platobných pokynov príjemcov, ktorí ich
  vyžadujú, napríklad daňovej správy či sociálneho zabezpečenia.

Keďže variabilný symbol je jedinečný len **u jedného vystaviteľa** — dvaja
dodávatelia môžu mať faktúru s číslom 2026001 — párovanie opísané nižšie sa
nikdy nespolieha len na symbol, ak vie, kto platil.

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Czech / Slovak Payment
Symbols** (popisy nastavení sú v tejto verzii po anglicky):

| Nastavenie | Čo robí |
|---|---|
| Variabilný symbol dobropisu (*Credit note variable symbol*) | Či dobropis odberateľovi nesie **vlastné číslo** (predvolené), alebo **variabilný symbol faktúry, ktorú opravuje**. Druhú možnosť zvoľte, ak odberatelia započítavajú dobropisy voči pôvodnej faktúre. |
| Predvolený konštantný symbol (*Default constant symbol*) | Predvyplní sa na každej faktúre a dobropise odberateľovi, napr. `0308`, ak predávate služby. Prázdne = žiadny. |
| Referencia platby = variabilný symbol (*Payment reference = variable symbol*) | Pri zaúčtovaní dokladu odberateľovi sa jeho *Referencia platby* nastaví na variabilný symbol. Vlastné QR kódy Odoo, identifikátor platby v e-faktúre (UBL) aj štandardné párovanie výpisov potom nesú VS bez ďalšieho nastavovania. Už zaúčtované doklady sa nemenia. |

## Na faktúrach, dobropisoch a dodávateľských faktúrach {#invoices}

Tri polia — *Variable Symbol*, *Constant Symbol*, *Specific Symbol* — sú hneď
za poľom *Referencia platby*: na dodávateľskej faktúre v hlavnej časti
formulára, na faktúre a dobropise odberateľovi na karte *Ďalšie info*.

- **Faktúra odberateľovi.** Variabilný symbol sa vyplní z číslic čísla
  dokladu, ponechá sa posledných 10: z `FV/2026/00042` vznikne `202600042`.
  Konštantný symbol sa prevezme z predvolenej hodnoty spoločnosti.
- **Dobropis odberateľovi.** Vlastné číslo alebo symbol pôvodnej faktúry,
  podľa nastavenia vyššie.
- **Dodávateľská faktúra.** Variabilný symbol sa vezme z číslic poľa
  *Referencia faktúry* — zvyčajne číslo faktúry dodávateľa, ktoré je zároveň
  VS, ktorý očakáva. Ak dodávateľ žiada iný VS, prepíšte ho.

Všetky polia sa dajú upraviť. Hodnotu, ktorá nie je len z číslic alebo je
dlhšia ako 10 / 4 / 10 číslic, Odoo pri uložení odmietne.

Pokladničné doklady odberateľovi (*out_receipt*) symboly nezobrazujú, lebo
Odoo pri nich nezobrazuje ani *Referenciu platby*.

## Platobné QR kódy {#qr}

Keď faktúra tlačí platobný QR kód, jej symboly sa odovzdajú generátoru QR
kódu, takže kód, ktorý odberateľ naskenuje, nesie VS, KS a SS ako samostatné
údaje. Slovenské a české formáty QR kódov poskytujú moduly
[module:account_qr_code_pay_by_square_sk](module:account_qr_code_pay_by_square_sk)
(PAY by square),
[module:account_qr_code_payme_sk](module:account_qr_code_payme_sk)
(payme.sk) a
[module:account_qr_code_qr_platba_cz](module:account_qr_code_qr_platba_cz)
(QR Platba).

## Platby {#payments}

Tlačidlo *Platba* (sprievodca registráciou platby) prenesie symboly na
vytvorenú platbu, ak majú všetky uhrádzané doklady rovnakú hodnotu. Hromadná
platba za faktúry s rôznymi variabilnými symbolmi nedostane žiadny — banka
príjemcu by ju aj tak nevedela priradiť jednej faktúre. Symboly sú na
formulári platby za poľom *Poznámka* a dajú sa upraviť.

## Bankové výpisy {#bank-statements}

Keď vznikne riadok výpisu — z bankového konektora alebo importom súboru —
symboly sa vyplnia v tomto poradí z:

1. hodnôt, ktoré konektor odovzdá priamo;
2. podrobností transakcie od konektora pod obvyklými názvami kľúčov
   (`variable_symbol`, `variableSymbol`, `vs`, `variable_code` a obdobne pre
   KS a SS);
3. značiek v popise, referencii a poznámke: `VS:123`, `VS 123`, `/VS123`,
   `/VS/123`, `?/VS123/SS/KS`. Súbory CAMT často nesú symboly len v
   referencii, preto sa číta aj tá.

Nulový symbol (`SS0`) sa považuje za žiadny. Variabilný symbol sa navyše
zapíše na začiatok popisu (`123 - pôvodný popis`, nikdy nie dvakrát), aby ho
videlo aj štandardné párovanie Odoo. Riadky, ktoré existovali pred
nainštalovaním modulu, sa spätne nečítajú.

## Párovanie prijatých platieb podľa variabilného symbolu {#bank-matching}

Jeden z dvoch doplnkových modulov pridá do automatického párovania výpisov
presné porovnanie variabilného symbolu. Oba sa nainštalujú samy, keď je
prítomný ich párovací nástroj:

- [module:l10n_cssk_payment_symbols_ee](module:l10n_cssk_payment_symbols_ee)
  — pre párovanie výpisov v Odoo Enterprise;
- [module:l10n_cssk_payment_symbols_oca](module:l10n_cssk_payment_symbols_oca)
  — pre párovací nástroj OCA (`account_reconcile_oca`) v edícii Community.

Pravidlo majú spoločné. Riadok výpisu s variabilným symbolom sa porovná s
otvorenými zaúčtovanými dokladmi tej istej spoločnosti s rovnakým symbolom,
pričom sa **ignorujú úvodné nuly** (`0042` = `42`):

- Ak riadok výpisu už pozná platiteľa (podľa čísla účtu), berú sa do úvahy len
  doklady tohto partnera.
- Ak symbol nesie práve jeden doklad, spáruje sa s ním.
- Ak ho nesie viac dokladov, vezme sa ten, ktorého otvorená suma sa rovná
  platbe — no len ak taký je práve jeden, a len v mene spoločnosti. Dva
  doklady s rovnakým symbolom aj sumou (dva predajné denníky môžu oba vystaviť
  …00001) ostanú na vás.
- Inak sa nespáruje nič a riadok ostane na vás. Modul nikdy nehádá.

Zálohové faktúry (proformy) sa podľa variabilného symbolu párujú v tom istom
kroku, ak je nainštalovaný modul
[module:sale_order_advance_invoice_payment_match](module:sale_order_advance_invoice_payment_match#matching).

Rozdiely medzi nimi:

| | Enterprise | OCA |
|---|---|---|
| Kedy beží | pred vlastným párovaním Odoo, ktoré ignoruje reťazce do 5 znakov, a preto krátky VS nespáruje nikdy | pred vlastným párovaním faktúr v OCA |
| Platba pokryje faktúru | spárované | spárované |
| Čiastočná úhrada | spárované, zvyšok faktúry ostane otvorený | spárované, zvyšok faktúry ostane otvorený |
| Preplatok | faktúra sa spáruje, prebytok ide do vlastného párovania Odoo a na vás | navrhne sa v nástroji, automaticky sa nikdy nespáruje |
| Cudzia mena | len párovanie s jedným dokladom | ponechá sa na OCA a na vás |
| Viac riadkov v jednom importe | — | riadok nájde len to, čo predchádzajúce riadky toho istého importu nechali otvorené: druhá úplná úhrada tej istej faktúry ostane na vás, splátky ju uhradia spolu a preplatok ponechaný na vás neuberie nič ďalšiemu riadku |
| Navyše | stĺpec VS a vyhľadávanie podľa VS v zozname bankových transakcií (KS, SS voliteľne) | — |

## Platobné príkazy {#payment-orders}

Ak sú nainštalované platobné príkazy OCA (`account_payment_order`), modul
[module:l10n_cssk_payment_symbols_payment_order](module:l10n_cssk_payment_symbols_payment_order)
prenesie VS, KS a SS každého dokladu na riadky platobného príkazu, ktoré z neho
vzniknú. Exportéry tuzemských bankových súborov —
[module:account_abo](module:account_abo) (český formát ABO) a
[module:account_multicash](module:account_multicash) — ich zapíšu do súboru
ako štruktúrované symboly. Vlastnú obrazovku nemá.

## SEPA úhrady / ISO 20022 {#iso20022}

Symboly do súboru SEPA úhrad (pain.001) zapisujú dva moduly, pre každý zo
spôsobov, ktorými ho Odoo vytvára:

- [module:l10n_cssk_payment_symbols_iso20022](module:l10n_cssk_payment_symbols_iso20022)
  — export ISO 20022 v Odoo Enterprise (dávkové platby); voľba **CZ/SK
  Symbols in pain.001** na bankovom denníku;
- [module:l10n_cssk_payment_symbols_sepa_oca](module:l10n_cssk_payment_symbols_sepa_oca)
  — platobný príkaz OCA (`account_banking_sepa_credit_transfer`), ktorý
  používa Odoo Community; voľba **Platobné symboly CZ/SK v SEPA úhradách** na
  bankovom denníku.

Oba ponúkajú tie isté voľby a zapisujú ten istý text:

| Voľba | Čo sa zapíše do súboru |
|---|---|
| *EndToEndId (/VS…/SS…/KS…)* | identifikátor end-to-end `/VS2026114455/SS77/KS0308`, štruktúra, ktorú čítajú slovenské banky (napríklad formát SEPA pre klientov VÚB). Predvolené pre slovenské spoločnosti v module OCA. |
| *Správa pre príjemcu (/VS/…/KS/…/SS/…)* | `/VS/…/KS/…/SS/…` pripojené k správe pre príjemcu; `PLATBA/VS/…`, ak žiadna nebola. Štruktúrovaná referencia veriteľa (RF) ostane nezmenená. Predvolené pre české spoločnosti v module OCA a v Enterprise. |
| *Symboly neexportovať* | súbor tak, ako ho zapíše Odoo alebo OCA. Predvolené pre ostatné spoločnosti. |

Pri exporte symbolov uhradí modul OCA faktúry s rôznymi symbolmi samostatnými
prevodmi: jeden prevod nesie jednu sadu symbolov a na spojenom prevode by
dodávateľ nespároval ani jednu faktúru. Dva prevody s rovnakými symbolmi majú
rovnaký identifikátor end-to-end, ako to vyplýva z formátu bánk.

**Pred spoľahnutím sa pošlite jednu skúšobnú platbu.** Banky sa líšia v tom,
čo spätne rozpoznajú ako symboly; pozrite sa, ako sa platba zobrazí na výpise
príjemcu.

## Obmedzenia {#limitations}

- Variabilný symbol sa odvodzuje z čísla dokladu. Číselný rad s predponou roka
  dá symboly ako `202600042`; ak sú odberatelia zvyknutí na iný tvar, upravte
  číselný rad alebo symbol.
- Automatické párovanie je presné a opatrné: žiadne približné párovanie,
  žiadne párovanie viacerých dokladov v cudzej mene, nič naprieč
  spoločnosťami.
- Symboly sa z riadkov výpisu čítajú pri ich vzniku, nie neskôr.
