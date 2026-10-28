---
title: CZ/SK lokalizace — společné jádro
summary: Společný základ českých a slovenských zákonných modulů — nastavení, finanční úřady, kontrola IČO, období DPH dokladu, životní cyklus podání a porovnání podaného s vypočteným.
verified: 19.0.1.18.1
---

## K čemu slouží {#purpose}

Na tomto modulu staví každý český a slovenský zákonný modul lokalizace —
přiznání k DPH, kontrolní hlášení, souhrnné hlášení, účetní závěrka, přiznání
k dani z příjmů. Záměrně ho instalujete jen zřídka: nainstaluje se s prvním z
nich nebo s kompletními sadami
[module:l10n_cz_datadance](module:l10n_cz_datadance) a
[module:l10n_sk_datadance](module:l10n_sk_datadance).

Přímo přináší:

- jeden **blok nastavení** pro celou lokalizaci;
- seznam **finančních úřadů** a **typů subjektů**, které podání používají;
- **kontrolu IČO** u českých a slovenských kontaktů;
- **DUZP** v seznamech faktur a datum **Deklarované období DPH** na dokladech,
  volitelně s přeúčtováním DPH;
- **výskyt ve výkazech** u zaúčtovaného dokladu;
- **společný životní cyklus zákonných podání** — výpočet, export, označení
  jako podané, dodatečné podání — a obrazovky **Podané vs vypočtené**;
- **mapování účtů do výkazů** pro účtové rozvrhy, které nepoužívají čísla účtů
  ze směrné účtové osnovy.

Závisí jen na modulech `account` a `mail`, takže funguje v Community i
Enterprise.

## Nastavení {#setup}

*Účetnictví → Konfigurace → Nastavení*, blok **Česká / slovenská
lokalizace**:

| Nastavení | Co dělá |
|---|---|
| Rozšířené účetní menu (Community) | Nainstaluje modul OCA `account_usability` s nabídkami, které má Enterprise (hlavní kniha, deníky, saldokonto po splatnosti…). Jen v Community. |
| Finanční výkazy (Community) | Nainstaluje modul OCA `account_financial_report`: hlavní kniha, obratová předvaha, kniha partnerů, saldokonto po splatnosti, deník. Jen v Community. |
| Výchozí správce daně | Finanční úřad, kterému jsou podání adresována. Nabízejí se jen úřady země daňové příslušnosti společnosti. |
| DPH přiznaná v pozdějším období | Účet pro přeúčtování DPH — viz [Přeúčtování DPH](#vat-deferral). Prázdné = vypnuto. |
| Deníky závěrky roku | Deníky se zápisy uzavření a otevření účetního roku. Jejich doklady se nezapočítávají do účetní závěrky, daňového přiznání k dani z příjmů ani do finančních výkazů, aby uzavření roku nevynulovalo rozvahu a výsledovku. Prázdné, pokud se rok v této databázi neuzavírá. |

Kompletní sady přidávají do tohoto bloku vlastní přepínače, jeden pro každý
volitelný modul.

## Vaše společnost {#company}

Ve formuláři společnosti (*Nastavení → Společnosti*) za polem *Země*:

- **Finanční úřad** — totéž pole jako *Výchozí správce daně* výše.
- **Typ subjektu** — právnická nebo fyzická osoba, ze seznamu
  [typů subjektů](#registries) země společnosti; podle něj se liší některé
  formuláře.

Zápis v obchodním rejstříku (*zapsaná v obchodním rejstříku vedeném…*) patří
do pole Odoo **Zápis v obchodním rejstříku** (*Trade Registry*) u společnosti, které
česká a slovenská lokalizace tiskne na fakturu. Tento modul měl dříve
samostatné pole *Registrační údaje*, které netiskl žádný doklad; z formuláře
zmizelo a při aktualizaci se jeho hodnota zkopíruje do pole *Zápis v
obchodním rejstříku*, pokud bylo prázdné.

## Kontakty a IČO {#partners}

U kontaktů se zemí Česko nebo Slovensko:

- Pole s registračním číslem se jmenuje **IČO** a zobrazuje se i u fyzických
  osob (Odoo ho jinak ukazuje jen u společností), protože živnostník, který
  nakoupí přes e-shop, vznikne jako osoba a IČO má.
- IČO se **kontroluje při uložení**: musí mít 6 až 8 číslic a platnou
  kontrolní číslici (vážený součet modulo 11, stejný v obou zemích). Chybná
  hodnota se odmítne se zprávou, která jmenuje společnost — název firmy, DIČ
  ani `Test` už do pole zapsat nelze.
- Platné IČO se uloží **doplněné nulami na osm číslic**: z `580007` bude
  `00580007`.
- Před polem DIČ je **Typ subjektu** pro zařazení partnera v zákonných
  výkazech.

Kontakty jiných zemí se nekontrolují: německé `HRB 12345` se přijme tak, jak
je.

## Finanční úřady a typy subjektů {#registries}

*Účetnictví → Konfigurace → CZ/SK lokalizace*:

- **Finanční úřady** — úřady, kterým se podání adresují, každý se stálým
  kódem, kódem zapisovaným do XML (*Kód podání*) a u územního pracoviště i s
  nadřízeným finančním úřadem. Úřady nahrávají české a slovenské zákonné
  moduly; vy obvykle jen jeden vyberete. Zobrazují se úřady zemí daňové
  příslušnosti společností právě **zvolených** v přepínači společností: kdo
  pracuje zároveň v české i slovenské společnosti, vidí obojí.
- **Typy osob / subjektů** — právnická osoba, fyzická osoba a podobně, pro
  každou zemi, nahrané stejně.
- **Mapování účtů do výkazů** — viz [níže](#account-mapping). Vidí ho
  správci účetnictví.

## Období DPH dokladu {#vat-period}

### DUZP

Seznamy vydaných a přijatých faktur mají sloupec **DUZP** (volitelný, ve
výchozím stavu zobrazený) a ve vyhledávání filtr i seskupení podle něj. Datum
uskutečnění zdanitelného plnění určuje období DPH u prodeje.

### Deklarované období DPH {#vat-period-declared}

Na fakturách, opravných daňových dokladech a přijatých fakturách je za datem
splatnosti pole **Deklarované období DPH**: období, ve kterém se DPH vykáže,
liší-li se od obvyklého. V běžném případě ho nechte prázdné.

Zákonné výkazy zařadí doklad do období takto:

| Doklad | Období |
|---|---|
| Vydaná faktura, opravný daňový doklad odběrateli | *Deklarované období DPH*, je-li vyplněno; jinak DUZP; jinak datum zaúčtování |
| Přijatá faktura, opravný doklad od dodavatele, jiný účetní doklad | *Deklarované období DPH*, je-li vyplněno; jinak datum zaúčtování |

Vyplňte ho u přijaté faktury, z níž uplatňujete odpočet později, než je
zaúčtována, u opravy přiznávané v pozdějším období nebo u dokladu zadaného
opožděně. Právní základ je v části [Právní rámec](#legal).

### Přeúčtování DPH {#vat-deferral}

Připadne-li *Deklarované období DPH* na pozdější měsíc než datum zaúčtování,
přiznání vykáže daň později, ale účet 343 ji nese v měsíci zaúčtování a s
přiznáním nesouhlasí. Vyberete-li v nastavení *DPH přiznaná v pozdějším
období* účet, vzniknou při zaúčtování takového dokladu i dva účetní doklady v
prvním deníku ostatních účetních operací:

1. k datu zaúčtování se daň převede z účtu DPH na zvolený účet;
2. k deklarovanému datu se vrátí zpět. Je-li to datum ještě v budoucnosti,
   doklad se zaúčtuje automaticky, jakmile nastane.

Převádějí se jen daňové řádky, které vstupují do uzávěrky DPH. Doklady nenesou
daně ani daňové štítky, takže je žádné přiznání nečte. Původní doklad zobrazí
**VAT deferral: *n* entries** s odkazem na ně; každý z nich ukazuje původní
doklad v poli *VAT Deferral Of*. Vrácení dokladu do konceptu, jeho zrušení
nebo změna deklarovaného data tyto doklady zruší (a podle potřeby vytvoří
nové).

## Právní rámec {#legal}

*Deklarované období DPH* existuje proto, že odpočet daně lze uplatnit později
než plnění:

- **Česko** — plátce je oprávněn uplatnit nárok na odpočet nejdříve za
  zdaňovací období, ve kterém jsou splněny podmínky (zejména má daňový doklad),
  a nelze ho uplatnit po uplynutí druhého kalendářního roku následujícího po
  roce, ve kterém nárok vznikl —
  [§ 73 odst. 2 a 3 zákona o DPH č. 235/2004 Sb.](law:cz/2004/235).
- **Slovensko** — odpočet se provede nejdříve v období vzniku práva a
  nejpozději v posledním období téhož kalendářního roku, má-li plátce fakturu
  do lhůty pro podání přiznání; jinak v období, kdy fakturu obdrží —
  [§ 51 ods. 2 slovenského zákona o DPH](law:sk/2004/222#paragraf-51.odsek-2).

Modul zaznamená období, které zvolíte. Zda dodržíte tyto lhůty, nekontroluje.

## Výskyt ve výkazech {#footprint}

Zaúčtovaná faktura nebo účetní doklad má tlačítko **Výskyt ve výkazech**
(jen pro účetní). Zobrazí řádky zákonných výkazů, do kterých doklad vstupuje —
výkaz, kód řádku a popis — a pokud už podání za období existuje, i podání s
odkazem na ně. Prázdné podání znamená, že výkaz za období ještě nebyl
vytvořen; řádky ukazují, kam by doklad vstoupil. Které výkazy se zobrazí,
závisí na nainstalovaných modulech.

## Zákonná podání: společný životní cyklus {#filings}

Přiznání k DPH, kontrolní hlášení, souhrnné hlášení a další formuláře jsou
samostatné moduly, ale mají jeden společný životní cyklus:

| Krok | Tlačítko | Co se stane |
|---|---|---|
| Koncept → Náhled | *Vypočítat* | řádky se vypočtou z účetnictví |
| Náhled → Exportováno | *Exportovat XML* | proběhnou kontroly obsahu, vytvoří se XML, ověří se proti oficiálnímu schématu a přiloží se. Chyba v kontrole export zastaví; **upozornění** ne, ale zobrazí se v oznámení, zapíše se do chatu a zůstane v poli *Upozornění exportu* do dalšího exportu — přečtěte si je před podáním |
| Exportováno → Podáno | *Označit jako podané* | exportované XML se zmrazí jako **podaná kopie** (*Podané XML*), zaznamená se datum a podání se uzamkne: nelze ho už přepočítat, znovu exportovat ani smazat |
| | *Podat* | otevře záznam o doručení pro potvrzení od úřadu — viz [module:l10n_cssk_submission_base](module:l10n_cssk_submission_base) |
| Podáno → Koncept | *Vrátit do konceptu* | jen správci účetnictví; podaná kopie zůstane zachována |
| | *Dodatečný / opravný* | u podaného výkazu: vytvoří koncept dodatečného podání propojený s původním |

Každé XML, které bylo kdy označeno jako podané, zůstává v poli **Historie
podání**, takže i po vrácení, přepočtu a novém podání je původně podaná kopie
k dispozici. Číslo podání z portálu zapište do pole **Reference podání**.

**Historická podání.** Podání převzaté z předchozího systému je ve stavu
*Historické podání*: zaznamenává, co bylo skutečně podáno, a nelze ho
vypočítat, exportovat ani podat. Lze k němu vytvořit dodatečné podání a lze ho
porovnat s tím, co za stejné období vypočte Odoo (*Porovnat s vypočteným*, viz
níže).

## Podané vs vypočtené {#comparisons}

*Účetnictví → Výkazy → Zákonné výkazy → Podané vs vypočtené*:

- **Porovnání** — jeden řádek za každé podání a způsob porovnání, s počtem
  shodných řádků, zjištění, řádků k posouzení a se součty.
- **Řádky k posouzení** — jednotlivé řádky všech porovnání, filtrované na ty,
  které čekají na odpověď.

Porovnání vznikne tlačítkem na podání. *Porovnat s vypočteným* u historického
podání ho postaví vedle toho, co Odoo vypočte za stejné období; slovenská sada
přidává porovnání podání s jiným podáním a s účtem 343. Pole **Porovnáno
vůči** říká, co je v pravém sloupci:

| Porovnáno vůči | Pravý sloupec |
|---|---|
| Podání, přepočítané | co Odoo vypočte za období podání |
| Účetnictví | zůstatek na účtech, např. 343 |
| Jiné podání | jiné podání za stejné období |

Každý řádek má **výsledek**:

| Výsledek | Význam |
|---|---|
| Shoduje se | stejná částka na obou stranách |
| Částka se liší | stejný řádek, jiná částka |
| Stejná částka, jiný řádek | obě strany mají stejnou částku na různých řádcích (zobrazeno jako propojená dvojice) |
| Má to jen podání / Počítáme to jen my | řádek je jen na jedné straně |
| Slovníky nejsou namapovány | strany používají kódy řádků, které nelze spárovat |
| Rozdíl je očekávaný | strukturální rozdíl, např. kontrolní hlášení obsahuje méně než přiznání |
| Informativní, nikoli kontrola | jen pro informaci, nikdy zjištění |

Zjištění vyřídíte nastavením **stavu** řádku — *Dotázán účetní*, *Podání bylo
správné*, *Podání bylo nesprávné*, *Chyba je u nás*, *Vysvětleno, bez zásahu*
— a zápisem vyjádření účetní do **Poznámky**. Odpověď i poznámka přežijí nové
spuštění, které aktualizuje jen částky. Řádek, který už není na žádné straně,
se nesmaže, ale označí jako *Již se neporovnává*.

Stav porovnání se odvíjí od jeho řádků — *Vše se shoduje*, *K posouzení*,
*Řeší se*, *Každý rozdíl zodpovězen* — a ručně ho nastavit nelze. Když
porovnání celé projdete, klikněte na **Schválit**; *Odvolat schválení* ho
zruší. Nové spuštění schválení nezruší.

## Mapování účtů do výkazů {#account-mapping}

Zákonné výkazy čtou zůstatky podle **čísla účtu** ze směrné účtové osnovy.
Rozvrh převzatý z jiného systému často používá vlastní analytické účty a takový
účet nepadne do žádného řádku výkazu.

*Účetnictví → Konfigurace → CZ/SK lokalizace → Mapování účtů do výkazů*
(správci účetnictví) vám umožní ponechat účtový rozvrh a určit, pod jakým
číslem se účet vykazuje:

| Pole | Význam |
|---|---|
| Účet | váš účet |
| Strana zůstatku | *Jakýkoli zůstatek* nebo *Jen debetní* / *Jen kreditní zůstatek* — např. bankovní účet vykázaný jako krátkodobý bankovní úvěr, jen když je přečerpaný |
| Vykazovaný kód | číslo účtu, pod kterým ho výkaz čte; čisté číslo bez mezer a operátorů |

Mapování podle strany zůstatku platí jen pro rozvahové zůstatky (ke dni); ve
výsledovce si účet ponechá vlastní číslo. Účet může mít buď jedno mapování
*Jakýkoli zůstatek*, nebo debetní a/nebo kreditní, ne obojí. Mapování platí
stejně pro náhled, XML i rozpad řádku.

## Omezení {#limitations}

- Kontrola IČO ověří, že číslo je správně utvořené, ne že existuje; ověření v
  rejstříku dělají jiné moduly.
- *Deklarované období DPH* se nekontroluje vůči zákonným lhůtám.
- Přeúčtování DPH jde do prvního deníku ostatních účetních operací
  společnosti; deník nelze vybrat. Společnost bez něj dostane při zaúčtování
  chybu.
- *Upozornění exportu* se zobrazí v chatu podání a v oznámení po exportu;
  formuláře podání je zatím neukazují jako pruh nad formulářem.
