---
title: SK VPP — výkaz poistného a príspevkov (dohody)
summary: Výkaz poistného a príspevkov za zamestnancov s nepravidelným príjmom — v praxi dohody DoVP a DoPČ — zostavený z výplatných pások mesiaca a vyexportovaný do XML overeného voči oficiálnej schéme.
verified: 19.0.1.2.0
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
  `MMRRRR`, oboje zo zvoleného mesiaca; typ výkazu R (riadny) alebo O (opravný).
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

## Opravný výkaz {#correction}

Formulár aj API predvyplnia pôvodný výkaz cez vyhľadanie podaného obdobia
v základnom module, ak existuje práve jeden uchovaný kandidát. Pri viacerých
kandidátoch vyberte pôvodný výkaz výslovne; program medzi nimi neháda.

Vygenerujte riadny natívny VPP; stav podaný zaznamenajte až po skutočnom podaní.
Pre opravu vytvorte nový VPP rovnakej firmy a mesiaca zúčtovania, vyberte opravný
typ a prepojte uchovaný podaný výkaz. Vygenerujte a overte XML štandardným postupom.
Výstup používa typ O, pôvodné číslo MM99RRRR a všetky aktuálne zdroje daného
obdobia. Nahrádza celý pôvodný výkaz. Pôvodná podaná príloha zostáva v natívnej
histórii bez zmeny.

Zmena firmy, obdobia, verzie či opravnej identity už vygenerovaného výkazu
vyžaduje návrat do návrhu. Riadny výkaz nemôže odkazovať na nahrádzaný výkaz.
Pôvodný musí mať stav podaný a uchovanú prílohu tej istej firmy a obdobia.
Označenie syntetického testu ako podaného nevykonáva žiadny prenos na úrad.

Táto funkcia neopravuje samotnú mzdu ani jej účtovný doklad. Oprava mzdy
a celkové odsúhlasenie sú samostatné workflow.

Zdroj: [poučenie SP k hlavičke](https://www.socpoist.sk/api/idsp/download/a4ab64fb-25b4-4321-9059-342b5945cd20).

## Obmedzenia {#limitations}

- Výber používa historický vzťah a pravidelnosť príjmu potvrdenej pásky.
  Nepravidelné DoVP, DoPČ a DoBPŠ patria sem; bežné pravidelné dohody ostávajú
  na MVP. Úplné rozpočítanie príjmu po skončení vyžaduje vlastné overené
  historické fondové napojenie, ktoré táto oprava nepridáva.
- Výplatná páska presahujúca hranicu mesiaca sa ignoruje. Mesiac je obdobie
  výplatnej pásky, ktoré sa môže líšiť od mesiaca, v ktorom bol príjem
  zúčtovaný na výplatu.
- Počet dní sleduje prekryv vzťahu s mesiacom; osobitné udalosti prílohy
  a fondové výnimky vyžadujú vlastné spracovanie. Príznak výnimky je 0.
- Dodáva sa vzor VPP 2026; úspešná schéma nepotvrdzuje prijatie portálom.
- Overenie voči schéme kontroluje tvar súboru, nie sumy.
