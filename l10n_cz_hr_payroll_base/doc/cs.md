---
title: Česká mzdová agenda
summary: Česká mzdová agenda na jednom místě — měsíční výplatní páska pro pracovní poměr, DPP a DPČ v aplikaci OCA payroll nebo v Odoo Enterprise Payroll, s datovanými zákonnými sazbami, nepřítomnostmi, ročním zúčtováním daně a zaúčtováním do hlavní knihy.
verified: 19.0.1.1.0
---

## Na co slouží {#purpose}

Česká mzdová agenda se dodává jako skupina modulů. Tato stránka popisuje
skupinu jako celek; jednotlivé moduly mají krátké stránky, které odkazují
sem.

| Modul | Co dělá |
|---|---|
| [module:l10n_cz_hr_payroll_base](module:l10n_cz_hr_payroll_base) (tento modul) | České údaje zaměstnance (druh pracovního vztahu, prohlášení poplatníka, děti, příznaky pojištění) a zákonné akruální plány dovolené. Nezávislý na mzdovém jádru, bez vlastních obrazovek. |
| [module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca) | Česká výplatní páska v **aplikaci OCA payroll** (`payroll`) pro Odoo Community. |
| [module:l10n_cz_hr_payroll_ee](module:l10n_cz_hr_payroll_ee) | Tatáž výplatní páska v **Odoo Enterprise Payroll** (`hr_payroll`). Odoo vlastní českou mzdovou lokalizaci nemá, jde tedy o úplnou lokalizaci, ne o nadstavbu. |
| [module:l10n_cz_hr_payroll_account_oca](module:l10n_cz_hr_payroll_account_oca), [module:l10n_cz_hr_payroll_account_ee](module:l10n_cz_hr_payroll_account_ee) | Zaúčtování výplatních pásek podle české účtové osnovy, pro každé jádro zvlášť. |
| [module:l10n_cz_hr_payroll_surcharges](module:l10n_cz_hr_payroll_surcharges) | Příplatky ke mzdě za práci přesčas, ve svátek, v noci, v sobotu a v neděli a ve ztíženém pracovním prostředí. |
| [module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base) | Evidence srážek ze mzdy, společná se Slovenskem. |
| Zákonná hlášení | Viz [Hlášení úřadům](#declarations). |

Základní modul obsahuje to, co na mzdovém jádru nezávisí: české údaje ve
smlouvě zaměstnance a akruální plány dovolené. Instaluje se automaticky jako
závislost modulů mzdového jádra a setkáte se s ním jen jejich
prostřednictvím. Každý modul mzdového jádra má vlastní mzdovou strukturu,
pravidla, zákonné hodnoty, typy nepřítomnosti a obrazovky.

## Volba mzdového jádra {#engines}

Obě jádra počítají stejná mzdová pravidla ze stejných datovaných hodnot.
Volíte tedy mzdovou aplikaci, ne česká pravidla.

| | OCA (`_oca`) | Enterprise (`_ee`) |
|---|---|---|
| Mzdová aplikace | OCA `payroll`, funguje v Community | Odoo Enterprise *Mzdy* (`hr_payroll`) |
| Instalace | ručně | automaticky, jakmile jsou nainstalovány Enterprise *Mzdy* a jejich propojení s nepřítomnostmi |
| Mzdová struktura | *Česká republika: Řádná mzda* (`CZMONTHLY`) | tatáž, pod typem struktury *Czech Republic: Employee* |
| Česká pole jsou | na kartě zaměstnance, záložka *Mzdy*, skupina **Česká mzdová agenda**, a na vzoru smlouvy | na kartě zaměstnance, záložka *Mzdy*, skupina **Česká mzdová agenda**, a na vzoru smlouvy |
| Nepřítomnosti se do pásky dostanou přes | **Český mzdový kód** na typu nepřítomnosti | typy pracovních záznamů (*CZHOLIDAY*, *CZSICK*, …) |
| Základní mzda za neúplný měsíc | mzda ze smlouvy × odpracované hodiny ÷ hodiny podle rozvrhu | vlastní krácení Odoo podle pracovních záznamů |
| Ručně zadávané hodiny a částky | řádek *Ostatní vstupy* s ručně zapsaným **kódem** vstupu | *Jiný vstup* příslušného typu nebo úprava mzdy |
| Zákonné sazby vidíte v | *Mzdy → Konfigurace → Parametry pravidel* | *Mzdy → Konfigurace → Mzdy → Parametry pravidel* |
| Výplatní páska v PDF | standard OCA | *CZ: Výplatní páska*, tištěná v jazyce zaměstnance |

Druh pracovněprávního vztahu není v žádném z jader samostatnou strukturou.
Určuje ho pole **Typ pracovněprávního vztahu** na smlouvě: *Pracovní poměr*,
*DPP (dohoda o provedení práce)* nebo *DPČ (dohoda o pracovní činnosti)*.

## Právní rámec {#legal}

Hodnoty, se kterými páska počítá, vycházejí z těchto předpisů. Odkazy na
paragrafy byly ověřeny proti úplným zněním účinným v říjnu 2026.

- **Sociální pojištění.** Zaměstnanec platí 7,1 % (6,5 % důchodové, 0,6 %
  nemocenské), zaměstnavatel 24,8 % (21,5 % důchodové, 2,1 % nemocenské,
  1,2 % státní politika zaměstnanosti) podle
  [§ 7 zákona č. 589/1992 Sb.](law:cz/1992/589). Roční vyměřovací základ je
  omezen čtyřicetiosminásobkem průměrné mzdy
  ([§ 15a](law:cz/1992/589)). Slevu na pojistném ve výši 5 % vyměřovacího
  základu u vybraných zaměstnanců s kratší pracovní dobou upravují
  [§ 7a a § 7b](law:cz/1992/589).
- **Zdravotní pojištění** činí 13,5 % z vyměřovacího základu
  ([§ 2 zákona č. 592/1992 Sb.](law:cz/1992/592)), zaokrouhleno na celé
  koruny nahoru u každého zaměstnance, třetinu hradí zaměstnanec
  ([§ 9 odst. 2 zákona č. 48/1997 Sb.](law:cz/1997/48)). Minimálním
  vyměřovacím základem je minimální mzda, krácená podle kalendářních dnů za
  neúplný měsíc trvání zaměstnání a za dny důležitých osobních překážek,
  například nemoci ([§ 3 odst. 6 a 9](law:cz/1992/592)). Zaměstnanec s
  nižším základem doplácí 13,5 % z rozdílu, ledaže je základ nižší z důvodu
  překážek na straně zaměstnavatele — pak rozdíl doplácí zaměstnavatel
  ([§ 3 odst. 10](law:cz/1992/592)); minimální vyměřovací základ neplatí pro
  osoby uvedené v § 3 odst. 8, mezi nimi pro držitele průkazu ZTP a ZTP/P a
  pro ty, za které platí pojistné stát.
- **Dohody.** Zaměstnanec na DPP je účasten nemocenského pojištění v měsíci,
  kdy příjem dosáhne 25 % průměrné mzdy zaokrouhlených na celé pětisetkoruny
  dolů ([§ 7a zákona č. 187/2006 Sb.](law:cz/2006/187)); na DPČ, jako u
  každého jiného zaměstnání, od rozhodného příjmu
  ([§ 6 odst. 2](law:cz/2006/187)). Pod těmito částkami a bez podepsaného
  prohlášení se příjem zdaňuje srážkovou daní
  ([§ 6 odst. 4 zákona o daních z příjmů](law:cz/1992/586)).
- **Daň z příjmů.** Měsíční záloha činí 15 % ze základu a 23 % z části
  přesahující trojnásobek průměrné mzdy; základ se zaokrouhluje na celé
  stokoruny nahoru ([§ 38h odst. 1 a 2](law:cz/1992/586)). Slevy na dani
  upravuje [§ 35ba](law:cz/1992/586), daňové zvýhodnění a bonus
  [§ 35c a § 35d](law:cz/1992/586); měsíční bonus se vyplácí jen tehdy,
  dosáhne-li příjem za měsíc poloviny minimální mzdy. Prohlášení poplatníka
  se podepisuje do 30 dnů po nástupu a každoročně do 15. února
  ([§ 38k odst. 4](law:cz/1992/586)). Roční zúčtování upravuje
  [§ 38ch](law:cz/1992/586).
- **Stravenkový paušál** je osvobozen do 70 % horní hranice stravného při
  pracovní cestě trvající 5 až 12 hodin
  ([§ 6 odst. 9 písm. b)](law:cz/1992/586)).
- **Minimální mzda a náhrady mzdy.** Minimální mzdu upravuje
  [§ 111 zákoníku práce](law:cz/2006/262) a vyhlašuje ji sdělení MPSV (pro
  rok 2026 č. 356/2025 Sb.). Nižší mzdu dorovnává doplatek, porovnávaný za
  hodinu, nebyla-li předem sjednána měsíční minimální mzda; mzda za práci
  přesčas a příplatky se do mzdy pro tento účel nezahrnují
  ([§ 111 odst. 1 a 2](law:cz/2006/262)). Za hodinu práce přesčas přísluší
  dosažená mzda a příplatek ([§ 114 odst. 1](law:cz/2006/262)). Za dovolenou přísluší náhrada mzdy ve výši
  průměrného výdělku ([§ 222](law:cz/2006/262)); za překážky na straně
  zaměstnavatele nejméně 80 % při prostoji a 60 % při nepříznivých
  povětrnostních vlivech ([§ 207](law:cz/2006/262)), 100 % u jiných překážek
  ([§ 208](law:cz/2006/262)) a nejméně 60 % při částečné nezaměstnanosti jen
  na základě dohody s odborovou organizací nebo vnitřního předpisu
  ([§ 209](law:cz/2006/262)). Náhrada mzdy za prvních 14 kalendářních dnů
  dočasné pracovní neschopnosti činí 60 % redukovaného průměrného výdělku;
  redukční hranice nemocenského pojištění se násobí koeficientem 0,175 a
  zaokrouhlují na haléře nahoru ([§ 192](law:cz/2006/262)). Náhrada se daní
  jako příjem ze závislé činnosti, pojistné se z ní neplatí. Průměrný výdělek
  upravují §§ 351–362.
- **Dovolená** činí nejméně 4 týdny v kalendářním roce
  ([§ 212](law:cz/2006/262)) a vzniká v hodinách podle odpracovaných týdnů
  ([§ 213](law:cz/2006/262)); nevyčerpanou dovolenou musí zaměstnavatel
  určit k čerpání nejpozději do konce následujícího roku
  ([§ 218](law:cz/2006/262)).

## Nastavení {#setup}

1. Nainstalujte modul mzdového jádra: v Community
   [module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca), v
   Enterprise se [module:l10n_cz_hr_payroll_ee](module:l10n_cz_hr_payroll_ee)
   nainstaluje sám spolu s *Mzdami*. Mají-li se výplatní pásky účtovat,
   přidejte účetní modul (viz [Zaúčtování do hlavní knihy](#accounting)).
2. Společnost musí mít sídlo v České republice. Česká mzdová struktura, typy
   nepřítomností a (v Enterprise) česká pole zaměstnance vidí jen české
   společnosti.
3. Přiřaďte smlouvě každého zaměstnance českou mzdovou strukturu (OCA) nebo
   typ struktury *Czech Republic: Employee* (Enterprise) a vyplňte české
   údaje popsané níže.
4. V Enterprise před první výplatní páskou nového roku zkontrolujte hodnoty
   v *Mzdy → Konfigurace → Mzdy → Parametry pravidel*.

## Údaje zaměstnance a smlouvy {#employees}

| Pole | Co dělá |
|---|---|
| Typ pracovněprávního vztahu | *Pracovní poměr*, *DPP* nebo *DPČ*. Určuje hranice účasti na pojištění a použití srážkové daně. |
| Podepsané prohlášení poplatníka | Zaměstnanec podepsal u tohoto zaměstnavatele prohlášení poplatníka: uplatní se měsíční slevy na dani a daňové zvýhodnění a dohoda pod hranicí se zdaní zálohou místo srážkové daně. |
| Zaměstnanec je držitelem ZTP/P, Stupeň invalidity | Přidá slevu na držitele ZTP/P, nebo základní (I./II. stupeň) či rozšířenou (III. stupeň) slevu na invaliditu. |
| Osoba, za kterou platí pojistné stát | Neuplatní se minimální vyměřovací základ zdravotního pojištění. Zaškrtněte jen tehdy, trvá-li některá z výjimek podle § 3 odst. 8 po celý měsíc. |
| Stravenkový paušál / směna | Stravenkový paušál za směnu, omezený osvobozeným limitem a vyplácený za každý odpracovaný den. |
| Průměrný hodinový výdělek | Nahradí vypočtený průměrný hodinový výdělek (nikdy ne pod hodinovou minimální mzdu). Ponechte prázdné, má-li ho páska spočítat sama. |
| Vyživované osoby pro exekuci | Vyživované osoby zvyšující nezabavitelnou částku, zadává-li se srážka jako vstup výplatní pásky. |
| Kategorie slevy na pojistném | Jedna z kategorií podle § 7a pro 5% slevu zaměstnavatele. |
| Děti (1. dítě), Děti (2. dítě), Děti (3. a další dítě), z toho dětí se ZTP/P | Počet dětí pro daňové zvýhodnění podle pořadí. |

## Jak se výplatní páska počítá {#payslip}

V pořadí, v jakém pravidla běží:

1. **Základní mzda.** Mzda ze smlouvy krácená o každou nepřítomnost v
   období.
2. **Příplatky ke mzdě** a **Mzda za práci přesčas** za hodiny přesčas, je-li
   nainstalována skupina příplatků.
3. **Náhrady mzdy** ve výši průměrného hodinového výdělku: *Náhrada mzdy za
   dovolenou*, *Náhrada za překážky v práci* (lékař, doprovod, dárcovství
   krve, veřejná funkce a další důvody podle §§ 199–206) a *Employer Work
   Obstacle (§§ 207-209)* ve výši 80, 60 nebo 100 % (částečná
   nezaměstnanost: sazba sjednaná společností, ve výchozím stavu 100 %).
   Průměrný hodinový
   výdělek je základní mzda z potvrzených výplatních pásek předchozího
   kalendářního čtvrtletí dělená jejich odpracovanými hodinami; bez takového
   čtvrtletí mzda ze smlouvy dělená hodinami období podle rozvrhu; nikdy
   méně než hodinová minimální mzda.
4. **Náhrada mzdy při nemoci**: 60 % průměrného hodinového výdělku
   redukovaného třemi redukčními hranicemi (90 / 60 / 30 %) za hodiny
   pracovní neschopnosti připadající na prvních 14 kalendářních dnů (nebo
   podle vstupu *Hodiny nemoci*), zaokrouhleno na celé koruny nahoru.
   Navazující žádosti o nepřítomnost se počítají jako jedna neschopnost.
   Nevstupuje do hrubé mzdy, pojistné se z ní tedy neplatí, je však součástí
   základu daně a čisté mzdy.
5. **Doplatek do minimální mzdy**, je-li nainstalována skupina příplatků
   (viz její stránka), a **Hrubá mzda.**
6. **Sociální pojištění** zaměstnance a zaměstnavatele z hrubé mzdy do výše
   zbytku ročního maxima po dřívějších potvrzených páskách roku. **Sleva na
   pojistném (zaměstnavatel)** u oprávněného zaměstnance v pracovním poměru:
   hrubá mzda nejvýše 1,5násobek průměrné mzdy a nejvýše 1,15 % průměrné
   mzdy na hodinu (odpracované hodiny a hodiny s náhradou mzdy); kromě
   mladších 21 let navíc sjednaná týdenní pracovní doba 8–30 hodin a nejvýše
   138 hodin v měsíci. Snižuje náklady zaměstnavatele, ne pojistné.
7. **Zdravotní pojištění**: 13,5 % z hrubé mzdy zaokrouhleno na celé koruny
   nahoru; zaměstnanec hradí třetinu zaokrouhlenou nahoru, zaměstnavatel
   zbytek. Je-li hrubá mzda zaměstnance v pracovním poměru nižší než
   minimální vyměřovací základ — minimální mzda krácená o kalendářní dny mimo
   zaměstnání a dny nemoci, ošetřování člena rodiny, placených osobních
   překážek a mateřské či rodičovské dovolené — doplatí zaměstnanec navíc
   13,5 % z rozdílu. Je-li na pásce překážka na straně zaměstnavatele, doplatí
   jej zaměstnavatel; u osoby, za kterou platí pojistné stát, a u držitele
   ZTP/P se nedoplácí.
8. Dohody pod svou hranicí neplatí žádné pojistné.
9. **Základ daně** = hrubá mzda a náhrada mzdy při nemoci. **Záloha na daň z příjmů**: základ
   zaokrouhlený na celé stokoruny nahoru, 15 % do měsíční hranice a 23 % nad
   ni. U dohody pod hranicí bez prohlášení místo ní **Srážková daň**: 15 % z
   hrubé mzdy v celých korunách, bez slev.
10. **Slevy na dani** při podepsaném prohlášení, nejvýše do výše zálohy.
11. **Daňové zvýhodnění na dítě** do výše zbývající daně a **Daňový bonus na
    dítě** za zbytek, dosáhne-li základ daně poloviny minimální mzdy.
12. **Exekuční srážky ze mzdy** a další srážky (viz [Srážky ze
    mzdy](#garnishment)), **Proplacení výdajů** a případně **Roční zúčtování
    daně**.
13. **Stravenkový paušál**, mimo hrubou mzdu.
14. **Čistá mzda** a souhrny zaměstnavatele.

## Zákonné hodnoty {#rates}

Každá sazba a částka je datovaná hodnota, páska tedy použije hodnotu platnou
k jejímu datu. Dodávané hodnoty:

| Hodnota | 2025 | 2026 |
|---|---|---|
| Průměrná mzda (pro pojistné a daň) | 46 557 Kč | 48 967 Kč |
| Sociální pojištění zaměstnanec / zaměstnavatel | 7,1 % / 24,8 % | beze změny |
| Maximální roční vyměřovací základ (48×) | 2 234 736 Kč | 2 350 416 Kč |
| Zdravotní pojištění zaměstnanec / zaměstnavatel | 4,5 % / 9 % | beze změny |
| Minimální mzda měsíční / hodinová (= minimální vyměřovací základ ZP) | 20 800 Kč / 124,40 Kč | 22 400 Kč / 134,40 Kč |
| Hranice pro DPP (25 % průměrné mzdy) | 11 500 Kč | 12 000 Kč |
| Rozhodný příjem pro DPČ | 4 500 Kč | 4 500 Kč |
| Daň z příjmů | 15 %, 23 % nad 139 671 Kč měsíčně | 15 %, 23 % nad 146 901 Kč měsíčně |
| Sleva na poplatníka měsíčně / ročně | 2 570 / 30 840 Kč | beze změny |
| Sleva na držitele ZTP/P měsíčně / ročně | 1 345 / 16 140 Kč | beze změny |
| Sleva na invaliditu I./II., III. stupně (měsíčně) | 210 / 420 Kč | beze změny |
| Daňové zvýhodnění měsíčně na 1. / 2. / 3. a další dítě | 1 267 / 1 860 / 2 320 Kč | beze změny |
| Podmínka příjmu pro měsíční bonus (½ minimální mzdy) | 10 400 Kč | 11 200 Kč |
| Osvobozený stravenkový paušál za směnu | 123,90 Kč | 129,50 Kč |
| Redukční hranice náhrady mzdy (hodinové) | 271,60 / 407,40 / 814,80 Kč | 285,78 / 428,58 / 856,98 Kč |
| Sleva na pojistném | 5 %, základ nejvýše 1,5× průměrné mzdy a 1,15 % průměrné mzdy na hodinu, 138 hodin | beze změny |

Sazby náhrad za překážky na straně zaměstnavatele (80 / 60 / 100 % a 60 %
jako spodní hranice pro částečnou nezaměstnanost) a
roční limity odpočtů (48 000 Kč na penzijní a životní pojištění, 150 000 Kč
na úroky z úvěru na bydlení, 30 % základu na dary) platí od roku 2024. V
Enterprise hodnotu pro další rok přidáte jako novou datovanou hodnotu v
*Parametrech pravidel*.

## Nepřítomnosti {#leave}

Moduly mzdového jádra dodávají české typy nepřítomností. V Enterprise je
každý navázán na typ pracovního záznamu, v OCA na český mzdový kód. Názvy
typů, které modul nepřekládá, se zobrazují anglicky:

| Kód | Typy nepřítomnosti | Ve výplatní pásce |
|---|---|---|
| CZHOLIDAY | Dovolená | náhrada ve výši průměrného výdělku |
| CZSICK | Nemoc, Quarantine / Isolation (karanténa) | základ náhrady mzdy při nemoci |
| CZOCR | Ošetřování člena rodiny (OČR), Krátkodobé ošetřovné (OČR) — limit 9 dní (16 pro osamělého rodiče), Dlouhodobé ošetřovné — limit 90 dní | zaměstnavatel neplatí (dávka ČSSZ) |
| CZUNPAID | Neplacené volno, Study Leave, unpaid (zvyšování kvalifikace) | neplaceno |
| CZOBSTACLE | Placená překážka - lékař / doprovod, Blood Donation (dárcovství krve, § 203), Public Office (výkon veřejné funkce, § 201), Other Acts in the Public Interest (§ 202), Study Leave, paid (§ 232), Transport of a Disabled Child to a Facility — 6 days/year, Doprovod k lékaři — max 1 den (placeno) | náhrada ve výši průměrného výdělku |
| CZPROSTOJ, CZPOVETRNOST, CZJINEPREKAZKY, CZCASTECNA | čtyři překážky na straně zaměstnavatele (§ 207 písm. a), § 207 písm. b), § 208, § 209) | náhrada v příslušném procentu |
| CZMATERSKA, CZRODICOVSKA, CZOTCOVSKA | Maternity Leave (mateřská, § 195), Parental Leave (rodičovská, § 196), Paternity Leave (otcovská) | zaměstnavatel neplatí |

Typy ošetřování a doprovodu s limitem vyžadují alokaci; doprovod zdravotně
postiženého dítěte do zařízení má vlastní plán, který přiděluje 6 dnů ročně.

**Akruální plány dovolené** dodává základní modul, takže jsou v obou jádrech
stejné. *Zákonná dovolená – 4 týdny (160 h/rok)* a
*Dovolená – 5 týdnů (200 h/rok)* přidělují dovolenou v hodinách za každý
odpracovaný týden ve výši 1/52 ročního nároku, za část roku tedy vznikne
poměrná část. Počítají se 40hodinovým týdnem. Nevyčerpaná dovolená se
převádí do dalšího roku a nepropadá: [§ 218](law:cz/2006/262) propadnutí
nezná. Převedenou dovolenou je zaměstnavatel povinen určit tak, aby byla
vyčerpána do konce následujícího roku, po 30. červnu ji může určit i
zaměstnanec a dovolená nevyčerpaná do skončení pracovního poměru se proplácí
([§ 222 odst. 2](law:cz/2006/262)). Dva alternativní plány, které
přidělí celý roční nárok k 1. 1., se dodávají archivované. Plány nejsou
navázány na typ *Dovolená*; přiřaďte je jednotlivým zaměstnancům alokací
(*Volno → Alokace*).

## Roční zúčtování daně {#tax-reconciliation}

*Mzdy → Výplatní pásky → Roční zúčtování daně* (v OCA *Mzdy → CZ roční
zúčtování daně*) obsahuje jeden záznam na zaměstnance a zdaňovací období pro
roční zúčtování záloh a daňového zvýhodnění.

1. Založte záznam pro zaměstnance a **Rok** (výchozí je předchozí rok).
2. Do skupiny **Nezdanitelné části základu daně (§15)** zadejte údaje z
   dokladů zaměstnance: příspěvky na penzijní připojištění, DPS, DIP a
   životní pojištění (společně 48 000 Kč), úroky z úvěru na bydlení
   (150 000 Kč), dary (do 30 % základu) a **Slevu na manžela/manželku** v
   uplatnitelné výši. *Odborové příspěvky* a *Zkoušky dalšího vzdělávání* se
   evidují, ale od roku 2024 se neodečítají.
3. Klikněte na **Vypočítat**. Z potvrzených výplatních pásek roku se převezme
   hrubý základ daně, sražené zálohy po měsíčních slevách a již vyplacený
   bonus; záznam spočítá roční daň, slevy, daňové zvýhodnění a bonus,
   **Přeplatek** a **Doplatek na daňovém bonusu**. Nedoplatek se nesráží,
   jak stanoví § 38ch odst. 5.
4. **Celkové vyrovnání** přidejte do výplatní pásky měsíce, ve kterém se
   zúčtování vypořádá, jako vstup *Roční zúčtování daně* (v OCA jako řádek
   vstupu s kódem `ANNUAL_TAX_SETTLEMENT`); zvýší čistou mzdu. Tlačítko pro
   tento krok neexistuje — viz [Omezení](#limitations).

Zaměstnanec musí o roční zúčtování požádat do 15. února a předložit potvrzení
od všech předchozích plátců v roce; zaměstnavatel ho provede do 31. března a
přeplatek nad 50 Kč vrátí nejpozději při zúčtování mzdy za březen
([§ 38ch odst. 1, 3 až 5](law:cz/1992/586)). Modul tyto lhůty nehlídá.
Vyúčtování daně pro finanční úřad je samostatný modul uvedený níže.

## Zaúčtování do hlavní knihy {#accounting}

[module:l10n_cz_hr_payroll_account_oca](module:l10n_cz_hr_payroll_account_oca)
(OCA) a
[module:l10n_cz_hr_payroll_account_ee](module:l10n_cz_hr_payroll_account_ee)
(Enterprise) přiřadí mzdovým pravidlům účty české účtové osnovy, každému
pravidlu účet na stranu Má dáti i Dal, takže potvrzená výplatní páska
zaúčtuje vyrovnaný doklad:

| Účet | Řádky |
|---|---|
| 521 Mzdové náklady | hrubá mzda a náhrada mzdy při nemoci (MD) |
| 331 Zaměstnanci | čistá mzda (D) a protistrana každé srážky |
| 336 Zúčtování s institucemi sociálního a zdravotního pojištění | pojistné zaměstnance; strana D pojistného zaměstnavatele |
| 524 Zákonné sociální pojištění | pojistné zaměstnavatele (MD) snížené o slevu na pojistném |
| 342 Ostatní přímé daně | záloha na daň a srážková daň po odečtení slev, daňového zvýhodnění, vyplaceného daňového bonusu a přeplatku z ročního zúčtování |
| 527 Zákonné sociální náklady | stravenkový paušál (MD) |
| 379 Jiné závazky | exekuční srážky, výživné, postoupení mzdy, ostatní srážky |
| 333 Ostatní závazky vůči zaměstnancům | proplacení výdajů (MD) |

Účtem je první účet, jehož číslo začíná uvedeným trojčíslím.

- **OCA.** Instaluje se ručně a vyžaduje modul OCA `payroll_account`.
  Nastaví účty na pravidlech u všech společností s českou účtovou osnovou —
  u těch, které ji mají při instalaci, i u společností, které ji načtou
  později — a založí jim všeobecný deník *Salaries* (kód `SLR`). Tento deník vyberte na smlouvě jako **Deník platů**.
- **Enterprise.** Nainstaluje se sám, jsou-li nainstalovány Enterprise
  *Mzdy s účetnictvím*, česká účtová osnova a česká mzdová agenda. Účty
  společnostem přiřadí a mzdový deník založí Odoo vlastním nastavením
  mzdového účetnictví.

## Srážky ze mzdy {#garnishment}

Je-li nainstalován modul
[module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base)
a má-li zaměstnanec v evidenci rozhodnutí, vezme pravidlo *Exekuční srážky ze
mzdy* částku z evidence srážek, která uplatní zákonné pořadí pohledávek přes
všechna rozhodnutí zaměstnance.

Bez rozhodnutí v evidenci zadejte pohledávku jako vstup výplatní pásky —
*Exekuční srážky ze mzdy - přednostní* (`GARNISHMENT_PREF`) nebo *Exekuční
srážky ze mzdy - nepřednostní* (`GARNISHMENT_NONPREF`), s dlužnou částkou. V
Enterprise je lze zadat i jako úpravu mzdy. Pravidlo pak z čisté mzdy po
odečtení nezabavitelné částky srazí dvě třetiny (přednostní) nebo jednu
třetinu (nepřednostní) zbytku do hranice a vše nad ni; jednu pohledávku na
pásku. Pro tento postup se dodávají jen hodnoty nezabavitelné částky pro rok
2026.

*Srážka ze mzdy (výkon rozhodnutí)*, *Postoupení mzdy* a *Výživné* jsou
prosté srážky zadané částky.

## Hlášení úřadům {#declarations}

Hlášení jsou samostatné moduly postavené na
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
a fungují s oběma jádry:

| Modul | Hlášení | Komu |
|---|---|---|
| [module:l10n_cz_hr_payroll_pvpoj](module:l10n_cz_hr_payroll_pvpoj) | Přehled o výši pojistného (PVPOJ) | ČSSZ |
| [module:l10n_cz_hr_payroll_onz](module:l10n_cz_hr_payroll_onz) | Oznámení o nástupu do zaměstnání / skončení zaměstnání (ONZ) | ČSSZ |
| [module:l10n_cz_hr_payroll_eldp](module:l10n_cz_hr_payroll_eldp) | Evidenční list důchodového pojištění (ELDP) | ČSSZ |
| [module:l10n_cz_hr_payroll_health](module:l10n_cz_hr_payroll_health) | Přehled o platbě pojistného zaměstnavatele a oznámení o zaměstnancích | zdravotní pojišťovny |
| [module:l10n_cz_hr_payroll_annual_tax_settlement](module:l10n_cz_hr_payroll_annual_tax_settlement) | Vyúčtování daně z příjmů ze závislé činnosti | Finanční správa |

Od 1. ledna 2026 se údaje pro sociální zabezpečení podávají v jednotném
měsíčním hlášení zaměstnavatele (JMHZ, zákon č. 323/2025 Sb.), které žádný
modul této skupiny nevytváří. ONZ je od 1. dubna 2026 nahrazeno; PVPOJ a
ELDP se podávají už jen za období, která jim ponechávají přechodná
ustanovení. Stránka každého hlášení uvádí za která.

## Omezení {#limitations}

- **Více DPP nebo DPČ.** Zákon příjmy z více dohod téže osoby u téhož
  zaměstnavatele sčítá (§ 7 odst. 4 a § 7a odst. 3 zákona č. 187/2006 Sb.).
  Modul ne: každá výplatní páska se s hranicí porovnává samostatně.
- **Zaokrouhlení.** Sociální pojistné se u zaměstnance nezaokrouhluje na
  celé koruny nahoru, zdravotní ano. Sleva na pojistném se také
  nezaokrouhluje: zákon zaokrouhluje její úhrn za všechny zaměstnance.
- **Minimální vyměřovací základ ZP** krátí jen celodenní nepřítomnost. Je-li
  na pásce překážka na straně zaměstnavatele, hradí zaměstnavatel celý
  doplatek, i když má část rozdílu jinou příčinu. Držitelé průkazu ZTP (na
  rozdíl od ZTP/P) a další osoby podle § 3 odst. 8 jsou vyjmuti jen při
  zaškrtnuté *Osobě, za kterou platí pojistné stát*.
- **Sleva na pojistném.** Více zaměstnání u téhož zaměstnavatele se
  nesčítá; oznámení ČSSZ (§ 7a odst. 5) a samotný důvod nároku jsou na vás.
- **Náhrada mzdy při nemoci.** 14 dnů se počítá od prvního dne nepřítomnosti;
  neschopnost vzniklá po odpracované směně (kdy lhůta začíná až následujícím
  dnem) a snížená či nepřiznaná náhrada (§ 192 odst. 4 a 5) vyžadují ruční
  opravu. Hodiny zadané vstupem *Hodiny nemoci* se proplatí, jak jsou.
- **Průměrný výdělek** zahrnuje jen základní mzdu předchozího čtvrtletí, ne
  příplatky ani odměny, a místo 21 odpracovaných dnů testuje „alespoň nějaké
  odpracované hodiny“.
- **Daňové zvýhodnění.** Dítě se ZTP/P přidá jednu částku za první dítě
  místo zdvojnásobení částky podle svého pořadí, u druhého a dalšího dítěte
  tedy příliš málo. Minimum měsíčního bonusu 50 Kč a ročního 100 Kč se
  neuplatňuje.
- **Roční zúčtování daně.** Tlačítko pro převod výsledku do výplatní pásky
  neexistuje, záznam se proto nikdy nedostane do stavu *Vyrovnáno*; vstup
  zadejte ručně. Načítají se jen potvrzené pásky tohoto zaměstnavatele —
  údaje z potvrzení předchozího plátce se nepřičítají. Minimum přeplatku
  50 Kč, minimální výše daru a limit 300 000 Kč u starších úvěrů se
  neuplatňují. Pravidlo jednoho záznamu na zaměstnance a rok se v Odoo 19
  nevynucuje.
- **Plány dovolené.** Plány předpokládají 40hodinový týden; při jiné délce
  upravte přírůstek. Minimum 4 odpracovaných týdnů podle § 213 odst. 3 se
  nevynucuje. Na lhůtu § 218 odst. 3 k určení převedené dovolené nic
  neupozorňuje.
- **Částečná nezaměstnanost (§ 209)** se platí sazbou z *Nastavení →
  Zaměstnanci → Short-time work compensation (§ 209)*, ve výchozím stavu
  100 %. Snižte ji jen tehdy, stanoví-li nižší sazbu dohoda s odborovou
  organizací nebo vnitřní předpis; pod zákonných 60 % páska nikdy nejde.
- **Stravenkový paušál** se vyplácí za každý odpracovaný den; modul
  nekontroluje tříhodinovou směnu ani pracovní cestu v týž den a částku nad
  osvobozený limit zkrátí, místo aby ji vyplatil jako zdanitelný příjem.
- **Jádro OCA.** **Český mzdový kód** vlastních typů nepřítomností nastavíte
  na formuláři typu nepřítomnosti vedle pole *Count as*; typ bez kódu se
  bere jako běžná nepřítomnost.
- Hodnoty se dodávají pro roky 2025 a 2026. Před použitím pro pozdější
  období je ověřte podle platných předpisů.
