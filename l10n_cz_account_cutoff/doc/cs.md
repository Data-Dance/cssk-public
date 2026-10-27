---
title: CZ časové rozlišení (381, 383, 384, 385)
summary: Nasměruje nástroje Odoo na časové rozlišení na české účty 381, 383, 384 a 385 — časová rozlišení OCA v edici Community, vlastní časové rozlišení Odoo v edici Enterprise.
verified: 19.0.1.0.2
---

## K čemu slouží {#purpose}

Časové rozlišení přesouvá náklad nebo výnos do období, do kterého patří,
když faktura spadá do jiného: pojistné zaplacené předem na příští rok,
nájemné přijaté předem, prosincová služba fakturovaná v lednu. Česká účtová
osnova na to má čtyři účty:

| Účet | Název | Typický případ |
|---|---|---|
| 381 | Náklady příštích období | pojistné nebo nájemné zaplacené předem |
| 383 | Výdaje příštích období | nájemné placené pozadu |
| 384 | Výnosy příštích období | nájemné nebo předplatné přijaté předem |
| 385 | Příjmy příštích období | nájemné přijímané pozadu |

Odoo má na časové rozlišení podle edice dva různé nástroje. Ani jeden české
účty nezná. Propojují je dva malé moduly:

- **Tento modul** ([module:l10n_cz_account_cutoff](module:l10n_cz_account_cutoff))
  vyplní výchozí účty **časových rozlišení OCA**
  (`account_cutoff_start_end_dates`), která běží v edici Community i
  Enterprise — viz [Časová rozlišení OCA](#cutoffs).
- [module:l10n_cz_account_deferred](module:l10n_cz_account_deferred) vyplní
  účty **vlastního časového rozlišení Odoo Enterprise** — viz
  [Časové rozlišení v Enterprise](#enterprise).

Oba se nainstalují samy, je-li přítomen jejich nástroj a česká účtová
osnova (`l10n_cz`). Ani jeden sám nic neúčtuje: jen zajistí, aby nástroj
účtoval na správné účty.

Položky, jejichž výše ke konci období ještě **není známa**, patří na dohadné
účty 388 a 389, ne sem; k tomu slouží
[module:l10n_cssk_accrual](module:l10n_cssk_accrual).

## Právní rámec {#legal}

- Podle [§ 3 odst. 1 zákona o účetnictví](law:cz/1991/563) se o
  skutečnostech účtuje do období, s nímž časově a věcně souvisejí, a o
  veškerých nákladech a výnosech bez ohledu na okamžik jejich zaplacení nebo
  přijetí.
- [Vyhláška č. 500/2002 Sb.](law:cz/2002/500) v § 13 a § 19 vymezuje
  položky: náklady příštích období jsou výdaje, které se týkají nákladů
  příštích účetních období; příjmy příštích období částky nepřijaté, které
  časově a věcně souvisejí s výnosy běžného období a nejsou účtovány přímo na
  účtech pohledávek; výdaje příštích období náklady běžného období, na které
  ještě nebyl uskutečněn výdaj; výnosy příštích období příjmy, které věcně
  patří do výnosů příštích období. Oba paragrafy stanoví hledisko pro
  použití těchto účtů: v okamžiku zaúčtování musí být současně známy účel,
  **částka** a období. Položka, jejíž výše známa není, patří na dohadný účet.

## Časová rozlišení OCA {#cutoffs}

### Co modul nastaví {#cutoffs-setup}

U společnosti s českou osnovou — při načtení osnovy nebo při instalaci,
pokud ji společnost už má — modul vyplní, jen jsou-li prázdné:

| Nastavení (*Účetnictví → Konfigurace → Nastavení*, blok *Časová rozlišení*) | Účet |
|---|---|
| Výchozí účet pro náklady příštích období | 381000 |
| Výchozí účet pro výdaje příštích období | 383000 |
| Výchozí účet pro výnosy příštích období | 384000 |
| Výchozí účet pro příjmy příštích období | 385000 |
| Výchozí deník časového rozlišení | první deník společnosti typu *Ostatní* |

Modul také vypne **Časové rozlišení daní**. Nástroj OCA ho má ve výchozím
stavu zapnuté a pak časově rozlišuje i DPH zdrojových řádků, na *Daňový účet
výdajů / příjmů příštích období*, který česká osnova nemá — časové rozlišení
řádků s daní proto končilo chybou *Missing 'Accrued Expense Tax Account'*.
Správné by to ani nebylo: daň na vstupu nelze odpočíst, dokud plátce nemá
daňový doklad ([§ 73 odst. 1 písm. a) zákona o DPH](law:cz/2004/235#p73)),
takže výdaje a příjmy příštích období na 383 / 385 jsou částky bez DPH. Při
instalaci a aktualizaci se volba vypne jen tam, kde není nastaven žádný daňový účet pro
časové rozlišení (ve společnosti ani na dani); nastavila-li ho vaše účetní,
zůstane zapnutá.

Každé z nich tam můžete změnit. Projděte si i další dvě nastavení téhož
bloku, která modul nemění:

- **Zaúčtovat účetní zápis časového rozlišení** je vypnuto: zápis vznikne
  jako koncept, který zkontrolujete a zaúčtujete.
- **Partner na účetních položkách ve výchozím nastavení** určuje, zda řádky
  zápisu nesou partnera.

### Zadání dat {#cutoffs-dates}

Časové rozlišení OCA vychází z **počátečního a koncového data na řádcích
faktur** (*Počáteční datum*, *Koncové datum*). Zadejte je na každém řádku,
jehož náklad nebo výnos se týká období — například 1. 7. 2026 – 30. 6. 2027
na faktuře za roční pojištění. Mají-li být data u produktu povinná,
zaškrtněte na něm *Musí mít počáteční/koncové datum*.

### Spuštění časového rozlišení {#cutoffs-usage}

Ke konci období: *Účetnictví → Účetnictví → Časová rozlišení*, vyberte druh
a klikněte na *Nový*:

| Nabídka | Účet | Které řádky zahrne |
|---|---|---|
| Náklady příštích období | 381 | řádky přijatých faktur s datem nejpozději k datu časového rozlišení, jejichž koncové datum je pozdější; časově se rozliší část po tomto datu |
| Výnosy příštích období | 384 | totéž u vydaných faktur |
| Výdaje příštích období | 383 | řádky přijatých faktur s datem **po** datu časového rozlišení, jejichž počáteční datum je nejpozději k němu; zpět se přesune část do tohoto data |
| Příjmy příštích období | 385 | totéž u vydaných faktur |

Částka se dělí podle dnů. Zadejte *Datum časového rozlišení*, zkontrolujte
*Zdrojové deníky*, klikněte na **Znovu vygenerovat řádky**, zkontrolujte
řádky a klikněte na **Vytvořit účetní zápis**. Zápis má datum časového
rozlišení.

Z toho plynou dvě praktické věci:

- 383 a 385 fungují jen s fakturami, které jsou **už zaúčtované** s
  pozdějším datem — spouštějte je, když jsou lednové faktury za prosincové
  služby zaúčtované a knihy ještě nejsou uzavřené.
- Zápis časového rozlišení se **automaticky nestornuje**. Stornujte ho sami
  k prvnímu dni následujícího období (tlačítko *Vytvořit opravný doklad* na
  zápisu — tak Odoo v češtině nazývá *Reverse Entry*; o opravný daňový
  doklad nejde), aby původní řádky faktur zatížily období, do kterého
  patří.

Ve společnosti může existovat jen jedno časové rozlišení daného druhu k
danému datu.

## Časové rozlišení v Enterprise {#enterprise}

Odoo Enterprise (`account_accountant`) má vlastní časové rozlišení: na
řádku faktury zadáte období ve sloupci **Odložené datum** (*Deferred Date*)
a Odoo částku rozloží přes účet časového rozlišení po měsících nebo po
dnech.

[module:l10n_cz_account_deferred](module:l10n_cz_account_deferred) se
nainstaluje sám spolu s `account_accountant` v databázi s českou osnovou a v
*Účetnictví → Konfigurace → Nastavení* nastaví:

| Nastavení | Hodnota |
|---|---|
| Časové rozlišení nákladů → Náklad příštích období | 381000 |
| Časové rozlišení výnosů → Výnosy příštích období | 384000 |
| *Deník* obou bloků | první deník společnosti typu *Ostatní*, je-li prázdný |

Bez něj Enterprise vyplní oba účty prvním účtem oběžných aktiv a prvním
účtem krátkodobých závazků v osnově, ať jsou jakékoli. Při instalaci modul
oba účty v každé české společnosti nastaví, jsou-li prázdné nebo stále na
této obecné volbě; účet, který jste nastavili ručně, ponechá. Později se
týká už jen nových společností.

Zda se zápisy vytvářejí při zaúčtování faktury (*Při zaúčtování faktury*)
nebo najednou (*Ručně & Seskupeno*) a zda se částka dělí po měsících nebo
dnech, jsou vlastní nastavení Enterprise v týchž blocích. Přehledy jsou v
*Účetnictví → Revize → Regularization Entries → Deferred Expenses /
Deferred Revenues* (tyto nabídky Odoo do češtiny nepřekládá).

Časové rozlišení Enterprise pokrývá jen případy placené předem, tedy 381 a
384. Výdaje a příjmy příštích období (383, 385) je třeba řešit časovými
rozlišeními OCA uvedenými výše nebo ručním zápisem.

## Omezení {#limitations}

- Oba moduly jen nastavují výchozí účty a deníky. Samy nic nepočítají ani
  neúčtují.
- Výdaje a příjmy příštích období se účtují bez DPH. Společnost, která není
  plátcem DPH a pro kterou je DPH nákladem, musí DPH doplnit ručně.
- Zápisy časového rozlišení se nestornují automaticky.
- V edici Enterprise mohou být nainstalovány oba nástroje současně a řádek
  faktury pak ukazuje obě sady dat. Na jeden řádek používejte jen jeden
  nástroj: data zadaná v obou by částku časově rozlišila dvakrát.
- Účet 382 *Komplexní náklady příštích období* není mapován.
- Ani jeden modul nekontroluje podmínku vyhlášky, že částka a období jsou
  známy; odhad do časového rozlišení nepatří.
