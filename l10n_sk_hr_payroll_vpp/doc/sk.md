---
title: SK VPP — výkaz poistného a príspevkov (dohody)
summary: Výkaz poistného a príspevkov za zamestnancov s nepravidelným príjmom — v praxi dohody DoVP a DoPČ — zostavený z výplatných pások mesiaca a vyexportovaný do XML overeného voči oficiálnej schéme.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

Zamestnanec, ktorému právny vzťah zakladá právo na **nepravidelný príjem**, je
poistený len na starobné a invalidné poistenie a poistné z takého príjmu
zamestnávateľ vykazuje na osobitnom výkaze, **VPP** (*Výkaz poistného
a príspevkov*). V praxi ide väčšinou o dohody — *dohodu o vykonaní práce*
(DoVP) a *dohodu o pracovnej činnosti* (DoPČ) — vyplácané nepravidelne.

Modul zostaví VPP z výplatných pások dohodárov za mesiac a vyexportuje ho do
XML pre portál Sociálnej poisťovne. Má rovnaký tvar ako mesačný výkaz MVP
([module:l10n_sk_hr_payroll_mvp](module:l10n_sk_hr_payroll_mvp)): sumy za
fondy a riadok prílohy za každého zamestnanca. Rovnako číta výplatné pásky cez
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
a funguje s oboma mzdovými jadrami — pozri
[príručku slovenských miezd](module:l10n_sk_hr_payroll_base#declarations).

## Právny rámec {#legal}

Odkazy sú na [zákon o sociálnom poistení](law:sk/2003/461).

- **Koho sa týka.** Zamestnancom na účely dôchodkového poistenia je aj
  fyzická osoba v právnom vzťahu, ktorý jej zakladá právo na nepravidelný
  príjem —
  [§ 4 ods. 2 písm. a)](law:sk/2003/461#paragraf-4.odsek-2.pismeno-a).
  Nemocenské poistenie a poistenie v nezamestnanosti sa viažu len na
  pravidelný mesačný príjem ([§ 4 ods. 1](law:sk/2003/461#paragraf-4.odsek-1)).
- **Povinnosť predložiť výkaz.**
  [§ 231 ods. 1 písm. g)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-g):
  výkaz poistného a príspevkov za kalendárny mesiac v lehote splatnosti
  poistného, v členení na zamestnancov a fondy.
- **Splatnosť.** Poistné z vymeriavacieho základu zamestnanca podľa § 4 ods. 2
  písm. a) je splatné **do ôsmeho dňa kalendárneho mesiaca nasledujúceho po
  kalendárnom mesiaci, v ktorom bol príjem zúčtovaný na výplatu** —
  [§ 143 ods. 1](law:sk/2003/461#paragraf-143.odsek-1).

## Nastavenie {#setup}

Rovnaké údaje spoločnosti a zamestnancov ako pri MVP:

- *IČO*, 8 až 12 číslic, na formulári spoločnosti;
- *Variabilný symbol Sociálnej poisťovne*, presne 10 číslic — vyplňte ho
  priamo vo formulári VPP. Ukladá sa na spoločnosti a je spoločný s modulmi
  MVP, RLFO a ELDP, vypĺňa sa raz; na jeho zmenu treba právo upravovať
  spoločnosti;
- **rodné číslo** zamestnanca v poli *Identifikačné č*;
- *Typ dohody* zamestnanca (zo slovenského mzdového modulu) nastavený na DoVP
  alebo DoPČ — podľa neho sa zamestnanec dostane do VPP.

## Zostavenie výkazu {#usage}

*Mzdové hlásenia → SK VPP (dohody)*, potom *Nové*.

1. Zvoľte **Rok** a **Mesiac**.
2. Kliknite na **Generovať**. Modul zoberie výplatné pásky spoločnosti, ktorých
   obdobie leží v danom mesiaci, ponechá tie, kde má zamestnanec *Typ dohody*
   DoVP alebo DoPČ, vytvorí riadok za každého zamestnanca, vygeneruje XML
   a overí ho voči `VPP-v2026.xsd`. Ak taká výplatná páska neexistuje, zastaví
   sa s hlásením.
3. XML stiahnite, nahrajte na portál a kliknite na **Označiť ako odoslané**.
   **Vrátiť do konceptu** výkaz znova otvorí.

## Obsah výkazu {#output}

- **Hlavička.** *Číslo výkazu* `MM99RRRR` a *obdobie výplaty príjmov*
  `MMRRRR`, oboje zo zvoleného mesiaca; typ výkazu R (riadny).
- **Fondy.** Rovnaké kódy pravidiel ako pri MVP (SICK/SICKEMPLOYER,
  PENSION/PENSIONEMPLOYER, DISABILITY/DISABILITYEMPLOYER,
  UNEMPLOYMENT/UNEMPLOYMENTEMPLOYER, ACCIDENT, GUARANTEEEMPLOYER,
  RESERVEFUNDEMPLOYER). Pri nepravidelnom príjme výplatná páska nemá
  nemocenské ani poistenie v nezamestnanosti, takže tieto riadky sú nulové.
- **Úhrn** (`spoluPoistne`): súčet riadkov fondov uvedených vyššie.
  Zdravotné poistenie doň nepatrí, odvádza sa zdravotným poisťovniam.
- **Príloha.** Za zamestnanca: rodné číslo, obdobie, typ vzťahu (*ZECD1N* pre
  DoVP, *ZECD2N* pre DoPČ — varianty s nepravidelným príjmom), vymeriavací
  základ (*GROSS*), dni, hodiny a sumy za jednotlivé fondy.

## Obmedzenia {#limitations}

- **Výber podľa typu dohody, nie podľa pravidelnosti príjmu.** Každá DoVP
  a DoPČ ide do VPP s kódom nepravidelného príjmu, aj keď má označený
  pravidelný mesačný príjem (taká patrí do MVP s kódom ZECD1/ZECD2). Keďže MVP
  dohody nevylučuje, taký dohodár sa objaví na oboch výkazoch. Dohoda
  o brigádnickej práci študentov (DoBPŠ) sa do VPP nedostane nikdy.
- Typ dohody sa číta z aktuálnej zmluvy zamestnanca, nie zo zmluvy, podľa
  ktorej bola výplatná páska vypočítaná.
- Započítajú sa aj koncepty výplatných pások, vynechajú sa len zrušené.
  Výplatná páska presahujúca hranicu mesiaca sa ignoruje. Mesiac je obdobie
  výplatnej pásky, ktoré sa môže líšiť od mesiaca, v ktorom bol príjem
  zúčtovaný na výplatu.
- Počet dní je pri každom riadku celý kalendárny mesiac; príznak výnimky
  z vymeriavacieho základu je vždy 0.
- Len riadny výkaz; opravy cez portál. Dodáva sa len vzor VPP 2026.
- Overenie voči schéme kontroluje tvar súboru, nie sumy.
