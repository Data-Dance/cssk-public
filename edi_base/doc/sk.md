---
title: EDI — základ
summary: Spoločný základ každého pripojenia EDI a Peppol — evidencia EDI správ, ich stavy, odosielanie a prijímanie a nastavenia partnerov, ktoré zdieľajú všetci poskytovatelia.
verified: 19.0.1.9.0
---

## Na čo slúži {#purpose}

Každý elektronický doklad, ktorý Odoo vymieňa s obchodným partnerom cez
poskytovateľa EDI — objednávka, potvrdenie objednávky, avízo o expedícii,
faktúra, elektronická faktúra Peppol či obchodná odpoveď — sa eviduje ako
jedna **EDI správa**. Modul poskytuje túto evidenciu a všetko okolo nej:

- zoznam *EDI → Messages* (správy), v ktorom sa uchovávajú všetky prijaté aj
  odoslané doklady všetkých poskytovateľov aj s pôvodným XML;
- **stavy**, ktorými správa prechádza, a tlačidlá, ktoré ju posúvajú ďalej;
- spôsob, akým sa odchádzajúca správa **odovzdá poskytovateľovi** a ako sa
  prichádzajúce doklady **vyzdvihnú**, uložia a spracujú;
- **GLN** každého kontaktu a prepínač automatického odosielania pre
  jednotlivých odberateľov.

Sám sa nikam nepripája. Prenos zabezpečuje modul poskytovateľa:

| Poskytovateľ | Moduly |
|---|---|
| Editel (eXite) | `edi_editel_*` |
| GRiT (Orion) | `edi_grit_*` |
| ePošťák (prístupový bod Peppol) | [module:edi_epostak_peppol](module:edi_epostak_peppol) |

Čo sa deje s objednávkami, dodávkami a faktúrami, opisujú návody pre stranu
predaja [module:edi_base_sale](module:edi_base_sale), stranu nákupu
[module:edi_base_purchase](module:edi_base_purchase) a elektronickú
fakturáciu Peppol [module:edi_base_peppol](module:edi_base_peppol).

Používateľské rozhranie je preložené do slovenčiny; anglické názvy polí a
tlačidiel uvedené v tomto návode (v zátvorke alebo kurzívou) zodpovedajú
anglickej verzii.

## Nastavenie {#setup}

1. **Prideľte prístup.** Menu **EDI** vidia len členovia dvoch skupín, ktoré
   sa nastavujú na používateľovi (*Nastavenia → Používatelia*):

   | Skupina | Môže |
   |---|---|
   | EDI User | vidieť menu EDI, správy a záložky EDI na dokladoch |
   | EDI Manager | všetko uvedené a navyše **Send** (odoslať), **Reprocess** (znova spracovať) a vytvárať či meniť správy |

   Administrátor v žiadnej z nich štandardne nie je — najprv pridajte seba.
   Odoslanie faktúry cez Peppol vytvára EDI správu, preto ten, kto ju
   odosiela, potrebuje skupinu **EDI Manager** (pozri
   [Peppol](module:edi_base_peppol#limitations)).
2. **Zadajte vlastné GLN** na kontakte vašej spoločnosti (pole **GLN**,
   záložka *Predaj a nákup*) a GLN každého partnera, s ktorým si vymieňate
   doklady EDIFACT. Pripojenia Peppol identifikujú strany podľa Peppol
   adresy — pozri [návod k Peppolu](module:edi_base_peppol#setup).
3. **Nainštalujte a nastavte poskytovateľa.** Jeho nastavenia sú v
   *Nastavenia → EDI* alebo cez *EDI → Configuration → Settings* (len pre
   správcov systému).

### Kontakty {#partners}

Na formulári kontaktu, záložka *Predaj a nákup*:

| Pole | Význam |
|---|---|
| GLN | Globálne lokalizačné číslo kontaktu. Odoo ho štandardne zobrazuje len na dodacích adresách; tu je viditeľné na každom kontakte, lebo každá strana EDI — vaša spoločnosť, odberateľ, príjemca faktúry, miesto dodania — sa identifikuje práve ním. Kontakty sa dajú podľa GLN aj vyhľadávať. |
| Prepísať automatické odosielanie EDI (*Override EDI auto-send*) | Vypnuté (predvolené): odchádzajúce EDI správy pre tohto odberateľa či dodávateľa sa riadia globálnymi nastaveniami poskytovateľa. Zapnuté: moduly poskytovateľov zobrazia voľbu pre jednotlivé doklady (*always* / *never* / *default*), ktorá má pre túto firmu a všetky jej kontakty prednosť. |

Ďalšie dve polia patria poskytovateľom EDIFACT a sú opísané
[nižšie](#gs1).

## Evidencia správ {#messages}

*EDI → Messages* zobrazuje všetky správy od najnovšej. Červené riadky sú
chybné, oranžové majú upozornenie alebo pochádzajú z testovacieho prostredia,
sivé sú vybavené. Filtre: *Inbound* (prijaté), *Outbound* (odoslané), *Test
Mode*, *Production*, *Errors* (chyby), *Pending* (koncept, pripravené alebo
prijaté), *Done*, *Peppol BIS3*; zoskupenie podľa poskytovateľa, typu správy,
smeru, stavu alebo partnera.

Formulár správy obsahuje:

| Pole | Význam |
|---|---|
| Document Name | názov súboru dokladu |
| Provider | prenos (Editel, GRiT, ePošťák, …) |
| Document Family | *EDIFACT* alebo *Peppol BIS3* — štandard dokladu, nezávislý od poskytovateľa |
| Message Type | ORDERS, ORDRSP, DESADV, INVOIC, … pre EDIFACT; Invoice, CreditNote, MLR, InvoiceResponse pre Peppol |
| Direction | prijatá (*Inbound*) / odoslaná (*Outbound*) |
| Environment | testovací alebo produkčný režim poskytovateľa v čase vytvorenia správy; testovacia správa má pásku **TEST** |
| Partner | určený podľa GLN či Peppol adresy odosielateľa (prijaté) alebo príjemcu (odoslané) |
| Message ID, Message Date, Sender GLN, Receiver GLN | údaje prečítané zo samotného dokladu; pri Peppole obsahujú polia „GLN“ Peppol adresy |
| External Reference, Customer / Vendor Reference | vaše číslo dokladu a číslo objednávky protistrany, aby sa celá komunikácia (objednávka → potvrdenie → avízo → faktúra) dala nájsť podľa jednej referencie |
| Provider Interchange ID, Transmission UUID | identifikátory poskytovateľa — uvádzajte ich podpore poskytovateľa |
| Error Details, Blocking Level | prečo správa zlyhala a či ide o upozornenie alebo chybu |
| XML Content | doklad, prehľadne odsadený |

XML sa vždy uloží ako príloha správy; doklady do 1 MB sa zobrazujú aj
priamo vo formulári. Prepojenia na objednávku, dodávku, faktúru či
dodávateľský doklad pridávajú moduly pre predaj, nákup a Peppol, ktoré
zároveň pridajú na tieto doklady záložku **EDI Messages**.

Správa patrí **spoločnosti dokladu, ku ktorému vznikla**, nie spoločnosti, v
ktorej práve pracoval používateľ, a v mene tejto spoločnosti sa aj odosiela
a spracúva.

## Stavy {#states}

| Stav | Odoslaná správa | Prijatá správa |
|---|---|---|
| Draft (koncept) | vytvorená, ešte nepripravená | — |
| Ready (pripravená) | vygenerovaná, čaká na odoslanie (automatické odosielanie je vypnuté alebo čaká na vás) | — |
| Queued (vo fronte) | odovzdaná na odoslanie, poskytovateľ ju ešte neprevzal | — |
| Sent (odoslaná) | poskytovateľ ju prevzal | — |
| Received (prijatá) | — | uložená, čaká na spracovanie alebo sa spracúva znova |
| Error (chyba) | odoslanie zlyhalo, pozri *Error Details* | spracovanie zlyhalo, doklad zostáva uložený |
| Done (vybavená) | dokončená: pri niektorých poskytovateľoch to znamená potvrdené doručenie príjemcovi (pozri návod poskytovateľa) | spracovaná: objednávka, doklad alebo odpoveď boli vytvorené či zaznamenané |

Čo presne *Sent* a *Done* dokazujú, závisí od poskytovateľa. Pri ePošťáku
*Sent* znamená, že prístupový bod doklad prevzal na prenos, a až *Done*, že
ho prijal prístupový bod príjemcu — pozri
[stav doručenia](module:edi_epostak_peppol#statuses).

## Odosielanie {#sending}

Odchádzajúce správy vytvárajú moduly poskytovateľov z dokladov — automaticky
pri potvrdení či zaúčtovaní dokladu, ak je automatické odosielanie zapnuté,
alebo tlačidlom poskytovateľa. Správu môžete odoslať alebo znova odoslať aj
sami:

- tlačidlom **Send** na formulári správy (EDI Manager) pri odosielaných
  správach v stave *Draft*, *Ready*, *Queued* alebo *Error*;
- hromadne: označte správy v zozname a zvoľte *Akcie → Send (queue
  dispatch)*. Dialóg najprv ukáže, čo sa odošle a čo sa preskočí (prijaté
  správy, správy už odoslané či vybavené).

Odoslanie vymaže predchádzajúcu chybu, presunie správu do stavu **Queued** a
zapíše na objednávku, dodávku alebo faktúru riadok „… queued for dispatch via
…“.

### Ako správa opustí front {#dispatch}

Každý poskytovateľ určí jeden z dvoch spôsobov:

- **Fronta úloh.** Zo správy sa stane úloha na pozadí v rade úloh OCA
  (`queue_job`), ktorú so správou prepojí modul
  [module:edi_base_queue_job](module:edi_base_queue_job). Takto pracujú
  konektory Editel a GRiT, ktoré ho aj inštalujú. Správa s úlohami má
  tlačidlo **Queue Jobs**; na úlohe otvorí správu tlačidlo *Related* a zoznam
  úloh sa dá podľa správy filtrovať. Úloha sa skúša najviac päťkrát.
- **Naplánovaná akcia.** *EDI: send queued messages (no job runner)* beží
  každé 2 minúty a odošle najviac 100 správ vo fronte od poskytovateľov,
  ktorí sa k nej prihlásili — medzi nimi je ePošťák. Každá správa sa odosiela
  samostatne: pri dočasnom zlyhaní (poskytovateľ nedostupný, prekročený limit
  požiadaviek) zostane v stave **Queued** s varovaním v *Error Details*
  a časom *Retry Not Before*: Retry-After poskytovateľa, inak pauza, ktorá sa
  s každým pokusom zdvojnásobí (2, 4, 8 … minút, najviac hodina). Po piatich
  dočasných zlyhaniach — prekročený limit sa nepočíta — prejde do stavu
  **Error** s posledným dôvodom; pri inom zlyhaní hneď. Opätovné odoslanie
  začne počítať odznova. Jedna
  neodoslateľná správa ostatné nezastaví ani nezvráti a výsledok každej
  správy sa uloží pred odoslaním ďalšej, takže prerušený beh si ponechá to,
  čo poskytovateľ už prevzal. Keď beh vyčerpá svoj čas, zvyšok zostane vo
  fronte na ďalší beh.

O spôsobe rozhoduje poskytovateľ, nie databáza, takže ani v databáze, kde sú
oba, sa jedna správa neodošle dvakrát.

## Prijímanie {#receiving}

Každý poskytovateľ má vlastnú naplánovanú akciu, ktorá vyzdvihuje nové
doklady. Pre každý doklad platí:

1. Ak už od toho istého poskytovateľa prišla správa s rovnakým ID správy,
   doklad sa preskočí ako duplikát (a potvrdí sa). Skupina poskytovateľov to
   môže sprísniť: pri Peppole sa musí zhodovať aj odosielateľ, príjemca a
   druh dokladu — pozri
   [prijímanie dokladov Peppol](module:edi_base_peppol#receiving).
2. Inak sa **najprv uloží** aj s XML ako správa v stave *Received*.
3. Potom sa spracuje — vznikne objednávka, doklad, zaznamená sa odpoveď — a
   správa prejde do stavu **Done**. Ak spracovanie zlyhá, správa prejde do
   stavu **Error** s dôvodom v *Error Details*; doklad sa nestratí.
4. Doklad sa poskytovateľovi potvrdí, aby ho nedoručil znova.

Ak poskytovateľ hlási, že čakajú ďalšie doklady, vyzdvihnutie sa spustí
znova hneď, nie až v ďalšom intervale.

**Reprocess** (EDI Manager, prijaté správy v stave *Received* alebo *Error*)
spustí krok 3 znova — typicky po tom, čo ste založili chýbajúci produkt alebo
doplnili GLN kontaktu.

### Párovanie produktov {#products}

Riadky prijatých objednávok a avíz sa párujú na produkty v tomto poradí:

1. **čiarový kód** — v tvare, ako prišiel, bez úvodných núl a doplnený na 8,
   12, 13 a 14 číslic, lebo partneri sa v dopĺňaní EAN nezhodujú;
2. vlastný kód odosielateľa pre produkt (*Kód produktu dodávateľa* v riadku
   dodávateľa na produkte), ak je odosielateľ známy;
3. **interná referencia** produktu.

Ak riadok nespáruje nič, celá prijatá objednávka štandardne zlyhá a chyba
vypíše všetky nespárované riadky (EAN, množstvo, cenu, názvy a kódy) s
radou založiť produkty a správu znova spracovať. Modul
[module:edi_base_sale_pending](module:edi_base_sale_pending) to mení, pozri
[čakajúce riadky](module:edi_base_sale#pending-lines).

## Variabilný symbol {#variable-symbol}

Kde správa nesie variabilný symbol — bankové údaje dodávateľa v odchádzajúcej
INVOIC, uhrádzaná faktúra v REMADV — je to symbol, aký používa český alebo
slovenský platobný príkaz: **len číslice, najviac desať**. Je to
*Variabilný symbol* z [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
ak je nainštalovaný; inak číslice *Referencie platby*, inak čísla faktúry
(pri dodávateľskej faktúre čísla dodávateľa), a ponechá sa posledných desať.
Z `INV/2026/00012` vznikne `202600012`. Ak tam nie je ani jedna číslica,
prvok sa vynechá.

## Identita strán EDIFACT (GS1) {#gs1}

Modul [module:edi_base_gs1](module:edi_base_gs1), ktorý sa inštaluje s
poskytovateľmi Editel a GRiT, pridáva nastavenia strán GS1, ktoré potrebuje
EDIFACT a Peppol nie:

| Kde | Pole | Význam |
|---|---|---|
| Kontakt | Komunikačný koncový bod EDI (*EDI Communication Endpoint*) | Kontakt, ktorého GLN vlastní schránku EDI; použije sa ako odosielateľ či adresát obálky, kým kupujúci, príjemca faktúry a miesto dodania si ponechajú vlastné GLN. Nastavte ho na firme, jej kontakty ho zdedia. Prázdne: vlastné GLN kontaktu. |
| Kontakt | DESADV v režime SSCC (*EDI DESADV in SSCC mode*) | Avíza o expedícii pre tohto odberateľa sa posielajú v štruktúre balení SSCC namiesto plochého zoznamu tovarov. Nastavuje sa na firme, kontakty ho zdedia. |
| Sklad (formulár, pri adrese) | GLN miesta dodania (*EDI GLN (Delivery Point)*) | GLN skladu ako miesta dodania v odchádzajúcich dokladoch a pri párovaní prijatých avíz; ak je prázdne, použije sa GLN spoločnosti. |

## Obmedzenia {#limitations}

- Dátumy a časy v dokladoch EDIFACT sa čítajú a zapisujú v časovom pásme zo
  systémového parametra `edi.timezone` (predvolené `Europe/Bratislava`).
- Pri dokladoch EDIFACT sa duplicity rozpoznávajú len podľa ID správy
  (interchange) a poskytovateľa; Peppol pridáva odosielateľa, príjemcu a
  druh dokladu (pozri
  [obmedzenia Peppolu](module:edi_base_peppol#limitations)).
- Správy sa z používateľského rozhrania nedajú zmazať; právo mazať ich nemá
  nikto.
