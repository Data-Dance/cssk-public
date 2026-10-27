---
title: SK časové rozlíšenie (381, 383, 384, 385)
summary: Nasmeruje nástroje Odoo na časové rozlíšenie na slovenské účty 381, 383, 384 a 385 — časové rozlíšenia OCA v edícii Community, vlastné časové rozlíšenie Odoo v edícii Enterprise.
verified: 19.0.1.0.3
---

## Na čo slúži {#purpose}

Časové rozlíšenie presúva náklad alebo výnos do obdobia, do ktorého patrí,
keď faktúra spadá do iného: poistné zaplatené vopred na budúci rok, nájomné
prijaté vopred, decembrová služba fakturovaná v januári. Slovenská účtová
osnova na to má štyri účty:

| Účet | Názov | Typický prípad |
|---|---|---|
| 381 | Náklady budúcich období | poistné alebo nájomné zaplatené vopred |
| 383 | Výdavky budúcich období | nájomné platené pozadu |
| 384 | Výnosy budúcich období | nájomné alebo predplatné prijaté vopred |
| 385 | Príjmy budúcich období | nájomné prijaté pozadu |

Odoo má na časové rozlíšenie podľa edície dva rôzne nástroje. Ani jeden
slovenské účty nepozná. Prepájajú ich dva malé moduly:

- **Tento modul** ([module:l10n_sk_account_cutoff](module:l10n_sk_account_cutoff))
  vyplní predvolené účty **časových rozlíšení OCA**
  (`account_cutoff_start_end_dates`), ktoré bežia v edícii Community aj
  Enterprise — pozri [Časové rozlíšenia OCA](#cutoffs).
- [module:l10n_sk_account_deferred](module:l10n_sk_account_deferred) vyplní
  účty **vlastného časového rozlíšenia Odoo Enterprise** — pozri
  [Časové rozlíšenie v Enterprise](#enterprise).

Oba sa nainštalujú samy, keď je prítomný ich nástroj a slovenská účtová
osnova (`l10n_sk`). Ani jeden sám nič neúčtuje: len zabezpečia, aby nástroj
účtoval na správne účty.

Položky, ktorých výška ku koncu obdobia ešte **nie je známa**, nie sú
časovým rozlíšením; na tie slúži
[module:l10n_cssk_accrual](module:l10n_cssk_accrual).

## Právny rámec {#legal}

- [Zákon o účtovníctve](law:sk/2002/431) vyžaduje účtovať a vykazovať
  účtovné prípady v období, s ktorým časovo a vecne súvisia —
  [§ 3 ods. 1](law:sk/2002/431#paragraf-3.odsek-1).
- [Opatrenie 740/2002 Z. z.](law:sk/2002/740) určuje účty: náklady a
  výdavky, ktoré sa týkajú budúcich účtovných období, sa časovo rozlišujú na
  účtoch 381 a 382, resp. 383 ([§ 5 ods. 3](law:sk/2002/740#paragraf-5.odsek-3));
  výnosy a príjmy na účtoch 384 a 385
  ([§ 5 ods. 4](law:sk/2002/740#paragraf-5.odsek-4)).
  [§ 56](law:sk/2002/740#paragraf-56) opisuje jednotlivé účty — vopred
  platené nájomné a predplatné na 381, nájomné platené pozadu na 383,
  nájomné prijaté vopred na 384, nájomné prijaté pozadu na 385 — a vymenúva
  náklady, ktoré sa časovo **nerozlišujú**, napríklad reklama, školenia či
  prieskum trhu, pokiaľ samotná služba nie je platená vopred (§ 56 ods. 6).

Účet 382 *Komplexné náklady budúcich období* nemapuje ani jeden z modulov.

## Časové rozlíšenia OCA {#cutoffs}

### Čo modul nastaví {#cutoffs-setup}

Pri spoločnosti so slovenskou osnovou — pri načítaní osnovy alebo pri
inštalácii, ak ju spoločnosť už má — modul vyplní, len ak sú prázdne:

| Nastavenie (*Účtovníctvo → Konfigurácia → Nastavenia*, blok *Časové rozlíšenia*) | Účet |
|---|---|
| Predvolený účet pre náklady budúcich období | 381000 |
| Predvolený účet pre výdavky budúcich období | 383000 |
| Predvolený účet pre výnosy budúcich období | 384000 |
| Predvolený účet pre príjmy budúcich období | 385000 |
| Predvolený denník časového rozlíšenia | prvý denník spoločnosti typu *Rôzne* |

Modul tiež vypne **Časové rozlíšenie daní**. Nástroj OCA ho má predvolene
zapnuté a potom časovo rozlišuje aj DPH zdrojových riadkov, na *Daňový účet
výdavkov / príjmov budúcich období*, ktorý slovenská osnova nemá — časové
rozlíšenie riadkov s daňou preto skončilo chybou *Missing 'Accrued Expense
Tax Account'*. Správne by to ani nebolo: daň na vstupe nemožno odpočítať,
kým platiteľ nemá faktúru ([§ 51 ods. 1 písm. a) zákona o DPH](law:sk/2004/222#paragraf-51.odsek-1.pismeno-a)),
takže výdavky a príjmy budúcich období na 383 / 385 sú sumy bez DPH. Pri
inštalácii a aktualizácii sa voľba vypne len tam, kde nie je nastavený žiadny daňový účet
pre časové rozlíšenie (v spoločnosti ani na dani); ak ho váš účtovník
nastavil, zostane zapnutá.

Každé z nich tam môžete zmeniť. Prejdite si aj ďalšie dve nastavenia toho
istého bloku, ktoré modul nemení:

- **Zaúčtovať účtovný zápis časového rozlíšenia** je vypnuté: zápis vznikne
  ako návrh, ktorý skontrolujete a zaúčtujete.
- **Partner na účtovných položkách v predvolenom nastavení** určuje, či
  riadky zápisu nesú partnera.

### Zadanie dátumov {#cutoffs-dates}

Časové rozlíšenie OCA vychádza z **počiatočného a koncového dátumu na
riadkoch faktúr** (*Počiatočný dátum*, *Koncový dátum*). Zadajte ich na každom
riadku, ktorého náklad alebo výnos sa týka obdobia — napríklad 1. 7. 2026 –
30. 6. 2027 na faktúre za ročné poistenie. Ak majú byť dátumy pri produkte
povinné, zaškrtnite na ňom *Musí mať počiatočný/koncový dátum*.

### Spustenie časového rozlíšenia {#cutoffs-usage}

Ku koncu obdobia: *Účtovníctvo → Účtovníctvo → Časové rozlíšenia*, vyberte
druh a kliknite na *Nový*:

| Ponuka | Účet | Ktoré riadky zahrnie |
|---|---|---|
| Náklady budúcich období | 381 | riadky prijatých faktúr s dátumom najneskôr k dátumu časového rozlíšenia, ktorých koncový dátum je neskorší; časovo sa rozlíši časť po tomto dátume |
| Výnosy budúcich období | 384 | to isté pri vydaných faktúrach |
| Výdavky budúcich období | 383 | riadky prijatých faktúr s dátumom **po** dátume časového rozlíšenia, ktorých počiatočný dátum je najneskôr k nemu; späť sa presunie časť do tohto dátumu |
| Príjmy budúcich období | 385 | to isté pri vydaných faktúrach |

Suma sa delí podľa dní. Zadajte *Dátum časového rozlíšenia*, skontrolujte
*Zdrojové denníky*, kliknite na **Znovu vygenerovať riadky**, skontrolujte
riadky a kliknite na **Vytvoriť účtovný zápis**. Zápis má dátum časového
rozlíšenia.

Z toho vyplývajú dve praktické veci:

- 383 a 385 fungujú len s faktúrami, ktoré sú **už zaúčtované** s neskorším
  dátumom — spúšťajte ich, keď sú januárové faktúry za decembrové služby
  zaúčtované a knihy ešte nie sú uzavreté.
- Zápis časového rozlíšenia sa **automaticky nestornuje**. Stornujte ho sami
  k prvému dňu nasledujúceho obdobia (tlačidlo *Záznam storna* na zápise —
  tak Odoo v slovenčine označuje *Reverse Entry*), aby pôvodné riadky faktúr
  zaťažili obdobie, do ktorého patria.

V spoločnosti môže existovať len jedno časové rozlíšenie daného druhu k
danému dátumu.

## Časové rozlíšenie v Enterprise {#enterprise}

Odoo Enterprise (`account_accountant`) má vlastné časové rozlíšenie: na
riadku faktúry zadáte obdobie v stĺpci **Dátum časového rozlíšenia** a Odoo
sumu rozloží cez účet časového rozlíšenia po mesiacoch alebo po dňoch.

[module:l10n_sk_account_deferred](module:l10n_sk_account_deferred) sa
nainštaluje sám spolu s `account_accountant` v databáze so slovenskou osnovou
a v *Účtovníctvo → Konfigurácia → Nastavenia* nastaví:

| Nastavenie | Hodnota |
|---|---|
| Záznamy časovo rozlíšených nákladov → Časovo rozlíšený náklad | 381000 |
| Záznamy časovo rozlíšených výnosov → Časovo rozlíšený výnos | 384000 |
| *Denník* oboch blokov | prvý denník spoločnosti typu *Rôzne*, ak je prázdny |

Bez neho Enterprise vyplní oba účty prvým účtom obežných aktív a prvým účtom
krátkodobých záväzkov v osnove, nech sú to akékoľvek. Pri inštalácii modul
oba účty v každej slovenskej spoločnosti nastaví, ak sú prázdne alebo ešte
na tejto všeobecnej voľbe; účet, ktorý ste nastavili ručne, ponechá. Neskôr
sa týka už len nových spoločností.

Či sa zápisy vytvárajú pri zaúčtovaní faktúry (*Pri potvrdení dodávateľskej
faktúry*) alebo naraz (*Ručne a zoskupené*) a či sa suma delí po mesiacoch
alebo dňoch, sú vlastné nastavenia Enterprise v tých istých blokoch.
Prehľady sú v *Účtovníctvo → Kontrola → Regulatívne požiadavky* (takto Odoo
nesprávne prekladá *Regularization Entries*) → *Časové rozlíšenie nákladov* /
*Časové rozlíšenie výnosov*.

Časové rozlíšenie Enterprise pokrýva len prípady platené vopred, teda 381 a
384. Výdavky a príjmy budúcich období (383, 385) treba riešiť časovými
rozlíšeniami OCA uvedenými vyššie alebo ručným zápisom.

## Obmedzenia {#limitations}

- Oba moduly len nastavujú predvolené účty a denníky. Samy nič nepočítajú
  ani neúčtujú.
- Výdavky a príjmy budúcich období sa účtujú bez DPH. Spoločnosť, ktorá nie
  je platiteľom DPH a pre ktorú je DPH nákladom, musí DPH doplniť ručne.
- Zápisy časového rozlíšenia sa nestornujú automaticky.
- Slovenská osnova Odoo nazýva účet 385000 *Náklady budúcich období
  (krátkodobé)* a 383000 *Výdaje budúcich období*; opatrenie ich nazýva
  *Príjmy budúcich období* a *Výdavky budúcich období*. Účty sú správne,
  nesprávne sú len názvy, ktoré dodáva Odoo. Ak používateľov mätú, premenujte
  ich v účtovom rozvrhu.
- V edícii Enterprise môžu byť nainštalované oba nástroje naraz a riadok
  faktúry potom ukazuje obe sady dátumov. Na jeden riadok používajte len
  jeden nástroj: dátumy zadané v oboch by sumu časovo rozlíšili dvakrát.
- Ani jeden modul nekontroluje, či sa náklad smie časovo rozlišovať (§ 56
  ods. 6 opatrenia).
