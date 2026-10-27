---
title: Elektronická fakturace Peppol (BIS Billing 3.0)
summary: Odesílá faktury a opravné daňové doklady odběratelům jako elektronické faktury Peppol BIS Billing 3.0, z přijatých elektronických faktur vytváří koncepty přijatých faktur a zpracovává obchodní odpovědi — přes kteréhokoli nainstalovaného poskytovatele EDI.
verified: 19.0.1.7.0
---

## K čemu slouží {#purpose}

**Peppol** je evropská síť pro výměnu elektronických faktur. Firma se do ní
připojuje přes **přístupový bod** (poskytovatele služeb Peppol) a v síti ji
najdou podle její **Peppol adresy** — kódu schématu a identifikátoru. Samotná
faktura je soubor **Peppol BIS Billing 3.0**: XML ve formátu UBL 2.1 podle
evropské normy EN 16931.

Modul řeší vše kolem dokladu a nic kolem přenosu:

- u každé faktury a opravného dokladu odběrateli rozhodne, zda odejde jako
  **elektronická faktura, nebo jako PDF**, a řekne proč
  ([směrování](#routing));
- vytvoří soubor BIS 3.0 vlastním generátorem Odoo a předá ho
  nainstalovanému poskytovateli ([odeslání](#sending));
- ukáže, co se s ním stalo ([stavy](#messages));
- z přijatých elektronických faktur a opravných dokladů vytvoří **koncepty
  přijatých faktur** ([příjem](#receiving));
- zaznamená **odpovědi** odběratelů a umožní odpovídat dodavatelům
  ([odpovědi](#responses)).

Přenos — připojení k přístupovému bodu — zajišťuje modul poskytovatele:

| Přístupový bod | Modul |
|---|---|
| ePošťák | [module:edi_epostak_peppol](module:edi_epostak_peppol) |
| Editel eXite | `edi_editel_peppol` |
| GRiT Orion | `edi_grit_peppol` |

Modul **nepoužívá** službu Peppol od Odoo (`account_peppol`). Je-li
nainstalovaná také, tutéž fakturu nikdy neodešlou obě — viz
[směrování](#routing).

Uživatelské rozhraní je přeloženo do češtiny; anglické názvy polí
a tlačítek uvedené v tomto návodu (v závorce nebo kurzívou) odpovídají
anglické verzi.

## Právní rámec {#legal}

**Česko.** Všeobecná povinnost elektronické fakturace neexistuje. Daňový
doklad má elektronickou podobu, je-li vystaven a obdržen elektronicky, a s
jeho použitím musí souhlasit osoba, pro kterou se plnění uskutečňuje
([§ 26 odst. 3 zákona o DPH](law:cz/2004/235)). Pro tuzemskou výměnu se
často používá národní formát ISDOC, viz
[module:account_edi_isdoc](module:account_edi_isdoc).

**Slovensko.** Pro slovenskou společnost je elektronická fakturace tuzemských
plnení podnikatelům **povinná od 1. ledna 2027** podle § 85o slovenského
[zákona o DPH](law:sk/2004/222#paragraf-85o) ve znění účinném od tohoto
dne; faktura se zasílá doručovací službou certifikovaného poskytovatele
([§ 76a](law:sk/2004/222#paragraf-76a)). Do 31. prosince 2026 vyžaduje
elektronická faktura souhlas příjemce
([§ 71 ods. 1 písm. b)](law:sk/2004/222#paragraf-71.odsek-1.pismeno-b)),
pro rok 2026 s výjimkou faktury zaslané doručovací službou podle § 85o
ods. 21 a 22. Podrobnosti uvádí slovenská a anglická verze tohoto návodu.

**Evropská unie.** Směrnice 2014/55/EU o elektronické fakturaci při zadávání
veřejných zakázek ukládá veřejným zadavatelům přijímat a zpracovávat faktury
podle evropské normy elektronické fakturace (EN 16931) v některé z jejích
syntaxí (čl. 7). Peppol BIS Billing 3.0 je specifikace normy EN 16931 v
syntaxi UBL.

## Nastavení {#setup}

1. **Nainstalujte a připojte poskytovatele.**
2. **Nastavení společnosti.** *Nastavení → EDI*, blok **Peppol BIS3 (this
   company)**. Všechna nastavení patří společnosti, ve které právě pracujete,
   takže slovenská firma může fakturovat elektronicky a její česká sesterská
   ne:

   | Nastavení | Význam |
   |---|---|
   | Povolit e-fakturaci přes Peppol (*Allow e-invoicing via Peppol*) | Povolení, ne rozhodnutí o směrování. Vypnuto: žádná faktura ani opravný doklad této společnosti neodejde přes Peppol, ať je na kontaktu cokoli. Příjmu se to netýká. |
   | Rozsah Peppol (*Peppol scope*) | Pro kontakty bez vlastní volby: **Slovak mandate: domestic B2B and B2G only** (slovenská povinnost) nebo **Any customer with a Peppol address** (každý odběratel s Peppol adresou, výchozí). Viz [směrování](#routing). |
   | Automaticky odeslat při zaúčtování (*Auto-send Peppol on Invoice Post*) | Každý zaúčtovaný doklad směrovaný na Peppol se hned vytvoří a zařadí do fronty. Vypnuto: použijte **Send via Peppol** nebo *Odeslat*. |
   | Nákupní deník pro Peppol (*Peppol Purchase Journal*) | Deník pro přijaté elektronické faktury. Prázdné: první nákupní deník společnosti. |

   **Peppol Transport** v témže bloku (pro celou databázi) určí, který
   poskytovatel přenáší doklady, je-li jich nainstalováno víc. Pak musí být
   nastaven: je-li jich víc a není zvolen žádný, přes Peppol neodejde nic a
   každá faktura ukáže **zablokováno** s tímto důvodem. Při jediném
   poskytovateli na něm nezáleží.
3. **Peppol adresa vaší společnosti.** Na kontaktu společnosti, záložka
   *Fakturace*, skupina *Zákaznické faktury*: **Peppol e-adresa (EAS)** a
   vedle ní koncový bod (*Peppol Endpoint*). České firmě s DIČ Odoo
   předvyplní schéma 9929 (*Czech Republic VAT*) s jejím DIČ; slovenská firma používá
   schéma **0245** se svým **DIČ** — viz
   [slovenský identifikátor Peppol](module:l10n_sk_ubl_bis3#participant).
4. **Peppol adresu každého odběratele a dodavatele** na stejném místě.
5. **Odeslání faktury** na kontaktu (tatáž skupina; Odoo ho mimo režim
   vývojáře skrývá, tento modul ho zobrazí) určuje, jak odběratel faktury
   dostává. Volba **by e-invoice (Peppol)** pošle přes Peppol každou jeho
   fakturu bez ohledu na rozsah.
6. **Přístup.** Tlačítka **Send via Peppol** a **Peppol Response…** vidí
   skupina *EDI User*. Fakturu může odeslat každý, kdo ji smí upravovat:
   zaúčtování se zapnutým automatickým odesíláním i **Odeslat a vytisknout**
   nevyžadují žádnou EDI skupinu, EDI zprávu systém zapíše za uživatele.

## Elektronická faktura, nebo PDF {#routing}

Každá faktura a opravný doklad odběrateli ukazuje, jak odejde: po zaúčtování
štítek v záhlaví formuláře a nahoře v záložce *Další informace* pole
**Sent as** a **Why**.

| Sent as | Význam |
|---|---|
| Peppol e-invoice | odejde přes Peppol |
| PDF | odejde obvyklou cestou (e-mail, tisk); Peppol se neuplatní |
| Peppol, but blocked | měla by jít přes Peppol, ale nemůže: chybí Peppol adresa |

Rozhodnutí v tomto pořadí:

1. Společnost elektronickou fakturaci nepovoluje → **PDF**.
2. **Odeslání faktury** na kontaktu je *by e-invoice (Peppol)* → **Peppol**,
   nebo **zablokováno**, nemá-li vaše společnost či odběratel Peppol adresu.
3. Je to *Peppol* — služba Peppol od Odoo → z pohledu tohoto modulu **PDF**;
   odešle ji služba Odoo, takže faktura nikdy neodejde přes dva přístupové
   body.
4. Je to cokoli jiného, například e-mail → **PDF**.
5. Na kontaktu není nic zvoleno a rozsah je **slovenská povinnost**:
   společnost, jejíž daňovou zemí není Slovensko nebo která nemá DIČ (není
   plátcem), odběratel mimo Slovensko nebo odběratel bez jakéhokoli
   podnikatelského identifikátoru — není firmou a nemá DIČ ani IČO (považuje
   se za spotřebitele) → **PDF**. Živnostník s IČO bez DIČ je podnikatel:
   povinnost se týká každé zdanitelné osoby. Stejně tak faktura, jejíž každý
   řádek je osvobozené plnění (daně jsou osvobozené nebo mimo DPH, viz níže)
   → **PDF**. Česká společnost s tímto rozsahem tedy přes Peppol neposílá nic,
   co není výslovně zvoleno na kontaktu.
6. Vaše společnost nemá Peppol adresu → **zablokováno**. Nemá ji odběratel →
   při slovenské povinnosti **zablokováno**, při *každém odběrateli s Peppol
   adresou* **PDF**.
7. Je nainstalováno více přenosů Peppol a **Peppol Transport** žádný
   neurčuje → **zablokováno**.
8. Jinak → **Peppol**.

Pravidlo slovenské povinnosti sleduje § 85o odst. 2 a 3 slovenského zákona
o DPH tak daleko, jak to údaje kontaktu dovolí: plátce dodávající
zdanitelné osobě (jakémukoli podnikateli, plátci i neplátci) nebo
nezdanitelné právnické osobě se sídlem na Slovensku. Osvobozené plnění (§ 28
až § 43, § 47) vyloučí podle daní faktury: jsou-li daně každého řádku
osvobozené (UBL kategorie *E*) nebo mimo DPH (*O*), jde faktura jako PDF.
Jediný zdanitelný řádek nebo řádek bez daně ji v povinnosti ponechá. Daň pro
přenesení daňové povinnosti, kterou si vytvoříte sami, potřebuje příznak
*Reverse charge* nebo kategorii *AE*, jinak vypadá jako osvobozená. Tuzemské
přenesení daňové povinnosti (§ 69 odst. 12) je zdanitelné plnění a zůstává v
ní, přestože má také 0 %. Místo plnění se nesleduje. Zjednodušené faktury jsou pokladní doklady, které se neodesílají
nikdy. Vychází-li zákon pro některého odběratele jinak, nastavte na jeho
kontaktu **Odeslání faktury**.

## Odeslání {#sending}

Zaúčtovaný doklad směrovaný na Peppol se odešle jedním ze tří způsobů:

- **Automaticky při zaúčtování**, je-li zapnuté *Auto-send Peppol on Invoice
  Post*. Faktura, která by odešla, ale je zablokovaná, dostane v historii
  řádek „Not sent via Peppol: …“ s důvodem; faktura, jejíž soubor neprojde
  kontrolami Odoo, dostane stejný řádek s chybami a aktivitu *Peppol
  e-invoice not sent* pro svého obchodníka. Faktura zůstane zaúčtovaná.
- Tlačítkem **Send via Peppol** v záhlaví formuláře.
- Tlačítkem **Odeslat** (dialog Odoo pro odeslání). Způsob **by e-invoice
  (Peppol)** je nabídnut a zaškrtnut; nemá-li kontakt zvolené *Odeslání
  faktury*, nahradí výchozí e-mail a způsob služby Peppol od Odoo se
  odškrtne. Selhání se ukáže v dialogu jako „The e-invoice could not be
  sent“. Doklad, který je už ve frontě nebo odeslaný, se přeskočí.

Odeslání vytvoří soubor BIS 3.0 generátorem podle **formátu e-faktury**
odběratele, jde-li o formát Peppol, jinak podle formátu, který Odoo pro
odběratele navrhne. Pokud kontroly pravidel EN 16931 a Peppol v Odoo selžou,
nic se neodešle a chyby se vypíšou. Jinak vznikne odchozí EDI zpráva se
souborem, zařadí se do fronty poskytovatele a do historie se zapíše řádek
„Invoice sent via Peppol: … (queued)“.

Každý doklad má **jednu** odchozí zprávu. Opětovné odeslání ji použije znovu
s nově vytvořeným souborem, přes přenos a v testovacím či produkčním režimu
platném **nyní** — doklad, který jste nejprve zkoušeli v testovacím
prostředí, po přepnutí odejde do produkce. Dokud je zpráva ve stavu *Queued*
nebo *Sent*, opětovné odeslání se odmítne („already being sent“), a také
když je v produkci *Done* („already delivered“): doručená faktura se opravuje
opravným daňovým dokladem, ne druhým odesláním.

## Stavy {#messages}

Na faktuře:

| Pole | Ukazuje |
|---|---|
| Peppol Status | stav poslední odchozí zprávy: *Ready*, *Queued*, *Sent*, *Error*, *Done* (viz [stavy](module:edi_base#states)) |
| Peppol Delivery Response | poslední odpověď sítě na úrovni zprávy (MLR) ve tvaru „kód — popis“ |
| Peppol Invoice Response | poslední obchodní odpověď odběratele, například *Accepted* nebo *Rejected* |
| Peppol Response Reason | důvod, který k ní odběratel uvedl |
| Peppol Response Sent | na přijaté faktuře: poslední odpověď, kterou jste poslali dodavateli |

Uživatelé účetnictví vidí tyto štítky i bez skupiny EDI. Členové skupin EDI
mají navíc záložku **Peppol Messages** se všemi zprávami dokladu —
elektronickou fakturou, přijatými a odeslanými odpověďmi — a každá zpráva
odkazuje zpět přes pole **Peppol Document**.

Co dokazují *Sent* a *Done*, závisí na přístupovém bodu: u některých
poskytovatelů je *Sent* jen převzetí k přenosu a teprve *Done* doručení do
přístupového bodu příjemce.

## Příjem elektronických faktur {#receiving}

Poskytovatel vyzvedává doklady adresované na vaši Peppol adresu (společné
kroky viz [příjem](module:edi_base#receiving)). U faktury nebo opravného
dokladu Peppol:

- vznikne **koncept přijaté faktury** — z opravného dokladu přijatý opravný
  doklad — v *nákupním deníku pro Peppol* nebo v prvním nákupním deníku
  společnosti; dodavatele, řádky, daně a částky vyplní standardní import UBL
  v Odoo;
- soubor XML se přiloží k faktuře;
- faktura se **nikdy nezaúčtuje automaticky**; zkontrolujte ji jako každou
  jinou;
- dodavatel se rozpozná podle Peppol koncového bodu a zpráva přejde do stavu
  *Done*. Nelze-li fakturu vytvořit, zpráva přejde do stavu *Error* a soubor
  si ponechá; odstraňte příčinu a stiskněte **Reprocess**.

Již přijatý doklad se přeskočí (a potvrdí se, takže ho poskytovatel přestane
doručovat) jen tehdy, když se s uloženou zprávou shoduje jeho číslo, druh
(faktura, opravný doklad, odpověď), koncový bod odesílatele i koncový bod
příjemce. Faktury dvou dodavatelů se stejným číslem, faktura a opravný
doklad se stejným číslem nebo faktury jednoho dodavatele dvěma vašim
společnostem jsou proto samostatné doklady. Doklad, u kterého nelze přečíst
koncový bod odesílatele, se uloží vždy.

## Obchodní odpovědi {#responses}

Peppol přenáší dva druhy odpovědí, obě jako doklad *ApplicationResponse*:

- **odpověď na úrovni zprávy (MLR)** — technická: zda přijímající systém
  soubor přijal;
- **odpověď na fakturu** (*Invoice Response*) — obchodní: co s fakturou dělá
  kupující.

Kódy stavů:

| Kód | Význam |
|---|---|
| AB | Acknowledged — přijato |
| IP | In process — ve zpracování |
| UQ | Under query — sporné, čeká se na odpověď |
| CA | Conditionally accepted — podmíněně přijato |
| AP | Accepted — přijato |
| RE | Rejected — odmítnuto |
| PD | Paid — zaplaceno |

**Odpovědi odběratelů.** Přijatá odpověď se spáruje s vaší fakturou nebo
opravným dokladem podle čísla dokladu, na který odkazuje, v rámci téže
společnosti. MLR vyplní *Peppol Delivery Response*; odpověď na fakturu
vyplní *Peppol Invoice Response* a *Peppol Response Reason*; obě zapíšou
řádek do historie. Odpověď na doklad, který Odoo nezná, se uloží jako zpráva,
označí se za vyřízenou a s ničím se nepropojí.

**Vaše odpověď dodavateli.** Na přijaté faktuře, která přišla přes Peppol
(obě strany mají Peppol adresu), otevře **Peppol Response…** dialog:

| Pole | Účel |
|---|---|
| Response | kód stavu z tabulky; výchozí *Rejected* |
| Reasons | kódované důvody, např. *PRI — Prices incorrect*, *QTY — Quantity incorrect*, *REF — References incorrect* |
| Requested actions | co má dodavatel udělat, např. *NCR — Issue a credit note*, *NIN — Issue a new invoice*, *PIN — Provide additional information* |
| Note | volný text pro dodavatele |

U *Rejected*, *Under query* a *Conditionally accepted* je důvod nebo
poznámka povinná. Odpověď odejde přes poskytovatele, faktura ukáže **Peppol
Response Sent** a historie ji zaznamená. Nic se neposílá automaticky — při
zaúčtování ani úhradě faktury žádná odpověď nevznikne.

## Omezení {#limitations}

- Přijatý doklad, u kterého nelze přečíst koncový bod odesílatele, se uloží
  při každém doručení, takže jeho opětovné doručení se objeví jako druhá
  zpráva.
- Pravidlo slovenské povinnosti je přiblížením (viz
  [směrování](#routing)).
- Odesílají se jen faktury a opravné doklady odběratelům. Přijaté
  elektronické faktury jsou koncepty; Odoo na ně neodpovídá zprávou MLR.
- Jeden přenos Peppol slouží celé databázi; nemůže se lišit podle
  společnosti.
