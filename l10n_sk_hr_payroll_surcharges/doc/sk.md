---
title: SK mzdové zvýhodnenia a minimálne mzdové nároky
summary: Zákonné mzdové zvýhodnenia za nočnú prácu, prácu v sobotu, v nedeľu a vo sviatok, za prácu nadčas, mzdová kompenzácia za sťažený výkon práce a náhrada za pracovnú pohotovosť, ako aj doplatok do minimálneho mzdového nároku podľa stupňa náročnosti, v oboch mzdových enginoch.
verified: 19.0.1.2.5
---

## Na čo slúži {#purpose}

Zákonník práce priznáva zamestnancovi mzdové zvýhodnenie za prácu v určitom
čase alebo za určitých podmienok a zaručuje minimálny mzdový nárok podľa
náročnosti pracovného miesta. Modul počíta oboje:

- mzdové zvýhodnenia za **nočnú prácu**, prácu **v sobotu**, **v nedeľu** a
  **vo sviatok**, za **prácu nadčas**, mzdovú kompenzáciu za **sťažený výkon
  práce** a náhradu za **neaktívnu časť pracovnej pohotovosti mimo
  pracoviska**;
- šesť **stupňov náročnosti** a **doplatok** mzdy, ktorá nedosiahne minimálny
  mzdový nárok pre stupeň pracovného miesta.

Každé percento a každá suma je datovaný záznam, zmena zákona je teda zmenou
údajov. Samotný modul obsahuje sadzby, polia a výpočet a funguje aj bez
mzdového enginu; mzdové pravidlá pridáva jeho mostík k enginu (pozri
[Mzdové enginy](#engines)). Patrí do
[skupiny slovenských miezd](module:l10n_sk_hr_payroll_base#purpose).

## Právny rámec {#legal}

Ak nie je uvedené inak, odkazy sú na [Zákonník práce](law:sk/2001/311).

| Zvýhodnenie | Paragraf | Najmenej | Z |
|---|---|---|---|
| Práca nadčas | [§ 121 ods. 1](law:sk/2001/311#paragraf-121.odsek-1) | dosiahnutá mzda + 25 % (pri rizikových prácach 35 %) | priemerného zárobku |
| Práca vo sviatok | [§ 122 ods. 1](law:sk/2001/311#paragraf-122.odsek-1) | 100 % | priemerného zárobku |
| Práca v sobotu | [§ 122a](law:sk/2001/311#paragraf-122a) | 50 % (45 % dohodou, ak sa v sobotu pracuje pravidelne) | minimálnej mzdy v eurách za hodinu |
| Práca v nedeľu | [§ 122b](law:sk/2001/311#paragraf-122b) | 100 % (90 % dohodou, ak sa v nedeľu pracuje pravidelne) | minimálnej mzdy v eurách za hodinu |
| Nočná práca | [§ 123](law:sk/2001/311#paragraf-123) | 40 % (pri rizikovej práci 50 %; 35 % dohodou, ak sa prevažná časť práce vykonáva v noci, nie pri rizikovej práci) | minimálnej mzdy v eurách za hodinu |
| Sťažený výkon práce | [§ 124 ods. 3](law:sk/2001/311#paragraf-124.odsek-3) | 20 % | minimálnej mzdy v eurách za hodinu |
| Neaktívna pohotovosť mimo pracoviska | [§ 96 ods. 5](law:sk/2001/311#paragraf-96.odsek-5) | 20 % | minimálnej mzdy v eurách za hodinu |

Nižšie zvýhodnenie za sobotu, nedeľu a nočnú prácu možno dohodnúť v
kolektívnej zmluve, alebo v pracovnej zmluve u zamestnávateľa, u ktorého
nepôsobí odborová organizácia a ktorý k 31. decembru predchádzajúceho roka
zamestnával menej ako 20 zamestnancov.

**Minimálne mzdové nároky.** Zamestnávateľ, u ktorého nie je odmeňovanie
dohodnuté v kolektívnej zmluve, musí poskytnúť mzdu najmenej v sume
minimálneho mzdového nároku pre stupeň náročnosti pracovného miesta a rozdiel
za kalendárny mesiac doplatí
([§ 120 ods. 1](law:sk/2001/311#paragraf-120.odsek-1)). Do porovnávanej mzdy
sa nezahŕňa mzda za prácu nadčas, mzdové zvýhodnenia ani mzdová kompenzácia
za sťažený výkon práce
([§ 120 ods. 2](law:sk/2001/311#paragraf-120.odsek-2)). Stupeň sa pracovnému
miestu priraďuje podľa najnáročnejšej pracovnej činnosti
([§ 120 ods. 3](law:sk/2001/311#paragraf-120.odsek-3)). Mesačný nárok je
mesačná minimálna mzda na príslušný rok zvýšená o (koeficient − 1) ×
minimálna mzda na rok 2020 vo výške 580 €, s koeficientmi 1,0 až 2,0; hodinový
nárok je jeho 1/174 ([§ 120 ods. 4](law:sk/2001/311#paragraf-120.odsek-4)).
Pri ustanovenom týždennom pracovnom čase kratšom ako 40 hodín sa hodinové
nároky úmerne zvýšia
([§ 120 ods. 5](law:sk/2001/311#paragraf-120.odsek-5)); mesačný nárok sa
znižuje v pomere k odpracovanému času
([§ 120 ods. 6](law:sk/2001/311#paragraf-120.odsek-6)). Samotná minimálna
mzda za hodinu je 1/174 mesačnej minimálnej mzdy
([§ 2 ods. 2 zákona o minimálnej mzde](law:sk/2007/663#paragraf-2.odsek-2)).

## Nastavenie {#setup}

1. Nainštalujte mostík pre svoj engine — nainštaluje sa sám spolu so
   slovenskými mzdami daného enginu.
2. **Zaraďte pracovné pozície.** Na každej pracovnej pozícii nastavte
   **Stupeň náročnosti**. Zmluva vytvorená na pozíciu ho po výbere pozície
   prevezme; stupeň, ktorý už na zmluve je, nikdy neprepíše.
3. **Na zmluve**, skupina **Slovenské mzdové príplatky**:

   | Pole | Čo robí |
   |---|---|
   | Stupeň náročnosti | Stupeň tejto zmluvy (§ 120). Ak je prázdny, použije sa 1. stupeň — samotná minimálna mzda. |
   | Riziková práca | Zvýši zvýhodnenie za nočnú prácu na 50 % a za prácu nadčas na 35 % a vylúči zníženú sadzbu za nočnú prácu. |
   | Dohodnutá znížená nočná sadzba, Dohodnutá znížená sobotňajšia sadzba, Dohodnutá znížená nedeľná sadzba | Zaškrtnite, ak bola nižšia sadzba dohodnutá, ako je opísané vyššie. Pri rizikovej práci je nočná voľba skrytá. |

   Ak je dohodnutá mzda nižšia ako nárok pre stupeň zmluvy (pri kratšom
   týždni pomerne znížený), nad skupinou sa zobrazí **Upozornenie na
   minimálnu mzdu**. Dohody a zmluvy s hodinovou mzdou sa nekontrolujú.
4. **Sadzby.** *Zamestnanci → Konfigurácia → Slovenské mzdové príplatky*
   (personálni manažéri):
   - **Minimálne mzdové nároky** — jeden záznam na stupeň a dátum účinnosti,
     s mesačným a hodinovým nárokom;
   - **Sadzby príplatkov** — jeden záznam na dátum účinnosti so všetkými
     percentami a **Ustanoveným týždenným pracovným časom**.

   Ak chcete platiť viac ako zákonné minimum alebo posunúť údaje do nového
   roka, pridajte nový datovaný záznam namiesto úpravy starého.

## Zadanie hodín {#usage}

Modul nočné ani víkendové hodiny z dochádzky nezisťuje. Každé zvýhodnenie
dostáva počet hodín pod svojím kódom:

| Kód | Hodiny | Riadok výplatnej pásky |
|---|---|---|
| NOC | nočnej práce | *Night Work Surcharge* |
| SOBOTA | práce v sobotu | *Saturday Work Surcharge* |
| NEDELA | práce v nedeľu | *Sunday Work Surcharge* |
| SVIATOK | práce vo sviatok | *Public Holiday Work Surcharge* |
| NADCAS | práce nadčas | *Overtime Pay* a *Overtime Surcharge* |
| STAZENY | sťaženého výkonu práce | *Difficult Conditions Compensation* |
| POHOTOVOST | neaktívnej pohotovosti mimo pracoviska | *Standby Compensation* |

Názvy riadkov a vstupov sa zobrazujú po anglicky. Hodiny zadajte ako vstup
výplatnej pásky s týmto kódom (ostatné vstupy na výplatnej páske; typy
vstupov sa volajú *Night hours*, *Saturday hours* atď.). Ak má výplatná páska
riadok odpracovaných dní s rovnakým kódom, má prednosť pred vstupom.

Nočné, sobotné, nedeľné hodiny a hodiny sťaženého výkonu práce zamestnanec
zároveň odpracoval bežne. Typ pracovného záznamu s takým kódom, ktorý by
hodiny presunul mimo bežnej práce, by znížil základnú mzdu; takéto hodiny
evidujte popri bežnej práci alebo použite vstupy.

## Čo ukáže výplatná páska {#payslip}

- **Zvýhodnenia.** Hodiny × hodinový základ × percento, zaokrúhlené na
  eurocent **nahor**, pretože každý údaj je zákonné minimum. Hodinovým
  základom je pri nočnej práci, sobote, nedeli, sťaženom výkone a pohotovosti
  **minimálna mzda v eurách za hodinu** 1. stupňa — bez ohľadu na stupeň
  zamestnanca — a pri sviatku a práci nadčas **priemerný hodinový zárobok**
  zamestnanca.
- **Mzda za prácu nadčas.** Hodiny nadčas sú mimo času, ktorý pokrýva mesačná
  mzda, preto *Overtime Pay* pridá popri zvýhodnení aj mzdu za tieto hodiny v
  sume priemerného zárobku. Za hodiny vo sviatok sa pridá len zvýhodnenie;
  mzda za ne sa predpokladá v základnej mzde.
- **Minimum Wage Top-up** (doplatok). Porovnáva **základnú mzdu** — bez
  zvýhodnení, práce nadčas a náhrad mzdy — s nárokom pre stupeň zmluvy:
  - pri mesačnej mzde s mesačným nárokom zníženým v pomere bežne
    odpracovaných hodín (bez neprítomnosti) k hodinám, ktoré by v období
    odpracovala zmluva na plný úväzok podľa pracovného kalendára spoločnosti;
  - pri hodinovej mzde (len v engine OCA) s hodinovým nárokom zvýšeným pri
    pracovnom kalendári kratšom ako ustanovený týždeň.

  Platí len pre pracovný pomer. Všetky riadky zvýhodnení vstupujú do hrubej
  mzdy, podliehajú teda poistnému aj dani.

## Zákonné údaje {#rates}

Percentá účinné od 1. júna 2023 (jediný dodávaný záznam):

| Noc | Noc, riziková | Noc, znížená | Sobota | Sobota, znížená | Nedeľa | Nedeľa, znížená | Sťažený výkon | Pohotovosť | Sviatok | Nadčas | Nadčas, riziková |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 40 % | 50 % | 35 % | 50 % | 45 % | 100 % | 90 % | 20 % | 20 % | 100 % | 25 % | 35 % |

Minimálne mzdové nároky (mesačne / za hodinu):

| Stupeň | 2024 | 2025 | 2026 |
|---|---|---|---|
| 1 — pomocné práce | 750 € / 4,310 € | 816 € / 4,690 € | 915 € / 5,259 € |
| 2 — jednoduché odborné práce | 866 € / 4,977 € | 932 € / 5,356 € | 1 031 € / 5,925 € |
| 3 — odborné práce | 982 € / 5,644 € | 1 048 € / 6,023 € | 1 147 € / 6,592 € |
| 4 — zložité odborné práce | 1 098 € / 6,310 € | 1 164 € / 6,690 € | 1 263 € / 7,259 € |
| 5 — veľmi zložité odborné práce | 1 214 € / 6,977 € | 1 280 € / 7,356 € | 1 379 € / 7,925 € |
| 6 — vysoko špecializované práce | 1 330 € / 7,644 € | 1 396 € / 8,023 € | 1 495 € / 8,592 € |

Hodina nočnej práce v roku 2026 teda prinesie popri mzde najmenej
40 % × 5,259 € = 2,11 €.

## Mzdové enginy {#engines}

Mzdové pravidlá pridáva mostík pre každý engine; oba používajú ten istý
výpočet a tie isté údaje z tohto modulu.

- [module:l10n_sk_hr_payroll_surcharges_ee](module:l10n_sk_hr_payroll_surcharges_ee)
  pridá pravidlá do slovenskej štruktúry Odoo Enterprise Payroll spolu so
  siedmimi typmi vstupov výplatnej pásky. Šablóny zmlúv prenášajú polia
  zvýhodnení na nové zmluvy. Nainštaluje sa sám, keď je nainštalovaný
  [module:l10n_sk_hr_payroll_ee](module:l10n_sk_hr_payroll_ee) aj tento modul.
- [module:l10n_sk_hr_payroll_surcharges_oca](module:l10n_sk_hr_payroll_surcharges_oca)
  pridá pravidlá do slovenských štruktúr aplikácie OCA payroll, každé pravidlo
  s vlastným vstupom. Nainštaluje sa sám, keď je nainštalovaný
  [module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca) aj tento
  modul.

## Obmedzenia {#limitations}

- **Podmienky znížených sadzieb sa nekontrolujú.** Modul neoveruje, či
  existuje kolektívna zmluva (alebo pracovná zmluva u oprávneného
  zamestnávateľa).
- **Odmeňovanie v kolektívnej zmluve.** § 120 ods. 1 sa uplatní, len ak
  odmeňovanie nie je dohodnuté v kolektívnej zmluve; modul doplatok počíta
  vždy.
- **Dohody** nekontroluje vôbec — ani nárok podľa § 120 (na ne sa
  nevzťahuje), ani minimálnu mzdu za hodinu.
- **Hodiny sa zadávajú, neodvodzujú.** Modul nedodáva typy pracovných
  záznamov a hodiny neberie z dochádzky ani z kalendára.
- **Práca nadčas** sa oceňuje priemerným zárobkom; zamestnávateľ, ktorého
  zmluvy uvádzajú hodinovú mzdu, musí upraviť pravidlo *Overtime Pay*.
- **Pohotovosť** pokrýva len neaktívnu časť mimo pracoviska; neaktívna
  pohotovosť na pracovisku je pracovný čas a modul ju nerozpozná.
- **Sťažený výkon práce** má jednu sadzbu; sadzby podľa druhu rizika, ktoré
  zavádzajú niektoré kolektívne zmluvy, sa nemodelujú.
- **Obdobia pred 1. júnom 2023** dodávaný záznam sadzieb nepokrýva a jeho
  percentuálne polia nevedia vyjadriť zvýhodnenie určené pevnou sumou.
