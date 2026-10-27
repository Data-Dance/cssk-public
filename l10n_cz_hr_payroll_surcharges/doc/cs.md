---
title: Příplatky ke mzdě (CZ)
summary: Zákonné příplatky ke mzdě za práci přesčas, ve svátek, v noci, v sobotu a v neděli a ve ztíženém pracovním prostředí, mzda za práci přesčas a doplatek do minimální mzdy, z datovaných sazeb, pro obě mzdová jádra.
verified: 19.0.1.1.0
---

## Na co slouží {#purpose}

Zákoník práce přiznává zaměstnanci za práci v určitou dobu nebo za určitých
podmínek příplatek ke mzdě. Modul počítá pět z nich:

- za **práci přesčas**,
- za **práci ve svátek**,
- za **noční práci**,
- za **práci v sobotu a v neděli**,
- za **práci ve ztíženém pracovním prostředí**.

Vedle příplatku za práci přesčas vyplácí i **mzdu za hodiny práce přesčas**
(dosaženou mzdu) a **doplatek do minimální mzdy**, je-li mzda nižší než
minimální mzda.

Modul obsahuje datované procentní sazby, datovanou minimální mzdu, dvě pole
smlouvy a výpočet a lze ho nainstalovat bez mzdového jádra. Mzdová pravidla
dodává modul pro příslušné jádro (viz [Mzdová jádra](#engines)). Je součástí
[české mzdové agendy](module:l10n_cz_hr_payroll_base#purpose).

Obdoba slovenských stupňů náročnosti v Česku není: od 1. ledna 2025 platí v
podnikatelské sféře jedna minimální mzda pro všechny práce.

Modul nemá český překlad, jeho obrazovky jsou proto anglicky; anglické
popisky uvádíme v závorce.

## Právní rámec {#legal}

Všechny odkazy jsou na [zákoník práce](law:cz/2006/262), mzdová sféra.
Všechny hodnoty jsou minimální („nejméně“).

| Příplatek | Ustanovení | Nejméně | Z čeho |
|---|---|---|---|
| Práce přesčas | § 114 odst. 1 | 25 %, nedohodne-li se místo příplatku náhradní volno | průměrný výdělek |
| Práce ve svátek | § 115 odst. 2 | 100 %, je-li dohodnut místo náhradního volna | průměrný výdělek |
| Noční práce | § 116 | 10 %; lze sjednat jinou minimální výši | průměrný výdělek |
| Ztížené pracovní prostředí | § 117 | 10 % za každý ztěžující vliv | minimální mzda |
| Práce v sobotu a v neděli | § 118 odst. 1 | 10 %; lze sjednat jinou minimální výši | průměrný výdělek |

Za hodinu práce přesčas přísluší dosažená mzda *a* příplatek
([§ 114 odst. 1](law:cz/2006/262)); nepřísluší ani jedno, byla-li mzda
sjednána již s přihlédnutím k práci přesčas, nejvýše pro 150 hodin ročně
([§ 114 odst. 3](law:cz/2006/262)). Mzdu nižší než minimální mzda
zaměstnavatel doplácí; mzda za práci přesčas a příplatky se do ní pro tento
účel nezahrnují ([§ 111 odst. 1](law:cz/2006/262)). Doplatek je rozdíl na
odpracovanou hodinu proti hodinové minimální mzdě, nebo proti měsíční
minimální mzdě, byla-li její použití předem sjednáno, stanoveno nebo určeno;
u dohod se porovnává vždy za hodinu ([§ 111 odst. 2](law:cz/2006/262)).
Měsíční minimální mzda se poměrně snižuje při kratší pracovní době nebo
neodpracovaném celém měsíci ([§ 111 odst. 6](law:cz/2006/262)).

Ztěžující vlivy (prach, chemické látky, hluk, vibrace, rozdělená směna aj.)
vymezuje [nařízení vlády č. 443/2024 Sb.](law:cz/2024/443), účinné od
1. ledna 2025. Příplatky se sčítají: hodina práce přesčas v sobotu v noci
nese příplatek podle § 114, § 116 i § 118.

## Nastavení {#setup}

1. Nainstalujte modul pro své mzdové jádro (viz [Mzdová jádra](#engines)).
2. Zkontrolujte sazby v *Zaměstnanci → Konfigurace → Czech Wage Surcharges*:
   - **Minimální mzda** (*Czech Minimum Wage*) — jeden záznam na datum
     účinnosti s měsíční a hodinovou částkou. Dodávají se roky 2025
     (20 800 Kč / 124,40 Kč) a 2026 (22 400 Kč / 134,40 Kč); záznam na další
     rok přidejte, jakmile ho MPSV vyhlásí.
   - **Sazby příplatků** (*Czech Wage Surcharges*) — jeden záznam na datum
     účinnosti s procenty: přesčas (*Overtime %*) 25, svátek (*Public
     holiday %*) 100, noční práce (*Night work %*) 10, sobota a neděle
     (*Saturday/Sunday %*) 10, ztížené prostředí (*Difficult environment %*)
     10 a stanovená týdenní pracovní doba (*Standard weekly hours*) 40.
     Dodává se jeden záznam od 1. 1. 2024. Platíte-li víc než minimum,
     zvyšte hodnotu nebo přidejte záznam s datem účinnosti dohody. Sjednané
     sazby pro noční a víkendovou práci (*Night work % (agreed)*,
     *Saturday/Sunday % (agreed)*) jsou prázdné; vyplňte je, jen pokud
     kolektivní nebo individuální smlouva sjednává jinou minimální výši.
   Záznamy smí měnit jen manažer personalistiky a žádné z pěti procent nesmí
   být nulové.
3. Na vzoru smlouvy (*Zaměstnanci → Konfigurace → Vzory smluv*), skupina
   **Czech Wage Surcharges**:

   | Pole | Co dělá |
   |---|---|
   | Ztížené prostředí — počet vlivů | Počet ztěžujících vlivů. Každý přidá dalších 10 %. Nula znamená, že se příplatek za ztížené prostředí neplatí bez ohledu na zadané hodiny. |
   | Sjednaná jiná výše příplatků | Dohoda sjednává jinou minimální výši příplatku za noční a víkendovou práci: použijí se sjednané sazby. |
   | Minimum wage top-up compared with | Hodinová (*Hourly minimum wage*, výchozí, jako v zákoně) nebo měsíční minimální mzda (*Monthly minimum wage*). Měsíční zvolte jen tehdy, byla-li předem sjednána, stanovena nebo určena. Dohody a zaměstnanci s hodinovou mzdou se porovnávají vždy za hodinu. |

## Zadání hodin {#usage}

Hodiny jednotlivých druhů se zadávají ve výplatní pásce — v jádru OCA jako
vstup, v Enterprise jako *Jiný vstup*:

| Vstup | Kód | Řádek příplatku ve výplatní pásce |
|---|---|---|
| Overtime hours | `PRESCAS` | Overtime Wage (§ 114) a Overtime Surcharge (§ 114) |
| Public holiday hours | `SVATEK` | Public Holiday Surcharge (§ 115) |
| Night hours | `NOCNI` | Night Work Surcharge (§ 116) |
| Weekend hours | `VIKEND` | Saturday/Sunday Surcharge (§ 118) |
| Difficult-environment hours | `ZTIZENE` | Difficult Environment Surcharge (§ 117) |

Částka vstupu je počet hodin. Noční, víkendové hodiny a hodiny ve ztíženém
prostředí jsou tytéž hodiny jako běžná práce, jen viděné podruhé — zadávejte
je navíc k pracovní době, ne místo ní. Má-li stejný kód řádek odpracovaných
dnů (například z vlastního typu pracovního záznamu s kódem `NOCNI`), má
přednost před vstupem.

## Jak se částka počítá {#computation}

Za každý kód: hodiny × hodinový základ × procento, zaokrouhleno na haléře
**nahoru**, aby zaokrouhlení nikdy nesnížilo platbu pod zákonné minimum.

- **Hodinovým základem pro přesčas, svátek, noc a víkend** je průměrný
  hodinový výdělek zaměstnance, jak ho spočítá česká mzdová agenda
  (předchozí čtvrtletí nebo hodnota zadaná na smlouvě).
- **Hodinovým základem pro ztížené prostředí** je hodinová minimální mzda
  ([§ 117 odst. 2](law:cz/2006/262); § 3 nařízení vlády č. 443/2024 Sb., do
  roku 2024 č. 567/2006 Sb.), poměrně zvýšená, má-li pracovní kalendář
  **společnosti** méně týdenních hodin než *Standard weekly hours*
  ([§ 111 odst. 5](law:cz/2006/262)). Kratší pracovní doba samotného
  zaměstnance (§ 80) ji nezvyšuje. Příplatek se pak násobí počtem
  ztěžujících vlivů.
- Příplatky vstupují do hrubé mzdy, a tedy do pojistného i daně.
- **Mzda za práci přesčas** (*Overtime Wage*) jsou hodiny přesčas × vlastní
  hodinová mzda zaměstnance: hodinová mzda u hodinově placeného, jinak
  měsíční mzda dělená hodinami, které smlouva v měsíci rozvrhuje. Zaměstnanci
  se mzdou sjednanou včetně práce přesčas (§ 114 odst. 3) hodiny přesčas
  nezadávejte.
- **Doplatek do minimální mzdy** (*Minimum Wage Top-up*) se počítá po
  náhradách mzdy a před hrubou mzdou, takže se z něj platí pojistné i daň.
  Porovnává se základní mzda a složky mzdy spočtené před ním, bez mzdy za
  práci přesčas, příplatků a náhrad mzdy (dovolená, překážky); hodinami jsou
  odpracované hodiny běžné pracovní doby bez nepřítomností a přesčasů. Při
  hodinovém porovnání činí doplatek (hodinová minimální mzda − mzda na
  hodinu) × hodiny; při měsíčním měsíční minimální mzdu, poměrně sníženou
  podle odpracovaných hodin proti plnému měsíci podle kalendáře společnosti,
  minus mzdu.

## Mzdová jádra {#engines}

Nainstalujte modul, který odpovídá vašemu českému mzdovému jádru. Ani jeden
se nenainstaluje sám.

- [module:l10n_cz_hr_payroll_surcharges_ee](module:l10n_cz_hr_payroll_surcharges_ee)
  — Odoo Enterprise Payroll: pět pravidel v české struktuře a pět typů
  vstupů výplatní pásky.
- [module:l10n_cz_hr_payroll_surcharges_oca](module:l10n_cz_hr_payroll_surcharges_oca)
  — OCA payroll: pět pravidel v české struktuře, každé s deklarovaným
  vstupem.

## Omezení {#limitations}

- **Doplatek do minimální mzdy.** Odměny a další složky mzdy se započtou,
  jen pokud jejich mzdové pravidlo běží před doplatkem (pořadí pod 95);
  pozdější se nezapočtou a doplatek pak může vyjít vyšší. Česká mzdová
  agenda má vlastní kopii minimální mzdy jako parametr pravidla; udržujte
  obě hodnoty shodné. Volbou měsíčního porovnání potvrzujete, že bylo předem
  sjednáno.
- **Náhradní volno za práci přesčas** (§ 114 odst. 1 a 2) se nesleduje:
  hodiny přesčas zadávejte do pásky, jen když se proplácejí.
- **Svátek** se platí 100 % vždy, když hodiny zadáte. Zadávejte je jen
  tehdy, byl-li příplatek dohodnut místo náhradního volna.
- **Stanovenou týdenní pracovní dobu zastupuje pracovní kalendář
  společnosti.** Hodinová minimální mzda se zvýší jen tehdy, má-li kalendář
  společnosti méně týdenních hodin než *Standard weekly hours*. Udržujte
  kalendář společnosti na stanovené týdenní pracovní době zaměstnavatele.
- **Průměrný výdělek** přebírá modul z české mzdové agendy, která počítá jen
  základní mzdu předchozího čtvrtletí.
- Pole smlouvy jsou jen na formuláři vzoru smlouvy; k zaměstnanci se
  hodnota dostane použitím vzoru na smlouvu.
