---
title: Zpracování účtenek (účtenky / bločky)
summary: Načte účtenky z QR kódu, fotografie nebo nahraných výdajů, ověří, zda jejich částky sedí, a vytvoří z nich koncept nákupní účtenky nebo výdaj zaměstnance s DPH rozdělenou podle sazeb.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

Pohonné hmoty, stravování, drobné nákupy: podnik sbírá spoustu účtenek z
pokladny (na Slovensku *bločků*) a každou je třeba zaúčtovat s DPH
rozdělenou podle sazeb. Tento modul je k tomu společným rámcem. Uchovává
**zachycenou účtenku** — prodávajícího, datum, částku, položky a
rekapitulaci DPH podle sazeb — a vytváří z ní doklady v Odoo, zatímco údaje
dodávají samostatní **poskytovatelé**:

| Poskytovatel | Modul | Co čte |
|---|---|---|
| Ověření v eKase | [module:l10n_sk_ekasa_receipt](module:l10n_sk_ekasa_receipt) | QR kód slovenského bločku; doklad, který prodávající zaevidoval, se i s položkami načte ze služby slovenské finanční správy |
| Čtení pomocí AI | [module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai) | fotografii, jazykovým modelem — pro české a zahraniční účtenky a slovenské, jejichž kód nelze přečíst (viz [Čtení pomocí AI](#ai-reader)) |

Účtenka, která se přečte bez chyby, se stane **konceptem nákupní účtenky**
nebo s modulem
[module:l10n_cssk_receipt_capture_expense](module:l10n_cssk_receipt_capture_expense)
**výdajem zaměstnance** (viz [Výdaje](#expenses)). Účtenka, jejíž částky
nesedí, se odloží ke kontrole, nikdy se nezaokrouhlí tak, aby seděla.

Rekapitulace DPH je samostatná tabulka, protože je jediným spolehlivým
zdrojem a účtenka může mít tři sazby (slovenský bloček z restaurace: jídlo,
nealkoholické nápoje, alkohol). Množství položek se na účtence uchovávají,
účtují se ale jako množství 1 s celkovou částkou řádku, protože jednotková
cena zaokrouhlená na haléře by neseděla (31,17 l nafty za 57,85 € není
1,86 € × 31,17).

## Právní rámec {#legal}

- **Kdy stačí účtenka k odpočtu DPH.** Účtenka je zjednodušeným daňovým
  dokladem jen do určité částky; nad ní potřebuje kupující řádný daňový
  doklad.
  - Česko: zjednodušený daňový doklad lze vystavit, *„pokud celková částka
    za plnění na daňovém dokladu není vyšší než 10000 Kč“* —
    [§ 30 odst. 1 zákona č. 235/2004 Sb.](law:cz/2004/235).
  - Slovensko: doklad vyhotovený pokladnicou e-kasa klient je zjednodušenou
    fakturou, *„ak cena tovaru alebo služby vrátane dane nie je viac ako
    400 eur“* —
    [§ 74 ods. 3 písm. b) zákona o DPH](law:sk/2004/222#paragraf-74.odsek-3.pismeno-b);
    odpočet předpokládá fakturu —
    [§ 51 ods. 1 písm. a)](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a).
- **Ověření v eKase (Slovensko).** Podle
  [§ 18 ods. 1 zákona č. 384/2025 Z. z.](law:sk/2025/384#paragraf-18.odsek-1)
  umožní slovenské finanční ředitelství prostřednictvím aplikace ověřit
  pomocí QR kódu nebo identifikátoru dokladu údaje z účtenek zaslaných do
  systému eKasa a zpřístupnit je, a to i opakovaně. Ověřovatel (*overovateľ*,
  [§ 2 ods. 1 písm. aj)](law:sk/2025/384#paragraf-2.odsek-1.pismeno-aj)) musí
  před začátkem používání služby oznámit finančnímu ředitelství IP adresu,
  ze které bude ke službě přistupovat, a zasílat pravdivé výsledky ověření —
  [§ 18 ods. 11](law:sk/2025/384#paragraf-18.odsek-11). Modul eKasa
  odmítá ověřování, dokud se toto oznámení v jeho nastavení nepotvrdí.

## Co se odesílá, kdy a kým {#data}

| Kam | Co | Poskytovatel |
|---|---|---|
| slovenská finanční správa (eKasa) | text QR kódu nebo identifikátory vytištěné na účtence | ověření v eKase |
| váš poskytovatel modelu, nebo služba Data Dance pro vytěžování přes zprostředkovatele | fotografie nebo PDF účtenky | čtení pomocí AI |
| veřejné rejstříky právnických osob | IČO prodávajícího, k ověření jeho názvu | čtení pomocí AI |

Čtení se spustí, když:

- uživatel s právem *Fakturace* stiskne na účtence **Capture** (zpracovat;
  účtenka ve stavu *New*, *Error* nebo *Needs Review*);
- **kterýkoli zaměstnanec** naskenuje QR kód přes **Scan Receipt** (kamera
  se čte v prohlížeči; na server dorazí jen dekódovaný text);
- **kterýkoli zaměstnanec** nahraje obrázky účtenek v aplikaci Výdaje, je-li
  zapnuto *Capture on Expense Upload* (výchozí) — jedno čtení na obrázek, s
  právy superuživatele, aby zaměstnanci nepotřebovali přístup k účetnictví;
- čtení selhalo z **dočasného** důvodu (služba je přetížená nebo
  nedostupná): automaticky se zopakuje po 15 minutách, po hodině a po čtyřech
  hodinách. Odmítnutí, neznámá účtenka ani nečitelná fotografie se podle
  časovače neopakují.

Poskytovatelé se zkoušejí v pořadí, nejprve ti, kteří čtou kód: při
zapnutém ověření v eKase se slovenský bloček s čitelným QR kódem k modelu
nikdy nedostane. Každý pokus se zaznamená u účtenky (**Attempts**) s
výsledkem, trváním a u čtení pomocí AI i s tokeny a cenou.

## Nastavení {#setup}

*Účetnictví → Konfigurace → Nastavení*, blok **Fiscal Receipt Capture**
(popisky jsou anglicky; modul zatím nemá český překlad):

| Nastavení | Účel |
|---|---|
| Receipt Journal (deník) | nákupní deník pro nákupní účtenky; je-li prázdný, použije se první |
| Default Expense Account (nákladový účet) | účet všech řádků; **povinný**, jinak se nákupní účtenka nevytvoří |
| Document Detail (podrobnost) | *One line per VAT rate* (řádek za sazbu, výchozí — zaúčtuje přesně základ, který vykázal prodávající) nebo *One line per receipt item* (řádek za položku) |
| Auto-create Seller | zatím nemá žádný účinek: prodávající se vytváří tlačítkem **Create Seller** |
| Receipts: AI Model Chain | se čtením pomocí AI, viz [níže](#ai-reader) |

Nákupní daň pro každou sazbu DPH se bere z mapování sazeb modulu
[module:account_invoice_ai_extract](module:account_invoice_ai_extract), je-li
nainstalován, jinak z výchozí nákupní daně společnosti nebo z tuzemské
nákupní daně s touto sazbou. Mapování, které přiřazuje sazbě daň s jinou
sazbou, se odmítne.

*Účetnictví → Konfigurace → Účetnictví → Capture Providers* (správci
účetnictví) uvádí poskytovatele s pořadím, zeměmi a přepínačem *Active*.

Ke čtení QR kódů z fotografií potřebuje server balík Pythonu `zxing-cpp`;
bez něj to účtenka uvede a skenování kamerou funguje dál.

## Práce s účtenkami {#usage}

*Účetnictví → Dodavatelé → Fiscal Receipts*:

- **Scan Receipt** — otevře kameru; naskenujte daňový QR kód. Věrnostní
  nebo webový odkaz vytištěný vedle něj se odmítne a skener zůstane otevřený.
- **Captured Receipts** — všechny účtenky. *Nový*, přiložte fotografii
  (*Source image*) nebo vložte text QR kódu (*QR payload*) a stiskněte
  **Capture**.
- **To Review** — nové, neúspěšné a odložené účtenky.

Stavy: *New* (nová) → *Captured* (vše sedí), *Needs Review* (některá
kontrola selhala; důvod je uveden), *Error* (zdroj odmítl nebo účtenku
neměl kdo přečíst; důvod je uveden) → *Posted*, jakmile z ní vznikl doklad.

**Kontroly, než se účtenka považuje za zachycenou:**

- částka účtenky existuje a základ plus DPH se jí rovná;
- součet položek se rovná částce účtenky;
- každá skupina DPH je aritmeticky správná pro svou sazbu a shoduje se s
  položkami s touto sazbou; žádná položka nemá sazbu, která v rekapitulaci
  chybí;
- žádná položka není označena jako vrácení nebo oprava (jejich znaménko se
  nikdy neodhaduje);
- u čtení pomocí AI je jistota modelu vyšší než nula a není pod prahem
  společnosti.

Účtenka s identifikátorem, který už byl zachycen, se odmítne jako
duplicita. **Accept Anyway** přesune odloženou účtenku do stavu *Captured*
na vaši odpovědnost; nahlášený rozdíl zůstane v chatteru.

**Prodávající** se hledá podle DIČ (s předponou státu), potom IČO, potom
daňového čísla bez předpony — nikdy podle názvu. **Create Seller** vytvoří
partnera z názvu, DIČ a IČO na účtence. Provozovna, kde byla účtenka
vystavena, se uchová jako poznámka a k partnerovi se nedostane.

**DPH, kterou nelze odečíst.** Překročí-li částka účtenky hranici uvedenou
výše (10 000 Kč u prodávajícího s českým DIČ, 400 eur u slovenského; podle
země společnosti, neuvádí-li účtenka DIČ), účtenka to uvede a její DPH se
zaúčtuje jako součást nákladu. Máte-li na nákup řádný daňový doklad,
zaškrtněte **Full invoice held**. Nákupní účtenku z takové účtenky nelze
zaúčtovat s DPH.

**Create Vendor Receipt** vytvoří **koncept** *Nákupní účtenky* s datem
účtenky a jejím identifikátorem jako referencí, s jedním řádkem za sazbu
DPH nebo za položku (množství 1, částka bez DPH, výchozí nákladový účet) a s
kopií fotografie. Odmítne se, nemá-li některá sazba nákupní daň, je-li
přiřazená daň zahrnutá v ceně, nebo liší-li se částka či DPH dokladu —
celkem nebo za sazbu — od účtenky. Zkontrolujte ji a zaúčtujte jako
obvykle.

## Čtení pomocí AI {#ai-reader}

[module:l10n_cssk_receipt_capture_ai](module:l10n_cssk_receipt_capture_ai)
přečte vyfocenou nebo naskenovanou účtenku (obrázek nebo PDF) jazykovým
modelem, přes stejné připojení jako
[vytěžování faktur pomocí AI](module:account_invoice_ai_extract#data). Pro
české účtenky, které nemají kód k ověření, je to jediný způsob čtení.

- **Co se odesílá:** obrázek — převedený do PNG, je-li ve formátu BMP nebo
  TIFF — nebo PDF, s pevnými pokyny pro účtenky. Model vrátí identifikátory
  prodávajícího, datum, částku, položky s částkou řádku včetně DPH,
  rekapitulaci DPH, svou jistotu a poznámky a u slovenského bločku i
  vytištěné identifikátory dokladu.
- **Vytištěné identifikátory:** nepodařilo-li se slovenský QR kód
  dekódovat, zkusí se tyto identifikátory v eKase; najde-li se zaevidovaný
  doklad (a jeho částka se shoduje s fotografií), jeho údaje nahradí
  přečtené, jinak se účtenka odloží ke kontrole.
- **Název prodávajícího z rejstříku:** podle přečteného IČO přes modul
  [module:l10n_cssk_registry_verify](module:l10n_cssk_registry_verify),
  shoduje-li se DIČ z rejstříku s přečteným — nebo, chybí-li DIČ k
  porovnání, neodporují-li si názvy. Jinak zůstane přečtený údaj a chatter
  uvede proč.
- **Řetězec modelů:** *Receipts: AI Model Chain* v nastavení účtenek —
  stejný mechanismus jako u faktur, obvykle se silnějším modelem, protože
  termopapír se čte hůř než PDF. Je-li prázdný, použije se výchozí
  poskytovatel a model vytěžování faktur, jehož **práh jistoty** platí i
  zde.
- Záložka **AI Reading** ukazuje jistotu, poznámky modelu, tokeny a cenu
  (přes zprostředkovatele bez ceny).

Každé čtení je placené volání; kdo je může spustit, viz část
[co se odesílá](#data).

## Výdaje {#expenses}

[module:l10n_cssk_receipt_capture_expense](module:l10n_cssk_receipt_capture_expense)
propojí účtenky s aplikací Výdaje v Odoo (Community):

- **Create Expenses** na zachycené účtence (uživatelé s právem *Fakturace*)
  vytvoří **jeden** výdaj za celou účtenku bez ohledu na počet sazeb DPH,
  pro zaměstnance aktuálního uživatele, v kategorii nastavené v *Výdaje →
  Konfigurace → Nastavení → Receipt Capture* (*Receipt Expense Category*;
  je-li prázdná, obecná kategorie výdajů Odoo). Jeho částka a DPH se
  porovnají s účtenkou.
- **Nahrání účtenek ve Výdajích** (*Výdaje → Mé výdaje*, tlačítko
  *Nahrát*) — při zapnutém *Capture on Expense Upload* se z každého obrázku
  stane účtenka a přečte se; čisté přečtení vyplní výdaj (částku, daně,
  dodavatele), jinak výdaj ukáže důvod. Upozornění shrne, kolik se přečetlo,
  kolik je třeba zkontrolovat a kolik selhalo.
- **Scan Receipt** a **My Receipts** jsou v nabídce *Výdaje → Mé výdaje*;
  zaměstnanec vidí účtenky, které zachytil, a ty, které patří k jeho
  vlastním výdajům.
- **Více sazeb DPH na jednom výdaji.** Odoo uplatní všechny daně výdaje na
  jeden základ, což by při 21 % a 12 % dalo 33 % ze všeho. U výdaje z
  účtenky se DPH i účetní zápis — ať platil zaměstnanec, nebo společnost —
  sestaví sazbu po sazbě z rekapitulace účtenky. Výdaj, jehož částka nebo
  daně se od účtenky změnily, se odmítne zaúčtovat.
- Nelze-li DPH z účtenky odečíst, výdaj nese celou částku bez daně.
- Účtenka uplatněná jako výdaj se už nemůže stát nákupní účtenkou, a
  naopak.

## Omezení {#limitations}

- Hranice pro odpočet se uplatní podle předpony DIČ prodávajícího na každou
  účtenku. U českých účtenek modul předpokládá, že účtenka do 10 000 Kč je
  platným zjednodušeným daňovým dokladem; její obsah (např. DIČ
  prodávajícího) nekontroluje. Slovenské pravidlo 400 eur platí pro doklady
  z e-kasy a obecné pravidlo 100 eur podle § 74 ods. 3 písm. a) se
  neuplatňuje.
- **Auto-create Seller** v nastavení nemá žádný účinek.
- Vrácení a opravy na účtence se automaticky nezaúčtují.
- Množství položek jsou jen informativní; každý řádek má množství 1.
- Všechny řádky jdou na výchozí nákladový účet; pohonné hmoty, stravování a
  ostatní přeúčtujte dodatečně.
- Nahrávání účtenek zaměstnanci spouští placená čtení pomocí AI bez účasti
  účetní; nechcete-li to, vypněte *Capture on Expense Upload*.
- Údaje ze čtení pomocí AI jsou přečtením papíru: kontroly zachytí částky,
  které nesedí, ne částku přečtenou všude stejně chybně.
