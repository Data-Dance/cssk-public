---
title: Daňové priznanie k DPH CZ/SK — spoločný základ
summary: Obrazovky a postup, na ktorých stojí slovenské aj české daňové priznanie k DPH — výpočet riadkov z daňových značiek, kontrola voči účtovným zápisom, export úradného XML a uchovanie podanej verzie.
verified: 19.0.1.11.1
---

## Na čo slúži {#purpose}

Modul je spoločným jadrom daňového priznania k DPH (na Slovensku *daňové
priznanie k DPH*, v Česku *přiznání k DPH*). Sám osebe nič nepodáva: samotné
tlačivo — jeho riadky, úradnú XSD schému a pravidlá krajiny — dodáva modul
[module:l10n_sk_vat_return](module:l10n_sk_vat_return) alebo
[module:l10n_cz_vat_return](module:l10n_cz_vat_return). Tento modul pridáva
všetko, čo majú obe krajiny spoločné:

- obrazovku **Daňové priznanie k DPH**, kde sa priznanie zakladá, počíta,
  kontroluje, exportuje a označuje ako podané;
- **verzie tlačiva** (vzory), ktoré určujú, aké riadky, aká XML šablóna a aká
  XSD schéma platia pre ktoré obdobia;
- výpočet, ktorý sčíta zaúčtované položky podľa **daňových značiek**, takže
  funguje rovnako v edícii Community aj Enterprise bez výkazového nástroja
  Odoo;
- preklik z každého riadku na účtovné zápisy, z ktorých vznikol;
- uchovanie podanej verzie, dodatočné a opravné priznania a historické sadzby
  dane pre import starších dokladov.

## Pred prvým priznaním {#setup}

- **Spoločnosť** musí mať vyplnené IČ DPH (v poli *DIČ*) — bez neho export
  neprebehne — a svoj daňový úrad: *Účtovníctvo → Konfigurácia → Nastavenia*,
  pole **Daňový úrad**, prípadne to isté pole na karte spoločnosti.
- **Modul krajiny** musí byť nainštalovaný. Prináša verzie tlačiva, bez ktorých
  sa nedá nič vypočítať.
- **Prístupové práva.** Účtovník môže priznania zakladať, počítať a
  exportovať. Upravovať verzie tlačiva a **vrátiť podané priznanie do
  návrhu** môže len administrátor účtovníctva.

## Príprava priznania {#usage}

*Účtovníctvo → Výkazy → Zákonné výkazy → Daňové priznanie k DPH*, potom
*Nové*.

| Pole | Čo vyplniť |
|---|---|
| Spoločnosť | Spoločnosť, za ktorú sa podáva (predvolená je aktuálna). |
| Dátum od / Dátum do | Prvý a posledný deň zdaňovacieho obdobia. |
| Typ obdobia | *Mesačne* alebo *Štvrťročne* — do XML sa zapíše mesiac alebo štvrťrok podľa *Dátumu od*. |
| Verzia | Vzor tlačiva. Ponúkajú sa len verzie krajiny spoločnosti platné v danom období, pozri [Verzie tlačiva](#versions). |
| Typ výkazu | Riadne, opravné alebo dodatočné — možnosti určuje verzia. |

Potom kliknite na **Vypočítať**. Priznanie prejde do stavu *Náhľad* a karta
**Riadky** sa naplní riadkami tlačiva.

**Ktoré doklady patria do obdobia.** Obe strany priznania sa datujú inak, tak
ako ich datuje zákon:

- **Faktúry a dobropisy odberateľom** sa zahrnú do obdobia podľa **dňa
  dodania** (*Dátum zdaniteľného plnenia*); ak ho nemajú, rozhoduje dátum
  účtovania.
- **Prijaté faktúry a ostatné doklady** sa zahrnú podľa **dátumu účtovania**,
  lebo to je obvyklé obdobie uplatnenia odpočtu. Interný doklad s dňom dodania
  sa riadi týmto dňom.
- Ak má doklad vyplnené **Deklarované obdobie DPH** (pole jadra lokalizácie),
  rozhoduje toto pole na oboch stranách — pri odpočte uplatnenom neskôr, ako
  bolo dodanie, alebo pri oprave vykázanej v období, keď opravný doklad prišiel.

Čítajú sa len zaúčtované zápisy s daňovými značkami.

## Kontrola riadkov {#lines}

Každý riadok má kód (kód tlačiva, napr. `r03` alebo `obrat23`), názov a
**Hodnotu**. Riadok je jedného z troch druhov:

- **daňové značky** — súčet zostatkov účtovných položiek so značkami riadku so
  znamienkom. Stĺpec ✓ ukazuje, či preklik dáva rovnakú sumu, a **Doklady**
  otvorí tieto položky zoskupené podľa dokladu;
- **súhrn** — vzorec nad inými riadkami (zobrazený sivou, vzorec je v stĺpci
  *Odvodenie*);
- **ručne** — údaj, ktorý účtovníctvo nevie dodať (prenášaný nadmerný odpočet,
  koeficient, rozdiel oproti predchádzajúcemu priznaniu). Kým ho nezadáte, je
  nulový.

Ak chcete údaj zadať alebo opraviť, zapnite na riadku **Prepis**, vpíšte
**Ručnú hodnotu** a znova stlačte **Vypočítať**. Prepísané riadky sú
zvýraznené, pri každom prepočte si hodnotu ponechajú a vstupujú do súhrnných
riadkov, ktoré od nich závisia.

V hlavičke sa zobrazí **Riadky súhlasia**, ak sa každý riadok zo značiek zhoduje
so svojimi položkami, inak červené tlačidlo **Nesúladné riadky** so zoznamom
tých, ktoré sa nezhodujú. Riadok, ktorý berie len svoj podiel značky
(rozdelenie špecifické pre krajinu, napr. slovenské riadky § 69 ods. 3 pred
rokom 2021), sa preklikne a porovná len s týmto podielom.

## Vysporiadanie a nadmerný odpočet {#settlement}

Záložka **Vysporiadanie** sleduje nadmerný odpočet z jedného obdobia do
ďalšieho:

| Pole | Význam |
|---|---|
| Predchádzajúce obdobie | Priznanie predchádzajúceho obdobia. |
| Nadmerný odpočet z predchádzajúceho obdobia | Čo predchádzajúce priznanie prenieslo; **Preniesť nadmerný odpočet** ho (aj *Predchádzajúce obdobie*) z neho doplní. |
| Nadmerný odpočet na prenos | Časť nadmerného odpočtu tohto obdobia, ktorú si nedáte vrátiť; nesmie prevýšiť nadmerný odpočet obdobia. |
| Na úhradu / (vrátenie) | Vlastná daňová povinnosť − nadmerný odpočet − prenesené z minula + prenesené ďalej; kladná suma je daň na úhradu, záporná vrátenie. |

Polia možno meniť, kým je priznanie v koncepte alebo náhľade. Ktoré riadky
sú vlastná daňová povinnosť a nadmerný odpočet, určuje verzia tlačiva danej
krajiny; záložka žiadny riadok tlačiva nemení.

## Export XML {#export}

**Exportovať XML** (v stave *Náhľad* alebo *Exportované*) vykoná v tomto
poradí:

1. kontrolu, či má spoločnosť IČ DPH;
2. obsahové kontroly, ktoré definuje modul krajiny (kontrolné pravidlá);
   chyba export zastaví a pomenuje porušené pravidlo;
3. vygenerovanie XML podľa šablóny verzie;
4. overenie voči úradnej XSD schéme verzie. Verzia bez schémy export odmietne,
   namiesto toho, aby vytvorila neoverený súbor.

Súbor sa priloží k priznaniu (*XML príloha*) a priznanie prejde do stavu
*Exportované*. Prepočítať a exportovať ho môžete opakovane, kým ho neoznačíte
ako podané.

## Podanie a podaná verzia {#submission}

XML podajte na portáli finančnej správy alebo cez modul podacieho kanála. Potom:

- **Označiť ako podané** zmrazí exportované XML ako podanú verziu, pridá ho do
  **Histórie podaní**, zaznamená dátum a pridá poznámku do chatteru. Zároveň
  založí záznam o doručení v stave návrh — miesto pre potvrdenie z portálu.
  Jeho stav ukazuje hlavička v poli **Doručenie**.
- **Podať** otvorí (alebo založí) tento záznam o doručení. Ak je
  nainštalovaných viac kanálov, vyberiete si; ak len ručný kanál, zaznamená,
  kto priznanie podal na portáli, a uchová potvrdenia.
- Podané priznanie je zamknuté: nedá sa prepočítať, znova exportovať ani
  zmazať. **Vrátiť do návrhu** (len administrátor) ho znova otvorí; podaná
  verzia a história zostanú zachované.

## Opravné a dodatočné priznanie {#amendments}

Na podanom priznaní tlačidlo **Dodatočné / opravné** založí nový návrh
prepojený s pôvodným (*Opravuje*) a prenesie doň ručné prepisy. Na novom
priznaní:

1. zvoľte správny **Typ výkazu** — kópia začína typom pôvodného priznania;
2. vyplňte **Deň zistenia rozdielu**, ktorý tlačivo pri priznaní opravujúcom
   iné vyžaduje (predvolený je dnešný deň);
3. opravte účtovníctvo, **Vypočítajte**, skontrolujte, exportujte a podajte
   ako zvyčajne.

Čo ďalej vyžaduje tlačivo konkrétnej krajiny (napríklad slovenský riadok
rozdielu), opisuje stránka modulu krajiny.

## Verzie tlačiva {#versions}

*Účtovníctvo → Konfigurácia → CZ/SK lokalizácia → Verzie priznania k DPH*
zobrazuje vzory dodané modulmi krajín. Každý obsahuje obdobie platnosti,
riadky so vzorcami značiek alebo súhrnnými vzorcami, typy podania, XML šablónu
a XSD schému. Sú to dáta modulu krajiny: meňte ich len na pokyn účtovníka.
Archivovaná verzia sa pri priznaniach za svoje obdobia ponúka ďalej, archiváciou
sa len sprehľadní zoznam.

## Historické sadzby DPH {#historic-rates}

Keď spoločnosť načíta slovenskú alebo českú účtovú osnovu (a pri inštalácii
modulu krajiny), vytvoria sa sadzby platné pred dnešnými ako **archivované**
dane, skopírované z dnešnej dane rovnakého druhu, aby sa vykazovali v tých
istých riadkoch. Slúžia na import starších dokladov; pri vystavovaní novej
faktúry sa nikdy neponúknu. Nájdete ich v *Účtovníctvo → Konfigurácia → Dane*
s filtrom *Archivovaný* a **Historická sadzba**; formulár dane ukazuje
**Sadzba platná od**, **Sadzba platná do** a **Odvodené z**. Ktoré sadzby sa
vytvárajú, uvádza stránka modulu krajiny. Ak ich chcete pre spoločnosť
vytvoriť znova (opakovanie je bezpečné), správca účtovníctva otvorí
spoločnosť v *Nastavenia → Spoločnosti* a v ponuke *Akcia* spustí
**Vytvoriť historické sadzby DPH**.

Ak historická sadzba existuje, iné moduly lokalizácie podľa nej zdania doklad
sadzbou platnou k jeho dátumu.

## Historické podania {#legacy}

Priznanie prenesené z predchádzajúceho systému je **Historické podanie**:
záznam o tom, čo bolo podané, označený stuhou. Nedá sa prepočítať, exportovať
ani podať. Jediná akcia, **Porovnať s vypočítaným**, prepočíta obdobie z
účtovníctva a zaznamená rozdiely v *Účtovníctvo → Výkazy → Zákonné výkazy →
Podané vs vypočítané*. Ak treba také obdobie opraviť, založte z neho dodatočné
priznanie; to je už bežné priznanie.

**Upozornenia exportu.** Kontroly, ktoré export nezastavia, sa zobrazia v
žltom pruhu navrchu formulára a v chatteri až do ďalšieho exportu.

## Obmedzenia {#limitations}

- Verziu za vás nikto nevyberie: zvoľte ju na každom priznaní. Nekontroluje sa,
  či dátumy tvoria celý mesiac alebo štvrťrok. *Typ obdobia* sa kontroluje len
  voči obdobiam, ktoré verzia pripúšťa (každá dodaná verzia pripúšťa obe).
- Kontrola sadzby, ktorá iba varuje (odvodená sadzba nezodpovedá žiadnej
  zákonnej), sa zapíše len do serverového logu a na obrazovke sa nezobrazí;
  export zastavia iba chyby.
- Stĺpec ✓ porovnáva absolútne sumy, chybu v znamienku teda neukáže.
- Dodatočné priznanie preberie typ výkazu pôvodného; zmeniť ho musíte sami.
- Výpočet ukáže to, čo hovoria značky. Daň so zlými značkami alebo doklad bez
  značiek skončí v zlom riadku alebo v žiadnom; pred podaním si prejdite
  preklik **Doklady**.
