---
title: Elektronická fakturácia Peppol (BIS Billing 3.0)
summary: Odosiela faktúry a dobropisy odberateľom ako elektronické faktúry Peppol BIS Billing 3.0, z prijatých elektronických faktúr vytvára koncepty dodávateľských faktúr a spracúva obchodné odpovede — cez ktoréhokoľvek nainštalovaného poskytovateľa EDI.
verified: 19.0.1.6.0
---

## Na čo slúži {#purpose}

**Peppol** je európska sieť na výmenu elektronických faktúr. Firma sa do nej
pripája cez **prístupový bod** (poskytovateľa služieb Peppol) a v sieti ju
nájdu podľa jej **Peppol adresy** — kódu schémy a identifikátora, napríklad
`0245:2020123456` pre slovenskú firmu identifikovanú podľa DIČ. Samotná
faktúra je súbor **Peppol BIS Billing 3.0**: XML vo formáte UBL 2.1 podľa
európskej normy EN 16931.

Modul rieši všetko okolo dokladu a nič okolo prenosu:

- pri každej faktúre a dobropise odberateľovi rozhodne, či odíde ako
  **elektronická faktúra, alebo ako PDF**, a povie prečo
  ([smerovanie](#routing));
- vytvorí súbor BIS 3.0 vlastným generátorom Odoo a odovzdá ho
  nainštalovanému poskytovateľovi ([odoslanie](#sending));
- ukáže, čo sa s ním stalo ([stavy](#messages));
- z prijatých elektronických faktúr a dobropisov vytvorí **koncepty
  dodávateľských faktúr** ([prijímanie](#receiving));
- zaznamená **odpovede** odberateľov a umožní odpovedať dodávateľom
  ([odpovede](#responses)).

Prenos — pripojenie k prístupovému bodu — zabezpečuje modul poskytovateľa:

| Prístupový bod | Modul |
|---|---|
| ePošťák | [module:edi_epostak_peppol](module:edi_epostak_peppol) |
| Editel eXite | `edi_editel_peppol` |
| GRiT Orion | `edi_grit_peppol` |

Modul **nepoužíva** službu Peppol od Odoo (`account_peppol`). Ak je
nainštalovaná tiež, tú istú faktúru nikdy neodošlú obe — pozri
[smerovanie](#routing).

Pre slovenské faktúry nainštalujte aj
[module:l10n_sk_ubl_bis3](module:l10n_sk_ubl_bis3). Ten identifikuje
slovenské subjekty podľa DIČ a zapíše variabilný symbol do súboru tam, kde ho
hľadá banka platiteľa; tento modul jeho generátor použije automaticky.

## Právny rámec {#legal}

**Slovensko.** Všetky odkazy sú na [zákon o DPH](law:sk/2004/222).

- **Do 31. decembra 2026** možno elektronickú faktúru vydať len so súhlasom
  príjemcu —
  [§ 71 ods. 1 písm. b)](law:sk/2004/222#paragraf-71.odsek-1.pismeno-b).
  Len pre rok 2026 [§ 85o ods. 21 a 22](law:sk/2004/222#paragraf-85o.odsek-22)
  súhlas nevyžadujú pri faktúre v dátovej štruktúre podľa európskej normy,
  ktorú platiteľ zasiela **doručovacou službou** tuzemskej zdaniteľnej osobe
  (alebo nezdaniteľnej právnickej osobe so sídlom v tuzemsku), ktorá si
  zabezpečila, že ju doručovacou službou prijme — okrem plnení oslobodených
  podľa § 28 až 43 a 47 a zjednodušených faktúr.
- **Od 1. januára 2027** je elektronická fakturácia **povinná**. Podľa § 85o
  ods. 2 a 3 v znení účinnom od toho dňa platiteľ, ktorý dodá tovar alebo
  službu s miestom dodania v tuzemsku zdaniteľnej osobe so sídlom, miestom
  podnikania, prevádzkarňou alebo bydliskom v tuzemsku alebo nezdaniteľnej
  právnickej osobe so sídlom v tuzemsku, alebo prijme platbu pred takým
  dodaním, je povinný vyhotoviť elektronickú faktúru; neplatí to pri
  plneniach oslobodených podľa § 28 až 43 a 47 a pri zjednodušenej faktúre.
  Vyhotovenie nepodlieha súhlasu príjemcu, zaslanie inak než doručovacou
  službou áno. Elektronickou faktúrou je podľa ods. 4 doklad s náležitosťami
  podľa § 74 ods. 1 vo formáte umožňujúcom automatizované spracovanie a v
  dátovej štruktúre podľa technickej normy pre elektronickú fakturáciu. Doklad,
  ktorý ju mení, musí byť tiež elektronickou faktúrou, uvádzať poradové číslo
  pôvodnej faktúry a ísť rovnakou cestou (ods. 5); lehota na vyhotovenie je
  pätnásť dní (ods. 6). Údaje z faktúry sa oznamujú finančnému riaditeľstvu
  prostredníctvom doručovacej služby a povinnosť je splnená odovzdaním faktúry
  doručovacej službe (ods. 9 až 11). Elektronické faktúry sa uchovávajú desať
  rokov (ods. 15). Tá istá novela dopĺňa **§ 71 ods. 5**: kto je povinný
  vyhotovovať elektronické faktúry, musí ich vedieť zaslať aj prijať
  doručovacou službou, a každý tuzemský príjemca takých plnení ich musí vedieť
  doručovacou službou prijať. Dnes platné úplné znenie tieto ustanovenia ešte
  neobsahuje; odkaz vedie na [§ 85o](law:sk/2004/222#paragraf-85o) v
  súčasnom znení. Podľa § 85o ods. 1 je tento režim prechodný, od
  1. januára 2027 do 30. júna 2030.
- **Doručovaciu službu** poskytuje certifikovaný poskytovateľ zapísaný v
  evidencii, ktorú vedie finančné riaditeľstvo
  ([§ 76a](law:sk/2004/222#paragraf-76a)). Či je ním váš prístupový bod,
  musí potvrdiť poskytovateľ, nie Odoo.

**Česko.** Všeobecná povinnosť elektronickej fakturácie neexistuje; daňový
doklad môže mať elektronickú podobu len so súhlasom odberateľa
([§ 26 odst. 3 zákona o DPH](law:cz/2004/235)). Český národný formát ISDOC
opisuje [module:account_edi_isdoc](module:account_edi_isdoc).

**Európska únia.** Smernica 2014/55/EÚ o elektronickej fakturácii vo verejnom
obstarávaní ukladá verejným obstarávateľom prijímať a spracúvať faktúry podľa
európskej normy elektronickej fakturácie (EN 16931) v niektorej z jej
syntaxí (čl. 7). Peppol BIS Billing 3.0 je špecifikácia normy EN 16931 v
syntaxi UBL.

## Nastavenie {#setup}

1. **Nainštalujte a pripojte poskytovateľa**, napríklad
   [ePošťák](module:edi_epostak_peppol#setup).
2. **Nastavenia spoločnosti.** *Nastavenia → EDI*, blok **Peppol BIS3 (táto
   firma)**. Všetky nastavenia patria spoločnosti, v ktorej práve pracujete,
   takže slovenská firma môže fakturovať elektronicky a jej česká sesterská
   nie:

   | Nastavenie | Význam |
   |---|---|
   | Povoliť e-fakturáciu cez Peppol | Povolenie, nie rozhodnutie o smerovaní. Vypnuté: žiadna faktúra ani dobropis tejto spoločnosti neodíde cez Peppol, nech je na kontakte čokoľvek. Prijímanie sa to netýka. |
   | Rozsah Peppol | Pre kontakty bez vlastnej voľby: **Slovenská povinnosť: len domáce B2B a B2G** alebo **Každý odberateľ s Peppol adresou** (predvolené). Pozri [smerovanie](#routing). |
   | Automaticky odoslať cez Peppol pri zaúčtovaní faktúry | Každý zaúčtovaný doklad smerovaný na Peppol sa hneď vytvorí a zaradí do frontu. Vypnuté: použite **Odoslať cez Peppol** alebo *Poslať*. |
   | Nákupný denník pre Peppol | Denník pre prijaté elektronické faktúry. Prázdne: prvý nákupný denník spoločnosti. |

   **Peppol Transport** v tom istom bloku (pre celú databázu) určí, ktorý
   poskytovateľ prenáša doklady, ak je nainštalovaných viac. Vtedy musí byť
   nastavený: ak je ich viac a nie je zvolený žiadny, cez Peppol neodíde
   nič a každá faktúra ukáže **zablokované** s týmto dôvodom. Pri jedinom
   poskytovateľovi na ňom nezáleží.
3. **Peppol adresa vašej spoločnosti.** Na kontakte spoločnosti, záložka
   *Fakturácia*, skupina *Zákaznícke faktúry*: **Peppol e-adresa (EAS)** a
   vedľa nej koncový bod. Slovenská firma používa schému **0245** so svojím
   **DIČ** (desať číslic) — nie IČ DPH (schéma 9950) a nie IČO; pozri
   [slovenský identifikátor Peppol](module:l10n_sk_ubl_bis3#participant).
4. **Peppol adresu každého odberateľa a dodávateľa** na rovnakom mieste.
5. **Odosielanie faktúr** na kontakte (tá istá skupina; Odoo ho mimo režimu
   vývojára skrýva, tento modul ho zobrazí) určuje, ako odberateľ faktúry
   dostáva. Voľba **elektronickou faktúrou (Peppol)** pošle cez Peppol každú
   jeho faktúru bez ohľadu na rozsah. Ak spoločnosť pracuje podľa slovenskej
   povinnosti a slovenská firma má nastavené niečo iné, kontakt zobrazí
   upozornenie, že od 1. 1. 2027 musia byť jej faktúry elektronické.
6. **Prístup.** Tlačidlá **Odoslať cez Peppol** a **Peppol odpoveď…** vidí
   skupina *EDI User*. Faktúru môže odoslať každý, kto ju smie upravovať:
   zaúčtovanie so zapnutým automatickým odosielaním aj **Odoslať a tlačiť**
   nevyžadujú žiadnu EDI skupinu, EDI správu systém zapíše za používateľa.

## Elektronická faktúra alebo PDF {#routing}

Každá faktúra a dobropis odberateľovi ukazuje, ako odíde: po zaúčtovaní
odznak v hlavičke formulára a hore v záložke *Ďalšie info* polia **Odoslané
ako** a **Dôvod**.

| Odoslané ako | Význam |
|---|---|
| Peppol e-faktúra | odíde cez Peppol |
| PDF | odíde obvyklou cestou (e-mail, tlač); Peppol sa neuplatní |
| Peppol, ale zablokované | mala by ísť cez Peppol, ale nemôže: chýba Peppol adresa |

Rozhodnutie v tomto poradí:

1. Spoločnosť elektronickú fakturáciu nepovoľuje → **PDF**.
2. **Odosielanie faktúr** na kontakte je *elektronickou faktúrou (Peppol)* →
   **Peppol**, alebo **zablokované**, ak vaša spoločnosť či odberateľ nemá
   Peppol adresu.
3. Je to *Peppol* — služba Peppol od Odoo → z pohľadu tohto modulu **PDF**;
   odošle ju služba Odoo, takže faktúra nikdy neodíde cez dva prístupové body.
4. Je to čokoľvek iné, napríklad *e-mailom* → **PDF**.
5. Na kontakte nie je nič zvolené a rozsah je **slovenská povinnosť**:
   spoločnosť, ktorej daňová krajina nie je Slovensko alebo ktorá nemá IČ DPH
   (nie je platiteľom), odberateľ mimo Slovenska alebo odberateľ bez
   akéhokoľvek podnikateľského identifikátora — nie je firmou a nemá IČ DPH,
   IČO ani DIČ (považuje sa za spotrebiteľa) → **PDF**. Živnostník s IČO
   bez IČ DPH je podnikateľ: povinnosť sa týka každej zdaniteľnej osoby.
6. Vaša spoločnosť nemá Peppol adresu → **zablokované**. Nemá ju odberateľ →
   pri slovenskej povinnosti **zablokované**, pri *každom odberateľovi s
   Peppol adresou* **PDF**.
7. Je nainštalovaných viac prenosov Peppol a **Peppol Transport** žiadny
   neurčuje → **zablokované**.
8. Inak → **Peppol**.

Pravidlo slovenskej povinnosti sleduje § 85o ods. 2 a 3 tak ďaleko, ako to
údaje kontaktu dovolia: platiteľ dodávajúci zdaniteľnej osobe (akémukoľvek
podnikateľovi, platiteľovi DPH aj neplatiteľovi) alebo nezdaniteľnej
právnickej osobe so sídlom na Slovensku. Nesleduje miesto dodania ani dane
faktúry, takže oslobodené plnenie (§ 28 až § 43, § 47) slovenskému
podnikateľovi sa smeruje na Peppol ako každé iné — je to dovolené, hoci nie
povinné. Zjednodušené faktúry sú pokladničné doklady, ktoré sa neodosielajú
nikdy. Ak zákon pre niektorého odberateľa vychádza inak, nastavte na jeho
kontakte **Odosielanie faktúr**.

## Odoslanie {#sending}

Zaúčtovaný doklad smerovaný na Peppol sa odošle jedným z troch spôsobov:

- **Automaticky pri zaúčtovaní**, ak je zapnuté *Automaticky odoslať cez
  Peppol pri zaúčtovaní faktúry*. Faktúra, ktorá by odišla, ale je
  zablokovaná, dostane v histórii riadok „Neodoslané cez Peppol: …“ s dôvodom;
  faktúra, ktorej súbor neprejde kontrolami Odoo, dostane rovnaký riadok
  s chybami a aktivitu *Peppol e-invoice not sent* pre svojho obchodníka.
  Faktúra zostane zaúčtovaná.
- Tlačidlom **Odoslať cez Peppol** v hlavičke formulára.
- Tlačidlom **Poslať** (dialóg Odoo na odoslanie). Spôsob **elektronickou
  faktúrou (Peppol)** je ponúknutý a zaškrtnutý; ak kontakt nemá zvolené
  *Odosielanie faktúr*, nahradí predvolený e-mail a spôsob služby Peppol od
  Odoo sa odškrtne. Zlyhanie sa ukáže v dialógu ako „Elektronickú faktúru sa
  nepodarilo odoslať“. Doklad, ktorý je už vo fronte alebo odoslaný, sa
  preskočí.

Odoslanie vytvorí súbor BIS 3.0 generátorom podľa **formátu e-faktúry**
odberateľa, ak ide o formát Peppol, inak podľa formátu, ktorý Odoo pre
odberateľa navrhne — pre slovenského odberateľa s nainštalovaným modulom
[module:l10n_sk_ubl_bis3](module:l10n_sk_ubl_bis3) slovenským. Ak kontroly
pravidiel EN 16931 a Peppol v Odoo zlyhajú, nič sa neodošle a chyby sa
vypíšu. Inak vznikne odchádzajúca EDI správa so súborom, zaradí sa do frontu
poskytovateľa a do histórie sa zapíše riadok „Invoice odoslané cez Peppol:
… (vo fronte)“.

Každý doklad má **jednu** odchádzajúcu správu. Opätovné odoslanie ju použije
znova s novo vytvoreným súborom, cez prenos a v testovacom či produkčnom
režime platnom **teraz** — doklad, ktorý ste najprv skúšali v testovacom
prostredí, po prepnutí odíde do produkcie. Kým je správa v stave *Queued*
alebo *Sent*, opätovné odoslanie sa odmietne („already being sent“), a tiež
keď je v produkcii *Done* („already delivered“): doručená faktúra sa opravuje
dobropisom, nie druhým odoslaním.

## Stavy {#messages}

Na faktúre:

| Pole | Ukazuje |
|---|---|
| Peppol stav | stav poslednej odchádzajúcej správy: *Ready*, *Queued*, *Sent*, *Error*, *Done* (pozri [stavy](module:edi_base#states)) |
| Peppol odpoveď o doručení | poslednú odpoveď siete na úrovni správy (MLR) v tvare „kód — popis“ |
| Peppol odpoveď na faktúru | poslednú obchodnú odpoveď odberateľa, napríklad *Akceptované* alebo *Zamietnuté* |
| Dôvod Peppol odpovede | dôvod, ktorý k nej odberateľ uviedol |
| Odoslaná Peppol odpoveď | na dodávateľskej faktúre: poslednú odpoveď, ktorú ste poslali dodávateľovi |

Používatelia účtovníctva vidia tieto odznaky aj bez skupiny EDI. Členovia
skupín EDI majú navyše záložku **Peppol EDI správy** so všetkými správami
dokladu — elektronickou faktúrou, prijatými a odoslanými odpoveďami — a
každá správa odkazuje späť cez pole **Peppol doklad**.

Čo dokazujú *Sent* a *Done*, závisí od prístupového bodu. Pri ePošťáku je
*Sent* prevzatie na prenos a *Done* doručenie do prístupového bodu príjemcu —
pozri [stav doručenia](module:edi_epostak_peppol#statuses).

## Prijímanie elektronických faktúr {#receiving}

Poskytovateľ vyzdvihuje doklady adresované na vašu Peppol adresu (spoločné
kroky pozri v [prijímaní](module:edi_base#receiving)). Pri faktúre alebo
dobropise Peppol:

- vznikne **koncept dodávateľskej faktúry** — z dobropisu dodávateľský
  dobropis — v *Nákupnom denníku pre Peppol* alebo v prvom nákupnom denníku
  spoločnosti; dodávateľa, riadky, dane a sumy vyplní štandardný import UBL
  v Odoo;
- súbor XML sa priloží k faktúre;
- faktúra sa **nikdy nezaúčtuje automaticky**; skontrolujte ju ako každú inú;
- dodávateľ sa rozpozná podľa Peppol koncového bodu a správa prejde do stavu
  *Done*. Ak faktúru nemožno vytvoriť, správa prejde do stavu *Error* a súbor
  si ponechá; odstráňte príčinu a stlačte **Reprocess**.

Už prijatý doklad sa preskočí (a potvrdí sa, takže ho poskytovateľ prestane
doručovať) len vtedy, keď sa s uloženou správou zhoduje jeho číslo, druh
(faktúra, dobropis, odpoveď), koncový bod odosielateľa aj koncový bod
príjemcu. Faktúry dvoch dodávateľov s rovnakým číslom, faktúra a dobropis s
rovnakým číslom či faktúry jedného dodávateľa dvom vašim spoločnostiam sú
preto samostatné doklady. Doklad, pri ktorom sa nedá prečítať koncový bod
odosielateľa, sa uloží vždy.

## Obchodné odpovede {#responses}

Peppol prenáša dva druhy odpovedí, obe ako doklad *ApplicationResponse*:

- **odpoveď na úrovni správy (MLR)** — technická: či prijímajúci systém súbor
  prijal;
- **odpoveď na faktúru** (*Invoice Response*) — obchodná: čo s faktúrou robí
  kupujúci.

Kódy stavov:

| Kód | Význam |
|---|---|
| AB | Potvrdené prijatie |
| IP | V spracovaní |
| UQ | Sporné — čaká sa na odpoveď |
| CA | Podmienečne akceptované |
| AP | Akceptované |
| RE | Zamietnuté |
| PD | Zaplatené |

**Odpovede odberateľov.** Prijatá odpoveď sa spáruje s vašou faktúrou alebo
dobropisom podľa čísla dokladu, na ktorý odkazuje, v rámci tej istej
spoločnosti. MLR vyplní *Peppol odpoveď o doručení*; odpoveď na faktúru
vyplní *Peppol odpoveď na faktúru* a *Dôvod Peppol odpovede*; obe zapíšu
riadok do histórie. Odpoveď na doklad, ktorý Odoo nepozná, sa uloží ako
správa, označí sa za vybavenú a s ničím sa neprepojí.

**Vaša odpoveď dodávateľovi.** Na dodávateľskej faktúre, ktorá prišla cez
Peppol (obe strany majú Peppol adresu), otvorí **Peppol odpoveď…** dialóg:

| Pole | Účel |
|---|---|
| Odpoveď | kód stavu z tabuľky; predvolené *Zamietnuté* |
| Dôvody | kódované dôvody, napr. *PRI — Prices incorrect*, *QTY — Quantity incorrect*, *REF — References incorrect* |
| Požadované akcie | čo má dodávateľ urobiť, napr. *NCR — Issue a credit note*, *NIN — Issue a new invoice*, *PIN — Provide additional information* |
| Poznámka | voľný text pre dodávateľa |

Pri *Zamietnuté*, *Sporné* a *Podmienečne akceptované* je dôvod alebo
poznámka povinná. Odpoveď odíde cez poskytovateľa, faktúra ukáže **Odoslaná
Peppol odpoveď** a história ju zaznamená. Nič sa neposiela automaticky — pri
zaúčtovaní ani úhrade faktúry žiadna odpoveď nevznikne.

## Obmedzenia {#limitations}

- Prijatý doklad, pri ktorom sa nedá prečítať koncový bod odosielateľa, sa
  uloží pri každom doručení, takže jeho opätovné doručenie sa objaví ako druhá
  správa.
- Pravidlo slovenskej povinnosti je priblížením (pozri
  [smerovanie](#routing)).
- Odosielajú sa len faktúry a dobropisy odberateľom. Prijaté elektronické
  faktúry sú koncepty; Odoo na ne neodpovedá správou MLR.
- Jeden prenos Peppol slúži celej databáze; nemôže sa líšiť podľa
  spoločnosti.
