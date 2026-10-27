---
title: Spracovanie pokladničných dokladov (bločky / účtenky)
summary: Načíta pokladničné doklady z QR kódu, fotografie alebo nahraných výdavkov, overí, či ich sumy sedia, a vytvorí z nich koncept nákupnej účtenky alebo výdavok zamestnanca s DPH rozdelenou podľa sadzieb.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Pohonné hmoty, stravovanie, drobné nákupy: podnik zbiera množstvo
pokladničných dokladov (*bločkov*, v Česku *účteniek*) a každý treba
zaúčtovať s DPH rozdelenou podľa sadzieb. Tento modul je na to spoločným
rámcom. Uchováva **zachytený doklad** — predávajúceho, dátum, sumu, položky a
rekapituláciu DPH podľa sadzieb — a vytvára z neho doklady v Odoo, kým údaje
dodávajú samostatní **poskytovatelia**:

| Poskytovateľ | Modul | Čo číta |
|---|---|---|
| Overenie v eKase | [module:l10n_sk_ekasa_receipt](module:l10n_sk_ekasa_receipt) | QR kód slovenského bločku; doklad, ktorý predávajúci zaevidoval, sa aj s položkami načíta zo služby finančnej správy |
| Čítanie pomocou AI | [module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai) | fotografiu, jazykovým modelom — pre české a zahraničné doklady a slovenské, ktorých kód sa nedá prečítať (pozri [Čítanie pomocou AI](#ai-reader)) |

Doklad, ktorý sa prečíta bez chyby, sa stane **konceptom nákupnej účtenky**
alebo s modulom
[module:l10n_cssk_receipt_capture_expense](module:l10n_cssk_receipt_capture_expense)
**výdavkom zamestnanca** (pozri [Výdavky](#expenses)). Doklad, ktorého sumy
nesedia, sa odloží na kontrolu, nikdy sa nezaokrúhli tak, aby sedel.

Rekapitulácia DPH je samostatná tabuľka, pretože je jediným spoľahlivým
zdrojom a doklad môže mať tri sadzby (bloček z reštaurácie: jedlo,
nealkoholické nápoje, alkohol). Množstvá položiek sa na doklade uchovávajú,
účtujú sa však ako množstvo 1 s celkovou sumou riadku, lebo jednotková cena
zaokrúhlená na centy by nesedela (31,17 l nafty za 57,85 € nie je
1,86 € × 31,17).

## Právny rámec {#legal}

- **Kedy stačí bloček na odpočítanie DPH.** Pokladničný doklad je
  zjednodušenou faktúrou len do určitej sumy; nad ňou potrebuje kupujúci
  riadnu faktúru.
  - Slovensko: doklad vyhotovený pokladnicou e-kasa klient je zjednodušenou
    faktúrou, *„ak cena tovaru alebo služby vrátane dane nie je viac ako
    400 eur“* —
    [§ 74 ods. 3 písm. b) zákona o DPH](law:sk/2004/222#paragraf-74.odsek-3.pismeno-b);
    odpočítanie dane predpokladá faktúru —
    [§ 51 ods. 1 písm. a)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a).
  - Česko: zjednodušený daňový doklad možno vystaviť, *„pokud celková částka
    za plnění na daňovém dokladu není vyšší než 10000 Kč“* —
    [§ 30 odst. 1 zákona č. 235/2004 Sb.](law:cz/2004/235).
- **Overenie v eKase.** Podľa
  [§ 18 ods. 1 zákona č. 384/2025 Z. z.](law:sk/2025/384#paragraf-18.odsek-1)
  finančné riaditeľstvo umožní prostredníctvom aplikácie overiť pomocou QR
  kódu alebo identifikátora dokladu správnosť údajov z pokladničných
  dokladov zaslaných do systému eKasa a sprístupniť tieto údaje, a to aj
  opakovane. Overovateľ
  ([§ 2 ods. 1 písm. aj)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-aj)) je
  povinný pred začatím používania služby oznámiť finančnému riaditeľstvu IP
  adresu, z ktorej bude k službe pristupovať, a zasielať pravdivé výsledky
  overenia — [§ 18 ods. 11](law:sk/2025/384#paragraf-18.odsek-11). Modul
  eKasa odmieta overovanie, kým sa toto oznámenie v jeho nastaveniach
  nepotvrdí.

## Čo sa odosiela, kedy a kým {#data}

| Kam | Čo | Poskytovateľ |
|---|---|---|
| finančná správa (eKasa) | text QR kódu alebo identifikátory vytlačené na doklade | overenie v eKase |
| váš poskytovateľ modelu, alebo služba Data Dance na vyťažovanie cez sprostredkovateľa | fotografia alebo PDF dokladu | čítanie pomocou AI |
| verejné registre právnických osôb | IČO predávajúceho, na overenie jeho názvu | čítanie pomocou AI |

Čítanie sa spustí, keď:

- používateľ s právom *Fakturácia* stlačí na doklade **Capture** (spracovať;
  doklad v stave *New*, *Error* alebo *Needs Review*);
- **ktorýkoľvek zamestnanec** naskenuje QR kód cez **Scan Receipt** (kamera
  sa číta v prehliadači; na server príde len dekódovaný text);
- **ktorýkoľvek zamestnanec** nahrá obrázky bločkov v aplikácii Výdavky,
  keď je zapnuté *Capture on Expense Upload* (predvolené) — jedno čítanie na
  obrázok, s právami superpoužívateľa, aby zamestnanci nepotrebovali prístup
  k účtovníctvu;
- čítanie zlyhalo z **dočasného** dôvodu (služba je preťažená alebo
  nedostupná): automaticky sa zopakuje po 15 minútach, po hodine a po štyroch
  hodinách. Odmietnutie, neznámy doklad ani nečitateľná fotografia sa podľa
  časovača neopakujú.

Poskytovatelia sa skúšajú v poradí, najprv tí, čo čítajú kód: pri zapnutom
overení v eKase sa slovenský bloček s čitateľným QR kódom k modelu nikdy
nedostane. Každý pokus sa zaznamená pri doklade (**Attempts**) s výsledkom,
trvaním a pri čítaní pomocou AI aj s tokenmi a cenou.

## Nastavenie {#setup}

*Účtovníctvo → Konfigurácia → Nastavenia*, blok **Fiscal Receipt Capture**
(popisy sú v angličtine; modul ešte nemá slovenský preklad):

| Nastavenie | Účel |
|---|---|
| Receipt Journal (denník) | nákupný denník pre nákupné účtenky; ak je prázdny, použije sa prvý |
| Default Expense Account (nákladový účet) | účet všetkých riadkov; **povinný**, inak sa nákupná účtenka nevytvorí |
| Document Detail (podrobnosť) | *One line per VAT rate* (riadok za sadzbu, predvolené — zaúčtuje presne základ, ktorý vykázal predávajúci) alebo *One line per receipt item* (riadok za položku) |
| Auto-create Seller | zatiaľ nemá žiadny účinok: predávajúci sa vytvára tlačidlom **Create Seller** |
| Receipts: AI Model Chain | s čítaním pomocou AI, pozri [nižšie](#ai-reader) |

Nákupná daň pre každú sadzbu DPH sa berie z mapovania sadzieb modulu
[module:account_invoice_ai_extract](module:account_invoice_ai_extract), ak
je nainštalovaný, inak z predvolenej nákupnej dane spoločnosti alebo z
tuzemskej nákupnej dane s touto sadzbou. Mapovanie, ktoré priraďuje sadzbe
daň s inou sadzbou, sa odmietne.

*Účtovníctvo → Konfigurácia → Účtovníctvo → Capture Providers* (správcovia
účtovníctva) uvádza poskytovateľov s poradím, krajinami a prepínačom
*Active*.

Na čítanie QR kódov z fotografií potrebuje server balík Pythonu
`zxing-cpp`; bez neho to doklad uvedie a skenovanie kamerou funguje ďalej.

## Práca s dokladmi {#usage}

*Účtovníctvo → Dodávatelia → Fiscal Receipts*:

- **Scan Receipt** — otvorí kameru; naskenujte daňový QR kód. Vernostný
  alebo webový odkaz vytlačený vedľa neho sa odmietne a skener zostane
  otvorený.
- **Captured Receipts** — všetky doklady. *Nový*, priložte fotografiu
  (*Source image*) alebo vložte text QR kódu (*QR payload*) a stlačte
  **Capture**.
- **To Review** — nové, neúspešné a odložené doklady.

Stavy: *New* (nový) → *Captured* (všetko sedí), *Needs Review* (niektorá
kontrola zlyhala; dôvod je uvedený), *Error* (zdroj odmietol alebo doklad
nemal kto prečítať; dôvod je uvedený) → *Posted*, keď z neho vznikol doklad.

**Kontroly, kým sa doklad považuje za zachytený:**

- suma dokladu existuje a základ plus DPH sa jej rovná;
- súčet položiek sa rovná sume dokladu;
- každá skupina DPH je aritmeticky správna pre svoju sadzbu a zhoduje sa s
  položkami s touto sadzbou; žiadna položka nemá sadzbu, ktorá v
  rekapitulácii chýba;
- žiadna položka nie je označená ako vrátenie alebo oprava (ich znamienko sa
  nikdy neodhaduje);
- pri čítaní pomocou AI je istota modelu vyššia ako nula a nie je pod prahom
  spoločnosti.

Doklad s identifikátorom, ktorý už bol zachytený, sa odmietne ako duplicita.
**Accept Anyway** presunie odložený doklad do stavu *Captured* na vašu
zodpovednosť; nahlásený rozdiel zostane v chatteri.

**Predávajúci** sa hľadá podľa IČ DPH, potom IČO, potom DIČ — nikdy podľa
názvu. **Create Seller** vytvorí partnera z názvu, IČ DPH a IČO na doklade.
Prevádzka, kde bol doklad vyhotovený, sa uchová ako poznámka a k partnerovi
sa nedostane.

**DPH, ktorú nemožno odpočítať.** Ak suma dokladu prekročí hranicu uvedenú
vyššie (400 eur pri predávajúcom so slovenským IČ DPH, 10 000 Kč pri
českom; podľa krajiny spoločnosti, ak doklad IČ DPH neuvádza), doklad to
uvedie a jeho DPH sa zaúčtuje ako súčasť nákladu. Ak máte na nákup riadnu
faktúru, zaškrtnite **Full invoice held**. Nákupnú účtenku z takého dokladu
nemožno zaúčtovať s DPH.

**Create Vendor Receipt** vytvorí **koncept** *Nákupnej účtenky* s dátumom
dokladu a jeho identifikátorom ako referenciou, s jedným riadkom za sadzbu
DPH alebo za položku (množstvo 1, suma bez DPH, predvolený nákladový účet) a
s kópiou fotografie. Odmietne sa, ak niektorá sadzba nemá nákupnú daň, ak je
priradená daň zahrnutá v cene, alebo ak sa suma či DPH dokladu — spolu alebo
za sadzbu — líši od bločku. Skontrolujte ju a zaúčtujte ako obvykle.

## Čítanie pomocou AI {#ai-reader}

[module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai)
prečíta odfotený alebo naskenovaný doklad (obrázok alebo PDF) jazykovým
modelom, cez to isté pripojenie ako
[vyťažovanie faktúr pomocou AI](module:account_invoice_ai_extract#data). Pre
české účtenky, ktoré nemajú kód na overenie, je to jediný spôsob čítania.

- **Čo sa odosiela:** obrázok — prekódovaný do PNG, ak je vo formáte BMP
  alebo TIFF — alebo PDF, s pevnými pokynmi pre pokladničné doklady. Model
  vráti identifikátory predávajúceho, dátum, sumu, položky so sumou riadku
  vrátane DPH, rekapituláciu DPH, svoju istotu a poznámky a na slovenskom
  bločku aj vytlačené identifikátory dokladu.
- **Vytlačené identifikátory:** ak sa slovenský QR kód nepodarilo
  dekódovať, tieto identifikátory sa skúsia v eKase; ak sa zaevidovaný doklad
  nájde (a jeho suma sa zhoduje s fotografiou), jeho údaje nahradia
  prečítané, inak sa doklad odloží na kontrolu.
- **Názov predávajúceho z registra:** podľa prečítaného IČO cez modul
  [module:l10n_cssk_registry_verify](module:l10n_cssk_registry_verify), ak sa
  IČ DPH z registra zhoduje s prečítaným — alebo, ak IČ DPH na porovnanie
  chýba, ak si názvy neodporujú. Inak zostane prečítaný údaj a chatter
  uvedie prečo.
- **Reťazec modelov:** *Receipts: AI Model Chain* v nastaveniach dokladov —
  ten istý mechanizmus ako pri faktúrach, zvyčajne so silnejším modelom,
  lebo termopapier sa číta horšie ako PDF. Ak je prázdny, použije sa
  predvolený poskytovateľ a model vyťažovania faktúr, ktorého **prah istoty**
  platí aj tu.
- Záložka **AI Reading** ukazuje istotu, poznámky modelu, tokeny a cenu
  (cez sprostredkovateľa bez ceny).

Každé čítanie je platené volanie; kto ho môže spustiť, pozri v časti
[čo sa odosiela](#data).

## Výdavky {#expenses}

[module:l10n_cssk_receipt_capture_expense](module:l10n_cssk_receipt_capture_expense)
prepojí doklady s aplikáciou Výdavky v Odoo (Community):

- **Create Expenses** na zachytenom doklade (používatelia s právom
  *Fakturácia*) vytvorí **jeden** výdavok za celý doklad bez ohľadu na počet
  sadzieb DPH, pre zamestnanca aktuálneho používateľa, v kategórii
  nastavenej v *Výdavky → Konfigurácia → Nastavenia → Receipt Capture*
  (*Receipt Expense Category*; ak je prázdna, všeobecná kategória výdavkov
  Odoo). Jeho suma a DPH sa porovnajú s dokladom.
- **Nahratie bločkov vo Výdavkoch** (*Výdavky → Moje výdaje*, tlačidlo
  *Nahrať*; Odoo tu v slovenčine používa české slovo „výdaje“) — pri
  zapnutom *Capture on Expense Upload* sa z každého obrázka stane doklad a
  prečíta sa; čisté prečítanie vyplní výdavok (sumu, dane, dodávateľa),
  inak výdavok ukáže dôvod. Upozornenie zhrnie, koľko sa prečítalo, koľko
  treba skontrolovať a koľko zlyhalo.
- **Scan Receipt** a **My Receipts** sú v ponuke *Výdavky → Moje výdaje*;
  zamestnanec vidí doklady, ktoré zachytil, a tie, ktoré patria k jeho
  vlastným výdavkom.
- **Viac sadzieb DPH na jednom výdavku.** Odoo uplatní všetky dane výdavku
  na jeden základ, čo by pri 23 % a 5 % dalo 28 % zo všetkého. Pri výdavku z
  bločku sa DPH aj účtovný zápis — či platil zamestnanec, alebo spoločnosť —
  zostavia sadzbu po sadzbe z rekapitulácie bločku. Výdavok, ktorého suma
  alebo dane sa od bločku zmenili, sa odmietne zaúčtovať.
- Ak DPH z bločku nemožno odpočítať, výdavok nesie celú sumu bez dane.
- Doklad uplatnený ako výdavok sa už nemôže stať nákupnou účtenkou, a
  naopak.

## Obmedzenia {#limitations}

- Hranica pre odpočítanie sa uplatní podľa predpony IČ DPH predávajúceho na
  každý doklad: slovenské pravidlo 400 eur platí pre doklady z e-kasy a
  všeobecné pravidlo 100 eur podľa § 74 ods. 3 písm. a) sa neuplatňuje. Pri
  českých účtenkách modul predpokladá, že účtenka do 10 000 Kč je platným
  zjednodušeným daňovým dokladom; jej obsah nekontroluje.
- **Auto-create Seller** v nastaveniach nemá žiadny účinok.
- Vrátenia a opravy na bločku sa automaticky nezaúčtujú.
- Množstvá položiek sú len informatívne; každý riadok má množstvo 1.
- Všetky riadky idú na predvolený nákladový účet; pohonné hmoty,
  stravovanie a ostatné preúčtujte dodatočne.
- Nahrávanie bločkov zamestnancami spúšťa platené čítania pomocou AI bez
  účasti účtovníka; ak to nechcete, vypnite *Capture on Expense Upload*.
- Údaje z čítania pomocou AI sú prečítaním papiera: kontroly zachytia sumy,
  ktoré nesedia, nie sumu prečítanú všade rovnako nesprávne.
