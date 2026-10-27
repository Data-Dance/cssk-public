---
title: Srážky ze mzdy CZ/SK
summary: Evidence českých a slovenských nařízení srážek ze mzdy, zákonné pořadí uspokojení všech nařízení zaměstnance na výplatní pásce, oznámení plátce mzdy soudu či exekutorovi a poukázání srážek příjemci.
verified: 19.0.1.3.0
---

## K čemu slouží {#purpose}

Nařídí-li soud, soudní exekutor nebo úřad srážky ze mzdy zaměstnance —
česká *exekuce srážkami ze mzdy*, slovenská *exekúcia zrážkami zo mzdy* —
stává se zaměstnavatel **plátcem mzdy**. Musí seřadit nařízení podle
pořadí, ponechat zaměstnanci nezabavitelnou částku, zbytek rozdělit mezi
oprávněné v pořadí, které stanoví zákon, sražené částky vyplatit a
vyúčtovat.

Tento modul je k tomu **evidence**:

- jeden záznam za každé doručené nařízení, s pořadím, druhem pohledávky a
  zbývajícím dluhem;
- výpočet, který bere **všechna** probíhající nařízení zaměstnance najednou
  a určí, kolik z měsíční čisté mzdy připadne na každé z nich — podle
  českých nebo slovenských předpisů, podle země společnosti;
- jedna **srážka** za každé nařízení a výplatní pásku s údajem, ze které
  třetiny částka pochází;
- **oznámení** plátce mzdy a **vyúčtování srážek** k tisku.

Závisí jen na modulu `hr` Odoo, vlastní mzdy tedy nemá. Výplatní pásku
napojuje doplněk popsaný v části [Mzdová jádra](#engines) a platbu
exekutorovi doplněk v části [Poukázání příjemci](#accounting). Skupina
modulů:

| Modul | Co dělá |
|---|---|
| [module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base) (tento modul) | Evidence, výpočet, oznámení. |
| [module:l10n_cssk_hr_payroll_garnishment_ee](module:l10n_cssk_hr_payroll_garnishment_ee) | Napojení na Mzdy Odoo Enterprise. |
| [module:l10n_cssk_hr_payroll_garnishment_oca](module:l10n_cssk_hr_payroll_garnishment_oca) | Napojení na mzdovou aplikaci OCA. |
| [module:l10n_cssk_hr_payroll_garnishment_account](module:l10n_cssk_hr_payroll_garnishment_account) | Ze srážek vytvoří závazky vůči exekutorovi. |

Samotnou srážku počítá mzdové pravidlo národních mezd:
[module:l10n_cz_hr_payroll_ee](module:l10n_cz_hr_payroll_ee),
[module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca),
[module:l10n_sk_hr_payroll_ee](module:l10n_sk_hr_payroll_ee) nebo
[module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca).

## Právní rámec {#legal}

Ověřeno proti úplným zněním účinným v říjnu 2026.

**Česko** — [občanský soudní řád, § 276 až 302](law:cz/1963/99) a
[nařízení vlády č. 595/2006 Sb.](law:cz/2006/595), o nezabavitelných
částkách. Podle stejných pravidel se postupuje i při exekuci vedené soudním
exekutorem.

- Sráží se z **čisté mzdy**: mzda po odečtení zálohy na daň z příjmů
  fyzických osob, pojistného na sociální zabezpečení, příspěvku na státní
  politiku zaměstnanosti a pojistného na veřejné zdravotní pojištění
  (§ 277).
- Povinnému se nesmí srazit **nezabavitelná částka** (§ 278). Podle § 1
  nařízení je to 85 % součtu životního minima jednotlivce, normativního
  nájemného pro jednočlennou domácnost v obci s alespoň 70 000 obyvateli a
  energetického paušálu, a k tomu jedna čtvrtina na každou osobu, které je
  povinný povinen poskytovat výživné. Manžel nebo partner se nezapočítává,
  s výjimkou přiznaného důchodu podle § 1 odst. 2. Částka se zaokrouhluje na
  celé koruny nahoru (§ 3) a použijí se částky platné **k 1. lednu roku, do
  kterého spadá výplata mzdy** (§ 4).
- Zbytek čisté mzdy se zaokrouhlí dolů na částku dělitelnou třemi v celých
  korunách. Pro nepřednostní pohledávku lze srazit jednu třetinu, pro
  přednostní (§ 279 odst. 2 — výživné, daně, pojistné a další) dvě.
  Přednostní pohledávky se uspokojují nejprve z druhé třetiny a teprve to,
  co nepokryje, se uspokojuje spolu s ostatními z první (§ 279 odst. 1).
- Nad **1,9násobek** uvedeného součtu (§ 2 nařízení) se zbytek srazí bez
  omezení; tato část se připočte k druhé třetině v rozsahu potřebném pro
  přednostní pohledávky, zbytek k první třetině (§ 279 odst. 3).
- Jsou-li na mzdu současně nařízeny **nejméně čtyři výkony rozhodnutí**
  k vymožení peněžitých pohledávek, srážejí se dvě třetiny: přednostní
  pohledávky se i nadále uspokojují nejprve z druhé třetiny, ale co
  nevyčerpají, připadne k první třetině a nezůstává povinnému (§ 279 odst. 4
  a 6). Neplatí to, prokáže-li povinný, že pobírá starobní důchod, invalidní
  důchod pro invaliditu druhého nebo třetího stupně nebo sirotčí důchod,
  **a** zároveň je jedna třetina nižší než měsíční odměna a hotové výdaje
  insolvenčního správce (§ 279 odst. 5).
- Z první třetiny se uspokojují pohledávky podle pořadí bez ohledu na to,
  zda jsou přednostní (§ 280 odst. 1). Z druhé třetiny nejprve výživné bez
  zřetele na pořadí a při nedostatku poměrně podle běžného výživného
  (§ 280 odst. 2 až 4). Pořadí se řídí dnem **doručení nařízení plátci
  mzdy**; nařízení doručená téhož dne mají stejné pořadí a uspokojí se
  poměrně (§ 280 odst. 5).
- Plátce mzdy začne srážet **od prvního dne kalendářního měsíce
  následujícího po doručení** (§ 282a).
- Zjistí-li nový zaměstnavatel nařízené srážky, oznámí to bez odkladu soudu
  (§ 294 odst. 2). Při skončení zaměstnání to plátce mzdy do týdne oznámí
  soudu a zašle vyúčtování provedených srážek, pohledávky a jejich pořadí
  (§ 295 odst. 2). Odcházejícímu zaměstnanci vydá potvrzení o nařízených
  srážkách (§ 294 odst. 1). Odpovídá na dotazy soudu (§ 128 o. s. ř.)
  a exekutora (§ 33 odst. 5 exekučního řádu).

**Slovensko** — [Exekučný poriadok](law:sk/1995/233) (§ 66 až 92) a
[nariadenie vlády č. 268/2006 Z. z.](law:sk/2006/268)

- Čistá mzda je mzda po odečtení zálohy na daň, zdravotního a sociálního
  pojištění a příspěvku na starobní důchodové spoření
  ([§ 69 ods. 1](law:sk/1995/233#paragraf-69.odsek-1)).
- Chráněná *základná suma* závisí na vymáhané pohledávce: 140 % životního
  minima zletilé osoby u nepřednostní pohledávky
  ([§ 1 ods. 1 nariadenia](law:sk/2006/268#paragraf-1.odsek-1)), 100 % u
  přednostní ([§ 2 ods. 2](law:sk/2006/268#paragraf-2.odsek-2)) a 70 % ze
  60 % u výživného pro nezletilé dítě
  ([§ 2 ods. 1](law:sk/2006/268#paragraf-2.odsek-1) ve spojení s
  [§ 70 ods. 2 Exekučného poriadku](law:sk/1995/233#paragraf-70.odsek-2)).
  Použije se životní minimum platné **v měsíci, za který** se sráží.
- Na každou vyživovanou osobu se přičítá 25 % — ze základní sumy, u
  přednostních pohledávek ze 100% základu
  ([§ 1 ods. 2](law:sk/2006/268#paragraf-1.odsek-2),
  [§ 2 ods. 3](law:sk/2006/268#paragraf-2.odsek-3)). Na rozdíl od Česka se
  započítává i manžel se samostatným příjmem. U poživatele důchodových dávek
  je to 50 % ([§ 2a](law:sk/2006/268#paragraf-2a)).
- Nad **trojnásobek** základní sumy podle § 1 ods. 1 se sráží bez omezení
  ([§ 3 ods. 1](law:sk/2006/268#paragraf-3.odsek-1)); částky se zaokrouhlují
  na eurocenty dolů ([§ 4](law:sk/2006/268#paragraf-4)).
- Třetiny, přednostní pohledávky a pořadí fungují jako v Česku, v centech
  ([§ 71 ods. 1 a 2](law:sk/1995/233#paragraf-71.odsek-1),
  [§ 72](law:sk/1995/233#paragraf-72.odsek-2)). Pořadí určuje den doručení
  příkazu na začatie exekúcie
  ([§ 72 ods. 3](law:sk/1995/233#paragraf-72.odsek-3)) a sráží se ode dne
  doručení ([§ 66 ods. 1](law:sk/1995/233#paragraf-66.odsek-1)). Sražené
  částky se vyplácejí **exekutorovi**
  ([§ 81 ods. 1](law:sk/1995/233#paragraf-81.odsek-1)).
- Nástup povinného oznamuje nový zaměstnavatel exekutorovi bez odkladu
  ([§ 84 ods. 2](law:sk/1995/233#paragraf-84.odsek-2)), skončení do týdne
  spolu s vyúčtováním srážek
  ([§ 85 ods. 2](law:sk/1995/233#paragraf-85.odsek-2)).

## Nastavení {#setup}

1. Země společnosti musí být Česko nebo Slovensko. V jiné společnosti mzdy
   nařízení ignorují.
2. Zkontrolujte zákonné částky v *Zaměstnanci → Konfigurace → Garnishment
   Rates* (jen administrátor personalistiky). Dodané hodnoty jsou v části
   [Zákonné částky](#rates). Když se částka změní, přidejte nový záznam
   s datem účinnosti (*Date From*).
3. U zaměstnance, vůči kterému je nařízení, na kartě *Nastavení* ve skupině
   **Wage Garnishment**:

   | Pole | Co dělá |
   |---|---|
   | Maintained Persons (vyživované osoby) | Osoby, kterým je zaměstnanec povinen poskytovat výživné. Každá zvyšuje nezabavitelnou částku. Kdo se započítává, posuďte sami: manžela posuzuje každá země jinak (viz [Právní rámec](#legal)) a nezapočítává se osoba, v jejíž prospěch je nařízena exekuce pro výživné. |
   | Pension Recipient (poživatel důchodových dávek) | Slovensko: na každou vyživovanou osobu se přičte 50 % místo 25 %. Česko: zaměstnanec prokázal, že pobírá starobní důchod, invalidní důchod pro invaliditu druhého nebo třetího stupně nebo sirotčí důchod; pravidlo dvou třetin při čtyřech a více exekucích se pak neuplatní, dokud je jedna třetina nižší než měsíční částka insolvenčního správce (§ 279 odst. 5 o. s. ř.). |

   Národní mzdové moduly mají na smlouvě vlastní pole *Garnishment
   Dependents* pro starší pravidlo s jednou pohledávkou. Je-li *Maintained
   Persons* ponecháno na 0, použije evidence toto pole ze smlouvy (platné ke
   konci období); číslo zadané zde má vždy přednost.

Přístup: personalisté se skupinou *Vedoucí pracovník : Řízení všech
zaměstnanců* vidí a upravují nařízení i srážky, mazat může jen
*Administrátor* personalistiky. Záznamy patří společnosti a výplatní páska
použije vždy jen nařízení své společnosti.

## Evidence nařízení {#orders}

*Zaměstnanci → Garnishments → Orders*, *Nový*.

| Pole | Význam |
|---|---|
| Case Number (spisová značka) | Např. `123 EX 456/2026`. |
| Employee | Povinný. |
| Garnishment Type | *Court execution* (exekuce), *Insolvency* (oddlužení), *Agreement* (dohoda o srážkách ze mzdy) nebo *Administrative enforcement* (správní exekuce). U české společnosti rozhoduje, zda se nařízení započte do čtyř výkonů podle § 279 odst. 4 o. s. ř.: *Court execution* a *Administrative enforcement* ano, *Agreement* a *Insolvency* ne. Jinak výpočet nemění. |
| Claim Class (druh pohledávky) | **Podle něj se počítá.** *Maintenance* (výživné), *Priority* (přednostní) nebo *Ordinary* (nepřednostní); *Administrative fine* je jen slovenský. Převezměte ho z nařízení. Při oddlužení, kde se sráží jako pro přednostní pohledávky, zvolte *Priority*. |
| Delivered On | Den, kdy bylo nařízení doručeno **vám**. Určuje pořadí. |
| Date Start / Date End | Období, na které se nařízení vztahuje. *Date Start* se u české společnosti předvyplní **prvním dnem měsíce následujícího po doručení** (§ 282a o. s. ř.), u slovenské dnem doručení. Lze ho změnit; ruční hodnota zůstane, dokud se nezmění *Delivered On*. |
| Total Claim | Jistina, náklady a úroky podle nařízení. U běžného výživného bez celkové částky nechte 0. |
| Monthly Maintenance | Běžné měsíční výživné. Bez celkové částky je nařízení neukončené a samo se nikdy neuzavře. |
| Arrears | Dlužné výživné, které se sráží vedle běžného (zobrazí se jen u výživného). |
| Creditor, Bailiff | Oprávněný a soudní exekutor. Je-li exekutor vyplněn, peníze jdou jemu. |
| Payee, Payee Bank Account | Příjemce (počítá se) a jeho účet. Účet jiného subjektu nelze uložit. |
| Variable Symbol | Číslice spisové značky, posledních 10; lze přepsat. Specifický a konstantní symbol podle nařízení. |

Nařízení musí mít celkovou částku nebo měsíční výživné. Samotné nařízení
přiložte na kartě *Document*.

**Stavy.** Nařízení ve stavu *Draft* mzdy ignorují. **Start** ho převede do
stavu *Running* — srážejí se jen probíhající nařízení. **Suspend** ho
pozastaví (např. při odkladu výkonu), **Mark Settled** uzavře, **Cancel**
zruší, **Reset to Draft** vrátí pozastavené nebo zrušené nařízení do
konceptu. Nařízení, jehož celková částka byla sražena, se uzavře samo, když
se potvrdí výplatní páska, která ho doplatila; zrušení nebo vrácení této
pásky do konceptu ho znovu otevře.

Na formuláři zaměstnance je tlačítko **Garnishments** s počtem probíhajících
nařízení.

## Na výplatní pásce {#payslip}

Pravidlo národních mezd **Wage Garnishment** (`GARNISHMENT`) běží po dani a
pojistném. Má-li zaměstnanec probíhající nařízení společnosti výplatní
pásky, evidence spočítá srážku z čisté mzdy pásky přes všechna probíhající
nařízení, jejichž období se s páskou překrývá, a pravidlo srazí celkovou
částku.

Dokud je páska koncept, do nařízení se nezapisuje nic, ať se přepočítá
kolikrát chce. Když pásku **potvrdíte** (*Potvrdit*), zaznamená se ze stejné
čisté mzdy jedna srážka za každé nařízení a páska je ukáže na kartě
**Garnishments**. Všechny najdete v *Zaměstnanci → Garnishments →
Deductions*.

- **Zrušit** nebo **Uložit jako koncept** na pásce smaže její srážky, které
  ještě nebyly poukázány.
- Pásku, jejíž srážka už byla **poukázána**, nelze zrušit ani vrátit do
  konceptu; nejprve stornujte poukázání.
- Zaměstnanci bez zaevidovaného nařízení zůstávají na starším pravidle
  národních mezd se vstupy, takže na evidenci můžete přecházet po jednom
  zaměstnanci.

## Jak se srážka počítá {#calculation}

**Česko**, v celých korunách:

1. Nezabavitelná částka = 85 % × (životní minimum + normativní nájemné +
   energetický paušál) × (1 + ¼ × vyživované osoby), zaokrouhleno nahoru.
2. Zbytek = čistá mzda − nezabavitelná částka. Do hranice se zaokrouhlí
   dolů na násobek tří a rozdělí na třetiny; nad hranicí se srazí celý.
3. **Druhá třetina**: nejprve výživné bez ohledu na pořadí, při nedostatku
   poměrně podle běžného výživného; potom ostatní přednostní pohledávky podle
   pořadí. Co přednostní pohledávky nevyčerpají, zůstává zaměstnanci —
   neuplatní-li se pravidlo dvou třetin (krok 6).
4. **První třetina**: vše dosud neuhrazené — přednostní i nepřednostní —
   podle pořadí; při stejném pořadí poměrně podle dlužné částky.
5. Plně zabavitelná část nad hranicí se přičte k druhé třetině v rozsahu
   potřebném pro přednostní pohledávky, zbytek k první třetině.
6. **Čtyři a více exekucí** (§ 279 odst. 4 až 6): jsou-li alespoň čtyři
   probíhající nařízení zaměstnance typu *Court execution* nebo
   *Administrative enforcement*, přičte se to, co přednostní pohledávky
   z druhé třetiny nevyčerpají, k první třetině a rozdělí se mezi všechny
   pohledávky podle pořadí. Neplatí to, je-li zaměstnanec označen jako
   *Pension Recipient* a jedna třetina je nižší než *Insolvency trustee
   monthly amount* (§ 279 odst. 5).

Příklad (2026): čistá mzda 30 000 Kč, jedno vyživované dítě, jedna
nepřednostní pohledávka. Nezabavitelná částka 14 101,50 + 3 525,375 =
17 626,875 → **17 627 Kč**. Zbytek 12 373 → 12 372, třetina **4 124 Kč** —
oprávněný dostane 4 124 Kč, zaměstnanci zůstane 25 876 Kč.

**Slovensko**, v centech: stejný postup, ale chráněný základ závisí na druhu
pohledávky (140 %, 100 %, 70 % × 60 % nebo 50 % životního minima). Modul
spočítá třetiny zvlášť pro každý přítomný druh pohledávky, přednostní
pohledávky čerpají svou druhou třetinu a část nad hranicí a neuhrazený zbytek
soutěží v první třetině. Dvě pojistky drží výpočet na bezpečné straně: žádné
nařízení nedostane víc, než by mu dovolil jeho vlastní druh samostatně, a
zaměstnanci vždy zůstane alespoň nejnižší základ z nařízení, ze kterých se
skutečně sráželo. Co pojistky uberou, zůstává zaměstnanci.

## Zákonné částky {#rates}

| Země | Platí od | Částky |
|---|---|---|
| CZ | 1. 1. 2026 | životní minimum 4 860 Kč, normativní nájemné 9 430 Kč, energetický paušál 2 300 Kč (součet 16 590 Kč); 85 %; ¼ na osobu; bez omezení nad 31 521 Kč (1,9 × 16 590); měsíční částka insolvenčního správce (*Insolvency trustee monthly amount*) 1 089 Kč ((750 + 150) × 1,21, vyhl. 313/2007 Sb.) |
| SK | 1. 7. 2024 | životné minimum 273,99 € |
| SK | 1. 7. 2025 | životné minimum 284,13 € |
| SK | 1. 7. 2026 | životné minimum 295,22 € |

Slovenské koeficienty jsou ve všech záznamech stejné: nepřednostní 140 %,
přednostní 100 %, výživné pro nezletilé dítě 70 % × 60 %, pokuta 50 %, 25 %
na osobu (50 % u poživatele důchodových dávek), bez omezení nad trojnásobkem
základní sumy.

Český záznam před rokem 2026 se nedodává: reforma 2026 změnila samotný
vzorec. Od 1. 10. 2026 činí životní minimum jednotlivce 5 500 Kč, ale podle
§ 4 nařízení se pro mzdy vyplácené v roce 2026 použije částka k 1. lednu;
před výpočtem mezd vyplácených v roce 2027 přidejte záznam pro rok 2027.

## Oznámení a vyúčtování srážek {#notices}

*Zaměstnanci → Garnishments → Statutory Notices* vytiskne pro jednoho
zaměstnance a některá nebo všechna jeho nařízení:

| Notice Type | Obsah |
|---|---|
| Notice of employment start (oznámení o nástupu) | povinný nastoupil dne *Event Date*; nařízení v evidenci |
| Notice of employment end (oznámení o skončení) | povinný odešel dne *Event Date*; stav každého nařízení |
| Answer to an enquiry (odpověď na dotaz) | nařízení v pořadí s pohledávkou, sraženou částkou a zůstatkem |
| Account of deductions (vyúčtování srážek) | nařízení a všechny srážky období rozdělené na druhou a první třetinu, s údajem o poukázání |

Adresát (*Addressee*) se předvyplní příjemcem prvního vybraného nařízení.
Tiskopisy jsou v angličtině s českým nadpisem a podepisují se ručně. Pod
nadpisem oznámení cituje ustanovení podle země společnosti:

| Notice Type | Česká společnost | Slovenská společnost |
|---|---|---|
| Notice of employment start | § 294 odst. 2 o. s. ř. | § 84 ods. 2 Exekučného poriadku |
| Notice of employment end | § 295 odst. 2 o. s. ř. | § 85 ods. 2 Exekučného poriadku |
| Answer to an enquiry | § 128 o. s. ř. / § 33 odst. 5 exekučního řádu | *Odpoveď na žiadosť exekútora* (bez paragrafu) |

## Mzdová jádra {#engines}

Evidenci s mzdovou aplikací spojují dva můstky. Každý se nainstaluje sám,
je-li nainstalováno jeho jádro i tento modul:

| | Enterprise | OCA |
|---|---|---|
| Modul | [module:l10n_cssk_hr_payroll_garnishment_ee](module:l10n_cssk_hr_payroll_garnishment_ee) | [module:l10n_cssk_hr_payroll_garnishment_oca](module:l10n_cssk_hr_payroll_garnishment_oca) |
| Mzdová aplikace | *Mzdy* Odoo Enterprise (`hr_payroll`) | OCA `payroll` |

Dělají totéž: zaznamenají srážky při potvrzení pásky, smažou je při jejím
zrušení nebo vrácení do konceptu, odmítnou zrušit nebo vrátit do konceptu
pásku, jejíž srážka už byla poukázána, a přidají na pásku kartu *Garnishments*. Částka na
pásce potřebuje jen tento modul a národní mzdové pravidlo; bez můstku by se
však k nařízením nic nezaznamenalo a nařízení by se nikdy neuzavřela.

## Poukázání příjemci {#accounting}

[module:l10n_cssk_hr_payroll_garnishment_account](module:l10n_cssk_hr_payroll_garnishment_account)
se nainstaluje sám spolu s `account` a
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols).

Mzdový doklad účtuje všechny srážky ve prospěch jednoho souhrnného závazku
(např. 379). Poukázání přesune podíl každého nařízení na příjemce:

    MD  souhrnný závazek ze srážek
        D  závazek vůči exekutorovi nebo oprávněnému (s partnerem)

jeden zaúčtovaný doklad za každé nařízení, se symboly a bankovním účtem
příjemce z nařízení. Otevřený závazek se pak uhradí jako kterýkoli
dodavatel — platebním příkazem a bankovním souborem nebo spárováním
s výpisem.

1. *Účetnictví → Konfigurace → Nastavení* (v Community bez plného účetnictví
   *Fakturace → Konfigurace → Nastavení*), blok **Wage Garnishments**:
   zvolte **Garnishment Remittance Journal** (deník typu Ostatní) a
   **Garnishment Liability Account** — tentýž účet, na který mzdové účtování
   účtuje srážky.
2. Příjemce musí mít vyplněný účet závazků.
3. Buď *Zaměstnanci → Garnishments → Remit to Payees*: zvolte *Up To*
   a případně *Only This Payee*, zkontrolujte seznam a klikněte na
   **Remit**; nebo v *Deductions* označte srážky a klikněte na
   **Remit to Payee**.

Doklad má datum posledního konce období, které pokrývá. Poukázané srážky
jsou ve stavu *Remitted* a nelze je smazat. Nabídku a tlačítko vidí
*Administrátor* účetnictví a uživatelé ve skupině *Show Full Accounting
Features*; nabídka je pod *Zaměstnanci*, takže je třeba i role
v personalistice. Účetní na srážce nezmění nic kromě údajů o poukázání.

## Omezení {#limitations}

- **Česká nařízení zaevidovaná před verzí 19.0.1.2.2** si ponechají tehdy
  uložené *Date Start* — den doručení. U nařízení, jejichž měsíc doručení
  ještě nebyl vyplacen, ho posuňte na první den následujícího měsíce.
- **Rok výplaty.** Použijí se částky k 1. lednu roku, v němž se mzda
  **vyplácí** (§ 4 nařízení). Datum výplaty se vezme z výplatní pásky, pokud
  ho mzdové jádro eviduje (Enterprise *Datum platby*, jakmile je páska
  zaplacena); jinak se předpokládá výplata v měsíci po období, nejpozději
  jak dovoluje zákoník práce. Mzda vyplacená ve vlastním měsíci na přelomu
  roku — prosincová mzda vyplacená v prosinci — proto na jádru OCA použije
  částky následujícího roku.
- **Paušální náhrada nákladů plátce mzdy** (50 Kč měsíčně, § 279 odst. 1
  o. s. ř. a § 4d až 4e vyhlášky č. 485/2000 Sb.) se nepočítá ani nesráží.
  Plátce mzdy se jí může vzdát; uplatňujete-li ji, srazte ji mimo evidenci.
- **Slovenské zaokrouhlování** se řídí § 4 nariadenia: chráněné částky
  i hranice srážek bez omezení se zaokrouhlují dolů na centy. Suma na
  povinného a suma na osobu se zaokrouhlují zvlášť (od 1. 7. 2026 413,30 € +
  103,32 € na osobu), jak je odstavce vymezují; zaokrouhlení jen jejich
  součtu by mohlo chránit o cent víc.
- **Slovenské pokuty.** Druh *Administrative fine* používá 50 % životního
  minima plus 25 % na osobu. Tento základ (§ 2b nariadenia) se týká pokut
  vymáhaných z dávek, které jinak exekuci nepodléhají, a nic na osobu
  nepřičítá; před použitím na mzdu to prověřte.
- **Kombinace různých druhů pohledávek** na Slovensku je modelové řešení tam,
  kde zákon mlčí; výsledek dejte zkontrolovat.
- **Jazyk oznámení.** Tiskopisy jsou anglické s českým nadpisem i pro
  slovenské společnosti a potvrzení pro odcházejícího zaměstnance (§ 294
  odst. 1) se netiskne.
- **Jen mzda.** Nemocenské, důchody a jiné příjmy vyplácené třetími osobami
  modul neřeší, stejně jako nižší srážky podle § 287 nebo dlužnou mzdu
  vyplacenou najednou za více měsíců (každý měsíc se počítá zvlášť, § 286).
- Podíl srážky z části nad hranicí (*From Unlimited Part*) se nesleduje;
  započítá se do třetin.
