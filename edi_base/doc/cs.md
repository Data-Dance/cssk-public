---
title: EDI — základ
summary: Společný základ každého připojení EDI a Peppol — evidence EDI zpráv, jejich stavy, odesílání a příjem a nastavení partnerů, která sdílejí všichni poskytovatelé.
verified: 19.0.1.9.0
---

## K čemu slouží {#purpose}

Každý elektronický doklad, který Odoo vyměňuje s obchodním partnerem přes
poskytovatele EDI — objednávka, potvrzení objednávky, avízo o expedici,
faktura, elektronická faktura Peppol nebo obchodní odpověď — se eviduje jako
jedna **EDI zpráva**. Modul poskytuje tuto evidenci a vše kolem ní:

- seznam *EDI → Messages* (zprávy), ve kterém se uchovávají všechny přijaté i
  odeslané doklady všech poskytovatelů včetně původního XML;
- **stavy**, kterými zpráva prochází, a tlačítka, která ji posouvají dál;
- způsob, jakým se odchozí zpráva **předá poskytovateli** a jak se příchozí
  doklady **vyzvednou**, uloží a zpracují;
- **GLN** každého kontaktu a přepínač automatického odesílání pro jednotlivé
  odběratele.

Sám se nikam nepřipojuje. Přenos zajišťuje modul poskytovatele:

| Poskytovatel | Moduly |
|---|---|
| Editel (eXite) | `edi_editel_*` |
| GRiT (Orion) | `edi_grit_*` |
| ePošťák (přístupový bod Peppol) | [module:edi_epostak_peppol](module:edi_epostak_peppol) |

Co se děje s objednávkami, dodávkami a fakturami, popisují návody pro stranu
prodeje [module:edi_base_sale](module:edi_base_sale), stranu nákupu
[module:edi_base_purchase](module:edi_base_purchase) a elektronickou
fakturaci Peppol [module:edi_base_peppol](module:edi_base_peppol).

Uživatelské rozhraní je přeloženo do češtiny; anglické názvy polí
a tlačítek uvedené v tomto návodu (v závorce nebo kurzívou) odpovídají
anglické verzi.

## Nastavení {#setup}

1. **Přidělte přístup.** Nabídku **EDI** vidí jen členové dvou skupin, které
   se nastavují na uživateli (*Nastavení → Uživatelé*):

   | Skupina | Může |
   |---|---|
   | EDI User | vidět nabídku EDI, zprávy a záložky EDI na dokladech |
   | EDI Manager | vše výše uvedené a navíc **Send** (odeslat), **Reprocess** (znovu zpracovat) a vytvářet či měnit zprávy |

   Administrátor ve výchozím stavu není v žádné z nich — nejprve přidejte
   sebe. Odeslání faktury přes Peppol vytváří EDI zprávu, proto ten, kdo ji
   odesílá, potřebuje skupinu **EDI Manager** (viz
   [Peppol](module:edi_base_peppol#limitations)).
2. **Zadejte vlastní GLN** na kontaktu vaší společnosti (pole **GLN**,
   záložka *Nákup a Prodej*) a GLN každého partnera, se kterým si vyměňujete
   doklady EDIFACT. Připojení Peppol identifikují strany podle Peppol
   adresy — viz [návod k Peppolu](module:edi_base_peppol#setup).
3. **Nainstalujte a nastavte poskytovatele.** Jeho nastavení najdete v
   *Nastavení → EDI* nebo přes *EDI → Configuration → Settings* (jen pro
   správce systému).

### Kontakty {#partners}

Na formuláři kontaktu, záložka *Nákup a Prodej*:

| Pole | Význam |
|---|---|
| GLN | Globální lokalizační číslo kontaktu. Odoo ho standardně zobrazuje jen na dodacích adresách; zde je vidět na každém kontaktu, protože každá strana EDI — vaše společnost, odběratel, příjemce faktury, místo dodání — se identifikuje právě jím. Kontakty lze podle GLN i vyhledávat. |
| Přepsat automatické odesílání EDI (*Override EDI auto-send*) | Vypnuto (výchozí): odchozí EDI zprávy pro tohoto odběratele či dodavatele se řídí globálním nastavením poskytovatele. Zapnuto: moduly poskytovatelů zobrazí volbu pro jednotlivé doklady (*always* / *never* / *default*), která má pro tuto firmu a všechny její kontakty přednost. |

Další dvě pole patří poskytovatelům EDIFACT a jsou popsána [níže](#gs1).

## Evidence zpráv {#messages}

*EDI → Messages* zobrazuje všechny zprávy od nejnovější. Červené řádky jsou
chybné, oranžové mají upozornění nebo pocházejí z testovacího prostředí,
šedé jsou vyřízené. Filtry: *Inbound* (přijaté), *Outbound* (odeslané),
*Test Mode*, *Production*, *Errors* (chyby), *Pending* (koncept, připravené
nebo přijaté), *Done*, *Peppol BIS3*; seskupení podle poskytovatele, typu
zprávy, směru, stavu nebo partnera.

Formulář zprávy obsahuje:

| Pole | Význam |
|---|---|
| Document Name | název souboru dokladu |
| Provider | přenos (Editel, GRiT, ePošťák, …) |
| Document Family | *EDIFACT* nebo *Peppol BIS3* — standard dokladu, nezávislý na poskytovateli |
| Message Type | ORDERS, ORDRSP, DESADV, INVOIC, … pro EDIFACT; Invoice, CreditNote, MLR, InvoiceResponse pro Peppol |
| Direction | přijatá (*Inbound*) / odeslaná (*Outbound*) |
| Environment | testovací nebo produkční režim poskytovatele v okamžiku vytvoření zprávy; testovací zpráva má pásku **TEST** |
| Partner | určen podle GLN či Peppol adresy odesílatele (přijaté) nebo příjemce (odeslané) |
| Message ID, Message Date, Sender GLN, Receiver GLN | údaje přečtené ze samotného dokladu; u Peppolu obsahují pole „GLN“ Peppol adresy |
| External Reference, Customer / Vendor Reference | vaše číslo dokladu a číslo objednávky protistrany, aby šla celá komunikace (objednávka → potvrzení → avízo → faktura) najít podle jedné reference |
| Provider Interchange ID, Transmission UUID | identifikátory poskytovatele — uvádějte je podpoře poskytovatele |
| Error Details, Blocking Level | proč zpráva selhala a zda jde o upozornění, nebo chybu |
| XML Content | doklad, přehledně odsazený |

XML se vždy uloží jako příloha zprávy; doklady do 1 MB se zobrazují i přímo
ve formuláři. Vazby na objednávku, dodávku, fakturu či přijatou fakturu
doplňují moduly pro prodej, nákup a Peppol, které zároveň přidají na tyto
doklady záložku **EDI Messages**.

Zpráva patří **společnosti dokladu, ke kterému vznikla**, ne společnosti, ve
které uživatel zrovna pracoval, a jménem této společnosti se také odesílá a
zpracovává.

## Stavy {#states}

| Stav | Odeslaná zpráva | Přijatá zpráva |
|---|---|---|
| Draft (koncept) | vytvořená, ještě nepřipravená | — |
| Ready (připravená) | vygenerovaná, čeká na odeslání (automatické odesílání je vypnuté nebo čeká na vás) | — |
| Queued (ve frontě) | předaná k odeslání, poskytovatel ji ještě nepřevzal | — |
| Sent (odeslaná) | poskytovatel ji převzal | — |
| Received (přijatá) | — | uložená, čeká na zpracování nebo se zpracovává znovu |
| Error (chyba) | odeslání selhalo, viz *Error Details* | zpracování selhalo, doklad zůstává uložen |
| Done (vyřízená) | dokončená: u některých poskytovatelů to znamená potvrzené doručení příjemci (viz návod poskytovatele) | zpracovaná: objednávka, doklad nebo odpověď byly vytvořeny či zaznamenány |

Co přesně *Sent* a *Done* dokazují, závisí na poskytovateli. U ePošťáku
*Sent* znamená, že přístupový bod doklad převzal k přenosu, a teprve *Done*,
že jej přijal přístupový bod příjemce.

## Odesílání {#sending}

Odchozí zprávy vytvářejí moduly poskytovatelů z dokladů — automaticky při
potvrzení či zaúčtování dokladu, je-li automatické odesílání zapnuté, nebo
tlačítkem poskytovatele. Zprávu můžete odeslat nebo znovu odeslat i sami:

- tlačítkem **Send** na formuláři zprávy (EDI Manager) u odesílaných zpráv ve
  stavu *Draft*, *Ready*, *Queued* nebo *Error*;
- hromadně: označte zprávy v seznamu a zvolte *Akce → Send (queue
  dispatch)*. Dialog nejprve ukáže, co se odešle a co se přeskočí (přijaté
  zprávy, zprávy již odeslané či vyřízené).

Odeslání smaže předchozí chybu, přesune zprávu do stavu **Queued** a zapíše
na objednávku, dodávku nebo fakturu řádek „… queued for dispatch via …“.

### Jak zpráva opustí frontu {#dispatch}

Každý poskytovatel určí jeden ze dvou způsobů:

- **Fronta úloh.** Ze zprávy se stane úloha na pozadí ve frontě úloh OCA
  (`queue_job`), kterou se zprávou propojí modul
  [module:edi_base_queue_job](module:edi_base_queue_job). Takto pracují
  konektory Editel a GRiT, které ho také instalují. Zpráva s úlohami má
  tlačítko **Queue Jobs**; na úloze otevře zprávu tlačítko *Related* a seznam
  úloh lze podle zprávy filtrovat. Úloha se zkouší nejvýše pětkrát.
- **Naplánovaná akce.** *EDI: send queued messages (no job runner)* běží
  každé 2 minuty a odešle nejvýše 100 zpráv ve frontě od poskytovatelů, kteří
  se k ní přihlásili — mezi nimi je ePošťák. Každá zpráva se odesílá
  samostatně: při dočasném selhání (poskytovatel nedostupný, překročený limit
  požadavků) zůstane ve stavu **Queued** s varováním v *Error Details*
  a časem *Retry Not Before*: Retry-After poskytovatele, jinak pauza, která se
  s každým pokusem zdvojnásobí (2, 4, 8 … minut, nejvýše hodina). Po pěti
  dočasných selháních — překročený limit se nepočítá — přejde do stavu
  **Error** s posledním důvodem; při jiném selhání hned. Opětovné odeslání
  začne počítat znovu. Jedna
  neodeslatelná zpráva ostatní nezastaví ani nevrátí zpět a výsledek každé
  zprávy se uloží před odesláním další, takže přerušený běh si ponechá to, co
  poskytovatel už převzal. Když běh vyčerpá svůj čas, zbytek zůstane ve frontě
  na další běh.

O způsobu rozhoduje poskytovatel, ne databáze, takže ani v databázi, kde jsou
oba, se jedna zpráva neodešle dvakrát.

## Příjem {#receiving}

Každý poskytovatel má vlastní naplánovanou akci, která vyzvedává nové
doklady. Pro každý doklad platí:

1. Pokud už od téhož poskytovatele přišla zpráva se stejným ID zprávy,
   doklad se přeskočí jako duplicita (a potvrdí se). Skupina poskytovatelů to
   může zpřísnit: u Peppolu se musí shodovat i odesílatel, příjemce a druh
   dokladu — viz
   [příjem dokladů Peppol](module:edi_base_peppol#receiving).
2. Jinak se **nejprve uloží** i s XML jako zpráva ve stavu *Received*.
3. Poté se zpracuje — vznikne objednávka, doklad, zaznamená se odpověď — a
   zpráva přejde do stavu **Done**. Pokud zpracování selže, zpráva přejde do
   stavu **Error** s důvodem v *Error Details*; doklad se neztratí.
4. Doklad se poskytovateli potvrdí, aby ho nedoručil znovu.

Hlásí-li poskytovatel, že čekají další doklady, vyzvednutí se spustí znovu
hned, ne až v dalším intervalu.

**Reprocess** (EDI Manager, přijaté zprávy ve stavu *Received* nebo *Error*)
spustí krok 3 znovu — typicky poté, co jste založili chybějící produkt nebo
doplnili GLN kontaktu.

### Párování produktů {#products}

Řádky přijatých objednávek a avíz se párují na produkty v tomto pořadí:

1. **čárový kód** — v podobě, jak přišel, bez úvodních nul a doplněný na 8,
   12, 13 a 14 číslic, protože partneři se v doplňování EAN neshodují;
2. vlastní kód odesílatele pro produkt (*Kód produktu dodavatele* v řádku
   dodavatele na produktu), je-li odesílatel znám;
3. **interní reference** produktu.

Pokud řádek nespáruje nic, celá přijatá objednávka standardně selže a chyba
vypíše všechny nespárované řádky (EAN, množství, cenu, názvy a kódy) s radou
založit produkty a zprávu znovu zpracovat. Modul
[module:edi_base_sale_pending](module:edi_base_sale_pending) to mění, viz
[čekající řádky](module:edi_base_sale#pending-lines).

## Variabilní symbol {#variable-symbol}

Kde zpráva nese variabilní symbol — bankovní údaje dodavatele v odchozí
INVOIC, hrazená faktura v REMADV — je to symbol, jaký používá český nebo
slovenský platební příkaz: **jen číslice, nejvýše deset**. Je to
*Variabilní symbol* z [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
je-li nainstalován; jinak číslice pole *Payment Reference*, jinak čísla
faktury (u přijaté faktury čísla dodavatele), a ponechá se posledních deset.
Z `INV/2026/00012` vznikne `202600012`. Není-li tam ani jedna číslice, prvek
se vynechá.

## Identita stran EDIFACT (GS1) {#gs1}

Modul [module:edi_base_gs1](module:edi_base_gs1), který se instaluje s
poskytovateli Editel a GRiT, přidává nastavení stran GS1, která potřebuje
EDIFACT, a Peppol ne:

| Kde | Pole | Význam |
|---|---|---|
| Kontakt | Komunikační koncový bod EDI (*EDI Communication Endpoint*) | Kontakt, jehož GLN vlastní schránku EDI; použije se jako odesílatel či adresát obálky, zatímco kupující, příjemce faktury a místo dodání si ponechají vlastní GLN. Nastavte ho na firmě, její kontakty ho zdědí. Prázdné: vlastní GLN kontaktu. |
| Kontakt | DESADV v režimu SSCC (*EDI DESADV in SSCC mode*) | Avíza o expedici pro tohoto odběratele se posílají ve struktuře balení SSCC místo plochého seznamu zboží. Nastavuje se na firmě, kontakty ho zdědí. |
| Sklad (formulář, u adresy) | GLN místa dodání (*EDI GLN (Delivery Point)*) | GLN skladu jako místa dodání v odchozích dokladech a při párování přijatých avíz; je-li prázdné, použije se GLN společnosti. |

## Omezení {#limitations}

- Data a časy v dokladech EDIFACT se čtou a zapisují v časovém pásmu ze
  systémového parametru `edi.timezone` (výchozí `Europe/Bratislava`).
- U dokladů EDIFACT se duplicity rozpoznávají jen podle ID zprávy
  (interchange) a poskytovatele; Peppol přidává odesílatele, příjemce a druh
  dokladu (viz
  [omezení Peppolu](module:edi_base_peppol#limitations)).
- Zprávy nelze z uživatelského rozhraní smazat; právo mazat je nemá nikdo.
