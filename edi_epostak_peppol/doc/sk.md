---
title: ePošťák — elektronická fakturácia Peppol
summary: Odosiela a prijíma elektronické faktúry a obchodné odpovede Peppol cez slovenský prístupový bod ePošťák — s vlastnou zmluvou s ePošťákom alebo cez hostovanú službu Data Dance.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

**ePošťák** je slovenský prístupový bod siete Peppol. Tieto moduly k nemu
pripoja Odoo, aby elektronické faktúry pripravené modulom
[elektronickej fakturácie Peppol](module:edi_base_peppol) naozaj odchádzali
a prichádzali:

| Modul | Úloha |
|---|---|
| tento modul | urobí z ePošťáka prenos pre doklady Peppol |
| [module:edi_epostak_base](module:edi_epostak_base) | prepínač testovacie / produkčné prostredie, ID firmy, kontrola Peppol adresy |
| [module:edi_epostak_connector_sapi](module:edi_epostak_connector_sapi) | samotné pripojenie: prihlasovacie údaje, odosielanie, vyzdvihovanie, stav doručenia, kontrola dosiahnuteľnosti |
| [module:edi_epostak_broker_client](module:edi_epostak_broker_client) | len v hostovanej službe Data Dance: odosiela cez sprostredkovateľa hostingu namiesto vlastných prihlasovacích údajov k ePošťáku ([nižšie](#broker)) |

Nainštalujte tento modul a konektor. Čo sa odosiela, kedy a čo sa stane s
prijatými dokladmi, rozhoduje modul Peppol — jeho návod opisuje
[smerovanie](module:edi_base_peppol#routing),
[odoslanie](module:edi_base_peppol#sending),
[prijímanie](module:edi_base_peppol#receiving) a
[obchodné odpovede](module:edi_base_peppol#responses). Tento návod pokrýva to,
čo je špecifické pre ePošťák: pripojenie, význam jednotlivých stavov a čo
robiť, keď niečo zlyhá.

Povinnú elektronickú fakturáciu od 1. januára 2027 zhŕňa
[právny rámec](module:edi_base_peppol#legal) návodu k Peppolu.

Používateľské rozhranie je preložené do slovenčiny; anglické názvy polí a
tlačidiel uvedené v tomto návode (v zátvorke alebo kurzívou) zodpovedajú
anglickej verzii.

## Nastavenie {#setup}

Všetko je v *Nastavenia → EDI*, časť **ePošťák**. Prostredie platí pre celú
databázu; ID firmy, prihlasovacie údaje (v hostovanej službe kľúč
sprostredkovateľa) a vyzdvihovanie patria **spoločnosti, v ktorej práve
pracujete**. Ďalšiu spoločnosť nastavíte tak, že sa do nej prepnete a vyplníte
jej vlastné údaje.

1. **Prostredie** (*ePošťák Environment*): **Sandbox** (testovacie,
   predvolené) alebo **Production** (produkčné). Kým je aktívny sandbox,
   upozorňuje na to žltý pruh; doklady zo sandboxu sa do skutočnej siete
   Peppol nikdy nedostanú. Každé prostredie má vlastné prihlasovacie údaje,
   takže prepnutie ich nezmaže.
2. **Prihlasovacie údaje** pre aktívne prostredie — blok *Credentials
   (Sandbox)* alebo *Credentials (Production)*: **Client ID** a **Client
   Secret** z vášho účtu v ePošťáku. Polia s adresami URL sú predvyplnené a
   obvykle sa nemenia. V hostovanej službe vyplňte namiesto nich
   sprostredkovateľa ([nižšie](#broker)).
3. **Configured key** ukáže, aký druh kľúča ste zadali — z poľa s heslom sa
   to spätne prečítať nedá:

   | Kľúč | ID firmy |
   |---|---|
   | kľúč firmy (`sk_live_…`) | **ePošťák Firm ID** nechajte prázdne; firma vyplýva z kľúča |
   | integrátorský kľúč (`sk_int_…`), ktorý hovorí za viac firiem | **ePošťák Firm ID** je povinné: UUID firmy, za ktorú táto databáza fakturuje |

4. **Test Connection** (otestovať pripojenie). Uloží nastavenia a skúsi sa
   prihlásiť. S integrátorským kľúčom bez ID firmy vypíše firmy, za ktoré
   smie kľúč konať, aj s ich IČO a Peppol adresou; ak je práve jedna, ID
   firmy spoločnosti doplní sám. Vymenuje aj ostatné spoločnosti, ktoré
   povoľujú e-fakturáciu, ale vlastné prihlasovacie údaje k ePošťáku nemajú. Potom stlačte tlačidlo znova na potvrdenie. Výsledok sa
   vždy zobrazí ako oznámenie — zlyhanie nezahodí to, čo ste zadali.
5. **Peppol adresa vašej spoločnosti** — na kontakte spoločnosti, záložka
   *Fakturácia*: **Peppol e-adresa (EAS)** `0245` a ako koncový bod vaše
   **DIČ** (pozri [slovenský identifikátor](module:l10n_sk_ubl_bis3#participant)).
   Každá požiadavka na ePošťák sa vykoná v mene tohto účastníka. Koncový bod
   pod schémou 0245, ktorý nemá presne desať číslic, sa odmietne skôr, než
   sa čokoľvek odošle; osem číslic sa ohlási ako IČO, ktoré smerovateľné nie
   je.
6. **Prepínače spoločnosti** na tej istej stránke nastavení, blok *Peppol
   BIS3 (táto firma)* — povolenie e-fakturácie, rozsah, automatické
   odosielanie, nákupný denník: pozri
   [nastavenie Peppolu](module:edi_base_peppol#setup). Ak je nainštalovaných
   viac poskytovateľov Peppol, nastavte tam **Peppol Transport**; ak zostane
   prázdne, cez Peppol neodíde nič.
7. **Pred prvou faktúrou overte odberateľa** — pozri
   [dosiahnuteľnosť](#reachability).

Nastavenia otvárajú len správcovia systému; na odosielanie a prezeranie EDI
správ potrebujú aj skupiny EDI ([prístup](module:edi_base#setup)).

## Cez hostovanú službu Data Dance {#broker}

V databáze hostovanej spoločnosťou Data Dance je nainštalovaný modul
[module:edi_epostak_broker_client](module:edi_epostak_broker_client) a
pripojenie ide cez sprostredkovateľa (*broker*) hostovanej služby, nie
priamo do ePošťáka. Databáza potom **nemá žiadne prihlasovacie údaje k
ePošťáku**. V *Nastavenia → EDI → ePošťák*, blok **Data Dance broker**:

| Pole | Čo to je |
|---|---|
| Broker URL | Vyplnením sa databáza prepne do režimu sprostredkovateľa; vymazaním sa vráti k priamej zmluve s ePošťákom |
| Broker key ID | identifikuje kľúč; sám osebe nie je tajný — pre každú spoločnosť |
| Broker key | podpisuje každú požiadavku; zobrazí sa raz pri vydaní — pre každú spoločnosť |

Tieto údaje dostanete spolu s hostovanou službou. Client ID, Client Secret a
ID firmy sa potom nepoužívajú ani nepotrebujú — za ktoré spoločnosti smie
databáza konať, rozhoduje sprostredkovateľ. **Test Connection** sa ho na to
spýta a ohlási chybu, ak pre túto databázu neuvádza žiadnu spoločnosť.

Všetko ostatné — doklady, stavy, vyzdvihovanie, kontrola dosiahnuteľnosti —
funguje rovnako. Chyby prichádzajú už roztriedené: kľúč databázy bol
odmietnutý, doklad alebo adresa boli odmietnuté (opravte ich, inak zlyhajú
rovnako znova), alebo je služba dočasne nedostupná.

## Čo znamenajú stavy {#statuses}

EDI správa dokladu odoslaného cez ePošťák prechádza takto:

| Stav | Význam |
|---|---|
| Ready | súbor je vytvorený a čaká na odoslanie |
| Queued | čaká na *EDI: send queued messages (no job runner)*, ktorá beží každé 2 minúty; čaká tu aj správa, ktorej odoslanie dočasne zlyhalo, s varovaním v *Error Details* |
| **Sent** | ePošťák **prevzal doklad na prenos** (HTTP 202). Ide o prevzatie, **nie o doručenie**. *Provider Interchange ID* obsahuje ID dokladu v ePošťáku. |
| **Done** | ePošťák hlási doklad ako **doručený** do prístupového bodu príjemcu |
| Error | odoslanie zlyhalo alebo ePošťák hlási doklad ako *rejected* (odmietnutý), *send failed*, *delivery failed* (doručenie zlyhalo) či *validation failed* (neprešiel kontrolou); *Error Details* obsahuje „ePošťák status: …“ s dôvodom od ePošťáka |

Zo stavu *Sent* sa správa dostane do *Done* alebo *Error* naplánovanou akciou
**ePošťák: Query Outbound Delivery Status**, ktorá beží každých 30 minút a
spracuje najviac 500 odoslaných správ. Potrebuje zapnuté **Track Delivery
Status** (predvolené) a kľúč s právom čítať doklady (rozsah `documents:read`).
Ak ePošťák dopyt na stav odmietne, sledovanie sa v tom behu preskočí a správy
jednoducho zostanú v stave *Sent* — správa, ktorá je v stave *Sent* dlho,
teda znamená „prevzatá, doručenie zatiaľ nepotvrdené“, nie „doručená“.

Doručenie do prístupového bodu príjemcu nie je súhlas odberateľa. Či
odberateľ faktúru prijme, rozporuje alebo zaplatí, príde — ak to jeho systém
posiela — ako [odpoveď na faktúru](module:edi_base_peppol#responses).

## Keď odoslanie zlyhá {#errors}

| Čo vidíte | Príčina | Čo urobiť |
|---|---|---|
| *Error*, text o prihlasovacích údajoch, Peppol adrese, ID firmy alebo chýbajúcom prvku | problém nastavenia alebo adresovania zistený pred odoslaním | opravte nastavenie alebo kontakt uvedený v hlásení a stlačte **Send** |
| *Error*, kód ePošťáka (napr. kontrola dokladu) | ePošťák doklad odmietol; znova zlyhá rovnako | opravte faktúru alebo kontakt |
| *Queued*, úroveň *Warning*, dôvod v *Error Details* | dočasný problém: vypršaný čas, obmedzenie počtu požiadaviek, nedostupnosť ePošťáka alebo jeho prihlásenia | nič — ďalší beh odosielania to skúsi znova |

Dočasné zlyhanie sa **opakuje automaticky** pri každom behu *EDI: send
queued messages (no job runner)*, teda každé 2 minúty, kým ePošťák doklad
neprevezme alebo ho natrvalo neodmietne; počet pokusov nie je obmedzený a
čakanie *Retry-After*, o ktoré ePošťák požiada, sa nad tento interval
nedodržiava. Trvalé zlyhanie presunie správu do stavu *Error*, v ktorom
zostane, kým ju niekto neodošle znova. Jeden neúspešný doklad nezastaví ani
nezvráti ostatné odoslané v tom istom behu. Identifikátor korelácie od
ePošťáka, ak ho poslal, je na konci chyby v hranatých zátvorkách — uveďte ho
podpore ePošťáka.

Na opakovanie stlačte **Send** na EDI správe (alebo *Akcie → Send (queue
dispatch)* pre viac správ). Odošle sa **ten istý súbor** a ePošťák ho spozná
podľa kľúča idempotencie (*Transmission UUID*, odvodeného z obsahu súboru):
ak predchádzajúci pokus v skutočnosti pred chybou prešiel, opakovanie sa
zlúči a nedoručí sa dvakrát. **Odoslať cez Peppol** na faktúre vytvorí súbor
nanovo; ak sa v ňom čokoľvek zmenilo, je to pre ePošťák nový doklad.

## Prijímanie {#receiving}

Naplánovaná akcia **ePošťák: Poll Inbound Documents** beží každých
30 minút. Za každú spoločnosť s vlastnými prihlasovacími údajmi k ePošťáku si
ako táto spoločnosť vypýta doklady čakajúce na jej Peppol adresu (spoločnosti
s jedným integrátorským kľúčom sa pýtajú po jednej Peppol adrese), 20 na stránku a najviac 5 stránok na jeden beh (*Documents per
Poll Page*, *Max Pages per Poll*), a ak čakajú ďalšie, spustí sa hneď znova.
Každý doklad sa uloží a spracuje podľa
[prijímania elektronických faktúr](module:edi_base_peppol#receiving) a až
potom sa ePošťáku potvrdí, čím sa odstráni z jeho frontu. Doklad, ktorého
obsah sa nedá stiahnuť, sa nepotvrdí a skúsi sa znova nabudúce. Potvrdenie
sa týka len Odoo a ePošťáka; odosielateľ z neho nedostane nič.

Prijímanie zlyháva potichu, ak sa nepozeráte, preto konektor hlási sám:

- **Last inbound poll** v nastaveniach ukazuje pre spoločnosť, v ktorej
  pracujete, „OK at … — N document(s) fetched“, „FAILED at … — dôvod (last
  success: …)“ alebo „Never polled“.
- **Poll inbound now** spustí vyzdvihnutie tejto spoločnosti hneď a povie,
  ako dopadlo.
- Po **Warn after N failed polls** zlyhaniach po sebe (predvolene 3; 0 to
  vypne) vznikne na kontakte vašej spoločnosti aktivita To-Do „Incoming
  ePošťák documents are not arriving“ pre prvého používateľa so skupinou EDI
  Manager (inak EDI User, inak pre administrátora). Keď vyzdvihovanie znova
  funguje, uzavrie sa sama.

## Kontrola Peppol adresy odberateľa {#reachability}

Na kontakte s Peppol adresou sa tlačidlom **Check Peppol reachability**
(vedľa koncového bodu, pre používateľov EDI) cez ePošťák spýtate adresára
Peppol, či táto adresa môže prijímať faktúry a dobropisy Peppol BIS Billing
3.0:

| Odpoveď | Význam |
|---|---|
| Reachable on Peppol | registrovaná a prijíma faktúry aj dobropisy BIS 3.0 |
| Registered, but not for BIS3 billing | v sieti existuje, ale odoslanie faktúry na ňu bude odmietnuté |
| Not registered on Peppol | adresár ju nepozná — odberateľ ešte nie je v sieti Peppol, alebo je chybná schéma či číslo (slovenské DIČ je schéma 0245, IČ DPH schéma 9950) |

Ak ePošťák uvedie vlastný dôvod, doplní sa, rovnako ako poznámka, ak účastník
nie je pripravený na sieť (*not network-ready*).

## Ladenie prenosu {#tuning}

Blok *Transfer Tuning*; predvolené hodnoty vyhovujú väčšine databáz.

| Nastavenie | Predvolené | Účel |
|---|---|---|
| OAuth Scope | `documents:send documents:read documents:write` | práva vyžiadané pri prihlásení; samotné `documents:send` umožní odosielať, ale nie vyzdvihovať ani sledovať doručenie |
| Track Delivery Status | zapnuté | sledovať stav doručenia odoslaných dokladov |
| Warn after N failed polls | 3 | kedy vytvoriť aktivitu o zlyhanom vyzdvihovaní |
| Documents per Poll Page | 20 | 1 až 100 |
| Max Pages per Poll | 5 | počet stránok na beh, potom sa vyzdvihnutie naplánuje znova |
| Request Timeout (s) | 60 | na jednu požiadavku na ePošťák |

## Obmedzenia {#limitations}

- **Jedno prostredie na databázu.** Sandbox alebo produkcia platí pre všetky
  spoločnosti; prihlasovacie údaje a ID firmy má každá spoločnosť vlastné.
  Spoločnosť, ktorá povoľuje e-fakturáciu bez vlastných prihlasovacích
  údajov, neodosiela (jej doklady skončia v *Error* s menom spoločnosti) ani
  nevyzdvihuje.
- Správa si počas odosielania ponechá prostredie, v ktorom vznikla;
  opätovné stlačenie *Odoslať cez Peppol* ju vytvorí znova v prostredí
  aktívnom **teraz** (pozri [odoslanie](module:edi_base_peppol#sending)).
- Trvalo neúspešné odoslanie sa automaticky neopakuje. Dočasné zlyhanie sa
  zopakuje po Retry-After od ePošťáku alebo po rastúcej pauze, najviac päťkrát
  (pozri [odosielanie](module:edi_base#sending)).
- *Configured key* v režime sprostredkovateľa ukazuje „No secret configured
  yet“, čo je tam v poriadku.
- Či je ePošťák certifikovaným poskytovateľom doručovacej služby podľa § 76a
  zákona o DPH, musí potvrdiť ePošťák; tento modul to neoveruje.
