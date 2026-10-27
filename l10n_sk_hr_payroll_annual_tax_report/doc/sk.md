---
title: SK Hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti
summary: Ročné hlásenie zamestnávateľa o príjmoch zo závislej činnosti, zrazených preddavkoch na daň a daňovom bonuse, s údajmi o každom zamestnancovi, zostavené z výplatných pások roka ako XML pre finančnú správu.
verified: 19.0.2.0.2
---

## Na čo slúži {#purpose}

Po skončení roka podáva zamestnávateľ, ktorý zráža preddavky na daň, správcovi
dane **Hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti**.
Zhŕňa mzdy, zrazené preddavky na daň a daňové bonusy za rok a uvádza každého
zamestnanca s jeho údajmi.

Modul hlásenie zostaví z výplatných pások kalendárneho roka a vyexportuje ho
ako XML vo formáte finančnej správy. Podobne ako mesačný
[module:l10n_sk_hr_payroll_monthly_tax_overview](module:l10n_sk_hr_payroll_monthly_tax_overview)
funguje s oboma mzdovými jadrami (pozri
[skupinu modulov slovenských miezd](module:l10n_sk_hr_payroll_base#declarations))
a obrazovky, stavy a kontrolu XML zdieľa s ostatnými mzdovými hláseniami
prostredníctvom
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base).

## Právny rámec {#legal}

Odkazy sú na [zákon o dani z príjmov](law:sk/2003/595).

- **Povinnosť.** Zamestnávateľ, ktorý je platiteľom dane, predkladá správcovi
  dane hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti
  poskytnutých jednotlivým zamestnancom za uplynulé zdaňovacie obdobie, o
  zrazených preddavkoch na daň, o zamestnaneckej prémii, o daňovom bonuse a o
  daňovom bonuse na zaplatené úroky —
  [§ 39 ods. 9 písm. b)](law:sk/2003/595#paragraf-39.odsek-9.pismeno-b).
  Hlásenie podľa toho istého ustanovenia obsahuje aj meno, priezvisko a
  **rodné číslo** zamestnanca — preto ho modul bez rodného čísla nevygeneruje.
- **Lehota.** Hlásenie sa podáva **do konca apríla** po uplynutí zdaňovacieho
  obdobia — [§ 49 ods. 2](law:sk/2003/595#paragraf-49.odsek-2). Hlásenie za
  rok 2026 treba podať do 30. 4. 2027.

## Nastavenie {#setup}

- **DIČ spoločnosti.** Na spoločnosti vyplňte *DIČ* (10-miestne daňové
  identifikačné číslo); bez neho generovanie skončí chybou.
- **Adresa, telefón a e-mail spoločnosti** idú do hlavičky. *Ulica* vyplní
  element ulice a *Ulica2* element čísla domu.
- **Každý zamestnanec potrebuje rodné číslo.** Zadajte ho (9 alebo 10 číslic)
  do poľa *Identifikačné č* na karte *Personal* formulára zamestnanca. Lomka a
  medzery sa ignorujú.
- **Mená a adresy zamestnancov.** Príloha preberá súkromnú ulicu, PSČ a obec
  zamestnanca. **Posledné slovo mena je priezvisko** a všetko pred ním meno,
  preto mená zapisujte ako „Ján Peter Novák“, nie „Novák Ján“. Ak je
  nainštalovaný `hr_employee_firstname`, použijú sa jeho samostatné polia pre
  meno a priezvisko.
- Verzia tlačiva **Annual tax reconciliation statement 2023+** (schéma
  `HLASENIEv23`, platná od 1. 1. 2023) sa nainštaluje spolu s modulom a
  vyberie automaticky.

## Podanie za rok {#usage}

*Mzdové hlásenia → SK hlásenie o vyúčtovaní dane*, potom *Nové*.

1. Zvoľte **Rok**. Obdobím je vždy 1. január až 31. december.
2. **Typ opravy** nechajte na *Regular* (riadne hlásenie).
3. Kliknite na **Generovať**. Modul zoberie všetky nezrušené výplatné pásky
   spoločnosti, ktorých obdobie leží v danom roku — **vrátane konceptov** —,
   pre každého zamestnanca vytvorí stĺpec prílohy, vykreslí XML a overí ho
   voči oficiálnej schéme `rh2023.xsd`. Ak niektorému zamestnancovi chýba
   rodné číslo, chyba ho menuje a nič sa nevygeneruje.
4. XML si stiahnite z poľa *Príloha XML* a na portál finančnej správy ho
   nahrajte sami.
5. Po podaní kliknite na **Označiť ako odoslané**; podaná kópia sa uchová a
   záznam sa uzamkne. *Vrátiť do konceptu* ho odomkne.

## Čo sa vyplní do tlačiva {#mapping}

**I. časť (súhrn za zamestnávateľa):**

| Riadok | Čím sa vyplní |
|---|---|
| r. 00 | súčet `GROSS` za rok |
| r. 01 | zrazený preddavok pred bonusom: `INCOMETAX19` + `INCOMETAX25` pri Enterprise, `INCOMETAX` pri jadre OCA |
| r. 04 | rovná sa r. 01 (r. 02 a 03 zostanú prázdne) |
| r. 05 | súčet `CHILD_BONUS`, najviac do výšky r. 04 |
| r. 06 | zamestnanecká prémia — vždy 0,00, žiadne mzdové pravidlo ju nevytvára |

**III. časť (rekapitulácia daňového bonusu):**

| Riadok | Čím sa vyplní |
|---|---|
| r. A | celý daňový bonus vyplatený za rok (súčet `CHILD_BONUS`) |
| r. B | časť vyplatená z úhrnu zrazených preddavkov — rovná sa r. 05 |
| r. C | r. A − r. B: bonus vyplatený z vlastných prostriedkov zamestnávateľa, lebo prevýšil preddavky |

**V. časť (za každého zamestnanca), dvaja zamestnanci na stranu:** rodné
číslo, meno, súkromná adresa, štát `SK`, zdaniteľné príjmy (r. 3a, z `GROSS`),
zrazené preddavky (r. 4a), zamestnanecká prémia (r. 6) a vyplatený daňový
bonus (r. 8). Pri nepárnom počte zamestnancov má posledná strana druhý stĺpec
prázdny.

IV. časť sa nevypĺňa nikdy: všetci zamestnanci idú do V. časti. II. časť,
riadky D až F III. časti, ostatné riadky I. časti, počet detí pri zamestnancovi a počty a sumy
daňového bonusu na zaplatené úroky (§ 33a) a príspevku na rekreáciu v hlavičke
zostanú prázdne.

## Opravy {#corrections}

Hlásenie pozná druhy *riadne*, *opravné* a *dodatočné*. Nastavte **Typ
opravy** na *Corrective* alebo *Supplementary*. Modul opravné ani dodatočné
hlásenie nevygeneruje, kým nie je riadne hlásenie označené ako odoslané — pozri
však [Obmedzenia](#limitations): pôvodné hlásenie dnes hľadá len v **tom istom
mesiaci**, v ktorom bol nový záznam vytvorený.

## Obmedzenia {#limitations}

- **Sumy pred podaním skontrolujte.** Kontrola voči schéme overí tvar súboru,
  nie sumy. Žiadne hlásenie z tohto modulu zatiaľ nebolo overené skutočným
  podaním; prvé odsúhlaste ručne a význam stĺpcov porovnajte s aktuálnym
  poučením na vyplnenie hlásenia za príslušný rok.
- **Dvojslovné priezviská.** Bez samostatných polí pre meno sa za priezvisko
  berie len posledné slovo; pri zamestnancovi s dvojslovným priezviskom
  skontrolujte V. časť.
- **Riadok 5 a III. časť sa obmedzujú na ročné úhrny.** Riadok 5 je menšia
  z dvoch súm: ročný bonus a riadok 4. Ak v niektorých mesiacoch bonus prevýšil
  preddavky daného mesiaca a rozdiel ste si nárokovali v mesačných prehľadoch
  namiesto neskoršieho započítania, pred podaním porovnajte riadky 5 a C so
  svojimi mesačnými prehľadmi.
- Štát v prílohe je vždy `SK`; daňovníci s pobytom v zahraničí a príjmy
  zdaňované zrážkovou daňou sa osobitne nerozlišujú.
- **Ročné zúčtovanie sa nevykazuje.** Riadky pre jeho výsledky, počet detí pri
  zamestnancovi, poistné a nezdaniteľné časti základu dane zostanú prázdne.
- **Započítavajú sa aj koncepty** výplatných pások a pásky sa vyberajú podľa
  obdobia, nie podľa dňa výplaty.
- **Opravné a dodatočné hlásenie a mesiac.** Opravné alebo dodatočné hlásenie
  nájde pôvodné len vtedy, ak bolo vytvorené v tom istom kalendárnom mesiaci
  ako odoslané riadne hlásenie; inak generovanie skončí hlásením „There is no
  submitted … to amend“. Dátum zistenia dôvodov na podanie dodatočného
  hlásenia zostane prázdny.
- Element právnej formy v hlavičke: *Právna forma* zapísaná na kontakte spoločnosti modulom `l10n_sk_trade_registry`; bez tohto modulu alebo pri prázdnom poli zostáva element prázdny.
- Dodáva sa len vzor 2023. Overte, že ho finančná správa za rok, ktorý
  podávate, stále prijíma.
- Úradu sa nič neposiela: *Označiť ako odoslané* len zaznamená, že ste
  hlásenie podali.
