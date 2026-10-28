---
title: Fio banka — platobné príkazy
summary: Zostaví platobné príkazy Fio XML z platobného príkazu OCA alebo z hromadnej platby Enterprise a odošle ich cez API do Fio banky na autorizáciu v internetbankingu.
verified: 19.0.1.4.0
---

## Na čo slúži {#purpose}

Namiesto sťahovania platobného súboru a jeho nahrávania do internetbankingu
odošlete dávku platieb z Odoo do Fio banky jedným tlačidlom. Fio ju uloží ako
**neautorizovanú dávku**; niekto s podpisovým právom ju potom potvrdí v
internetbankingu Fio (SMS alebo podpisom Fio). **Odoo samo žiadne peniaze
nepošle.**

Súbor je vo vlastnom XML formáte Fio (`importIB.xsd`), jedinom formáte pre
Fio, ktorý nesie variabilný, konštantný a špecifický symbol ako samostatné
polia — pain.001 je len pre EUR a ABO len pre tuzemské platby v CZK. Modul
pracuje s **platobným príkazom** OCA (`account_payment_order`); v edícii
Enterprise robí to isté s **hromadnou platbou** modul
[module:account_payment_fio_batch](module:account_payment_fio_batch) — pozri
[nižšie](#batch).

Potrebuje pripojenie podľa modulu [module:account_fio](module:account_fio#setup)
s **tokenom na zadávanie** pri denníku.

## Tri druhy príkazov {#kinds}

Každý riadok platobného príkazu sa automaticky stane jedným z troch príkazov
Fio:

| Účet príjemcu | Príkaz Fio | Poznámky |
|---|---|---|
| český: IBAN `CZ` alebo `[predčíslie-]číslo/kód banky` | tuzemská platba | ľubovoľná mena, ktorú Fio povoľuje medzi vlastnými účtami; VS, KS, SS, správa pre príjemcu |
| EUR na IBAN v krajine SEPA (vrátane Slovenska) | Europlatba (SEPA) | VS, KS, SS; vyžaduje sa meno príjemcu |
| čokoľvek iné | zahraničná platba | vyžaduje sa BIC, meno, ulica, mesto a krajina príjemcu, referencia platby a *platobný titul* |

Pri platobnom príkaze sa na každom riadku nastaví **Priority** (*Urgent*
odošle prioritnú platbu) a **Charge Bearer** (pri zahraničných platbách);
predvolená je štandardná platba a delené poplatky.

Príkazy sa zapíšu v poradí tuzemské, Europlatby, zahraničné, ako to Fio
vyžaduje. Súbor má názov `FIO-<kód denníka>-<dátum a čas>.xml`.

## Nastavenie {#setup}

1. Bankový denník: jeho bankový účet je účet vo Fio, z ktorého peniaze
   odchádzajú — IBAN `SK` alebo `CZ`, prípadne `číslo/8330` (Fio SK) alebo
   `číslo/2010` (Fio CZ). Potrebuje **Token Fio na zadávanie** (pozri
   [module:account_fio](module:account_fio#tokens)).
2. Spôsob platby (*Účtovníctvo → Konfigurácia → Účtovníctvo → Payment Modes*)
   s platobnou metódou **Fio XML (Fio banka API)** a týmto denníkom.
3. Partneri: bankový účet pri každom, komu platíte; pri zahraničných platbách
   aj adresu, BIC jeho banky a **Platobný titul** pri partnerovi (karta
   *Predaj a nákup*), aby sa vypĺňal sám.
4. Odporúčame [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   aby sa VS/KS/SS faktúr dostali na riadky platobného príkazu samy (pozri
   [module:account_abo](module:account_abo#setup)).

## Platenie {#usage}

Popisy platobných príkazov OCA sú v tejto verzii po anglicky.

1. *Účtovníctvo → Dodávatelia → Payment Orders*, **Nové**, zvoľte spôsob
   platby Fio, **Create Payment Lines from Journal Items**.
2. Skontrolujte riadky: **Variabilný symbol**, **Konštantný symbol**,
   **Špecifický symbol** a **Platobný titul** sú vedľa poľa *Communication*.
   Prázdny symbol sa vezme zo značky `VS:` / `KS:` / `SS:` v poli
   *Communication*.
3. **Confirm Payments**. Tu sa všetko skontroluje (pozri nižšie).
4. **Generate Payment File** a potom **Odoslať do Fio**.
5. Dávku autorizujte v internetbankingu Fio.

Keď Fio dávku prijme, príkaz zobrazí *Sent to Fio as batch …* s číslom dávky
Fio a sám prejde do stavu nahratého súboru — tlačidlo *File Successfully
Uploaded* netreba. Odpoveď Fio vrátane upozornení k jednotlivým príkazom sa
zapíše do chatteru príkazu.

### Čo sa kontroluje {#checks}

Pri **Confirm Payments** sa skontroluje celý príkaz a **všetky** problémy sa
vypíšu v jednom hlásení (*This payment order cannot be sent to Fio yet*):

- suma nie je kladná alebo chýba mena, dátum či účet príjemcu;
- tuzemská platba nemá kód banky;
- Europlatba alebo zahraničná platba nemá meno príjemcu;
- zahraničnej platbe chýba BIC, ulica, mesto alebo krajina príjemcu,
  referencia platby (pole *Communication*) alebo platný *platobný titul*;
- Europlatba nad 50 000 EUR z účtu vedeného **slovenskou** pobočkou Fio nemá
  platný *platobný titul*;
- účet nie je IBAN ani tuzemské `číslo/kód banky`.

*Platobný titul* je trojmiestny kód dôvodu platby z číselníka Českej národnej
banky. Na riadku platobného príkazu sa predvyplní z partnera.

## Odoslanie do Fio {#send}

Tlačidlo **Odoslať do Fio** sa zobrazí na každom platobnom príkaze, ktorý má
vygenerovaný súbor a ešte nebol odoslaný. Druh súboru rozpozná zo samotného
súboru, takže odošle aj:

- súbor ABO z modulu [module:account_abo](module:account_abo),
- súbor SEPA pain.001 (a pain.008) z modulov SEPA od OCA,

pokiaľ je denník účtom vo Fio s tokenom na zadávanie. Súbory nad 2 MB Fio
odmietne; vtedy príkaz rozdeľte.

**Ak sa odpoveď stratí.** Keď súbor z Odoo odišiel, ale odpoveď neprišla,
nikto nevie, či Fio dávku má. Príkaz potom prejde do stavu **Neznáme — overte
v banke** a zobrazí červené upozornenie; opätovné odoslanie je zablokované,
lebo druhá dávka by pri autorizácii oboch zaplatila všetko dvakrát. Pozrite sa
v internetbankingu Fio, či tam je neautorizovaná dávka, a zapíšte, čo ste
zistili:

- **V banke JE** — príkaz sa označí ako odoslaný a znova sa odoslať nedá;
- **V banke NIE JE** — odoslanie sa znova povolí.

Dávka, ktorú Fio **odmietne**, ostane *Neodoslané*; dôvody sa zobrazia na
obrazovke aj v chatteri a po oprave ju môžete odoslať znova.

## Hromadné platby Enterprise {#batch}

Modul [module:account_payment_fio_batch](module:account_payment_fio_batch)
zostaví to isté Fio XML z **hromadnej platby** Enterprise a odošle ho tým istým
tlačidlom s tou istou poistkou stavu *Neznáme*.

- Pri inštalácii sa odchádzajúca platobná metóda **Fio XML (Fio banka API)**
  pridá do bankových denníkov, ktorých vlastný účet je vo Fio (kód banky 2010
  alebo 8330, alebo BIC Fio), a do takých denníkov založených neskôr alebo
  denníkov, ktorým sa účet vo Fio doplní neskôr. Denníky iných bánk ju
  nedostanú.
- Formulár platby dodávateľovi dostane pole **Platobný titul** predvyplnené
  z partnera.
- Zaregistrujte platby s touto metódou, zoskupte ich do hromadnej platby
  (*Účtovníctvo → Dodávatelia → Hromadné platby*) a stlačte **Potvrdiť**:
  hromadná platba pred zapísaním súboru vypíše všetky platby, ktoré sa nedajú
  odoslať, zoskupené podľa problému. Potom stlačte **Odoslať do Fio**. Odpoveď
  banky je na karte *Fio* hromadnej platby.
- Všetky platby hromadnej platby sa vykonajú k **dátumu hromadnej platby**,
  lebo v internetbankingu sa dávka autorizuje ako celok.
- S modulom ISO 20022 od Odoo sa platba označená ako urgentná odošle ako
  prioritná.

Oba moduly možno mať nainštalované súčasne.

## Obmedzenia {#limitations}

- Dobropis zoskupený s faktúrou v platobnom príkaze (voľba spôsobu platby
  *Group Transactions in Payment Orders*) sa zapíše ako **jedna položka
  v čistej sume** — tej, ktorú príkaz zaúčtuje ako platbu. Nesie variabilný
  symbol faktúry; ak sa jeden dobropis započíta proti viacerým faktúram,
  symboly sa líšia a neodíde žiadny. Skupiny bez dobropisu majú naďalej jednu
  položku za faktúru. Bez zoskupenia sa riadok dobropisu odmietne.
- **„Odoslané“ neznamená „zaplatené“**: dávka čaká v internetbankingu na
  autorizáciu.
- Číslo dávky Fio nie je ID pokynu, ktoré sa neskôr objaví na riadkoch výpisu,
  takže platbu cez neho k riadku výpisu nedohľadáte — párujte podľa VS, sumy a
  dátumu.
- Účet platiteľa nemôže mať **predčíslie**: `accountFrom` je vo Fio holé číslo.
  Nastavte denníku číslo účtu tak, ako ho ukazuje samotné Fio.
- **Slovenských príjemcov zadávajte ako IBAN.** Účet `číslo/kód banky` sa
  číta ako český. Keď Odoo vie, že je slovenský — krajina jeho banky, inak
  krajina majiteľa je Slovensko — platba sa odmietne so žiadosťou o IBAN `SK`,
  namiesto aby odišla českej banke s tým kódom; bez zaznamenanej krajiny
  odíde ďalej ako česká tuzemská platba.
- Fio neprevádzkuje testovacie prostredie; prvú dávku si pred autorizáciou v
  internetbankingu dôkladne skontrolujte.
