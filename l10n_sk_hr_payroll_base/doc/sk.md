---
title: Slovenské mzdy
summary: Celá skupina modulov slovenských miezd na jednom mieste — mesačná výplatná páska pre pracovný pomer a tri dohody v Odoo Enterprise Payroll alebo v aplikácii OCA payroll, s datovanými zákonnými sadzbami, voľnom, ročným zúčtovaním dane a zaúčtovaním do hlavnej knihy.
verified: 19.0.1.1.0
---

## Na čo slúži {#purpose}

Slovenské mzdy tvorí skupina modulov. Táto stránka opisuje skupinu ako celok;
jednotlivé doplnky majú krátke stránky, ktoré odkazujú sem.

| Modul | Čo robí |
|---|---|
| [module:l10n_sk_hr_payroll_base](module:l10n_sk_hr_payroll_base) (tento modul) | Štyri formy zamestnania a jedna tabuľka, ktorá určuje, aké poistenie a nároky patria ku každej z nich. Nezávislý od mzdového enginu, bez vlastných obrazoviek. |
| [module:l10n_sk_hr_payroll_ee](module:l10n_sk_hr_payroll_ee) | Slovenská výplatná páska v **Odoo Enterprise Payroll** ako nadstavba nad vlastným modulom Odoo `l10n_sk_hr_payroll`. |
| [module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca) | Tá istá výplatná páska v **aplikácii OCA payroll** (`payroll`) pre Odoo Community. |
| [module:l10n_sk_hr_payroll_account_ee](module:l10n_sk_hr_payroll_account_ee), [module:l10n_sk_hr_payroll_account_oca](module:l10n_sk_hr_payroll_account_oca) | Zaúčtovanie výplatných pások do slovenskej účtovej osnovy, pre každý engine jeden. |
| [module:l10n_sk_hr_payroll_surcharges](module:l10n_sk_hr_payroll_surcharges) | Mzdové zvýhodnenia a minimálne mzdové nároky šiestich stupňov náročnosti. |
| Výkazy pre úrady | Pozri [Výkazy pre úrady](#declarations). |

Samotný základný modul obsahuje formy zamestnania a tabuľku uplatniteľnosti.
Nainštaluje sa automaticky ako závislosť modulov enginu a stretnete sa s ním
len cez ne.

## Výber enginu {#engines}

Oba enginy počítajú tú istú výplatnú pásku z tých istých zákonných údajov a
vývojové testy prepočítajú rovnaké prípady v oboch a výsledky porovnajú.
Vyberáte teda mzdovú aplikáciu, ktorú prevádzkujete, nie slovenské pravidlá.

| | Enterprise (`_ee`) | OCA (`_oca`) |
|---|---|---|
| Mzdová aplikácia | Odoo Enterprise *Mzdy* (`hr_payroll`) so slovenskou lokalizáciou Odoo `l10n_sk_hr_payroll` | OCA `payroll`, funguje na Community |
| Ako je postavený | Nadstavba: slovenská štruktúra Odoo zostáva, jej pravidlá sa opravia na mieste a chýbajúce pravidlá sa doplnia | Vlastná úplná slovenská mzdová štruktúra |
| Formu zamestnania určuje | **typ štruktúry** (jeden na formu, všetky nad jednou štruktúrou) | **mzdová štruktúra** (jedna na formu, so spoločnými pravidlami) |
| Slovenské polia sú | na karte zamestnanca, záložka mzdy, skupina **Slovenská mzdová agenda (Data Dance)** | na karte zamestnanca, záložka mzdy, a na formulári šablóny zmluvy: skupiny **Slovenská mzdová agenda**, **Stravné (Slovensko)**, **Dohoda (Slovensko)**, **Exekúcia (Slovensko)** |
| Neprítomnosť sa do výplatnej pásky dostane cez | typy pracovných záznamov (*DOVOLENKA*, *PN*, *OCR*, …) | **Slovenský mzdový kód** na type voľna |
| Daň z príjmu na výplatnej páske | dva riadky (pásmo 19 % a vyššie pásma) a riadok *NČZD* | jeden riadok *Preddavok na daň z príjmu* |
| Zákonné sadzby vidno v | *Mzdy → Konfigurácia → Mzda → Parametre pravidla* | *Mzdy → Konfigurácia → Parametre pravidiel* (správca miezd) |
| Inštalácia | automaticky, keď je nainštalovaný `l10n_sk_hr_payroll` | zámerne |

Nadstavba pre Enterprise závisí od vlastného modulu Odoo a opravuje ho, nie
nahrádza: daň z príjmu sa počíta zo základu dane namiesto z hrubej mzdy, sadzby
zdravotného poistenia sú datované a doplnené sú nezdaniteľná časť základu
dane, daňový bonus na dieťa, sadzby pre ZŤP, doplatok do minimálneho
poistného, progresívne pásma dane a model stravného.

## Právny rámec {#legal}

Údaje, s ktorými výplatná páska počíta, vychádzajú z týchto predpisov.
Odkazy na paragrafy sú overené voči úplným zneniam platným v októbri 2026.

- **Formy zamestnania.** Dohodu o vykonaní práce možno uzatvoriť najviac na
  350 hodín v kalendárnom roku
  ([§ 226 ods. 1 Zákonníka práce](law:sk/2001/311#paragraf-226.odsek-1)),
  dohodu o pracovnej činnosti najviac na 10 hodín týždenne
  ([§ 228a ods. 1](law:sk/2001/311#paragraf-228a.odsek-1)), dohodu o
  brigádnickej práci študentov najviac na 20 hodín týždenne v priemere
  ([§ 227 ods. 2](law:sk/2001/311#paragraf-227.odsek-2)).
- **Ktoré poistenie sa platí.** Nemocenské poistenie a poistenie v
  nezamestnanosti sa týka zamestnanca s pravidelným mesačným príjmom
  ([§ 4 ods. 1 zákona o sociálnom poistení](law:sk/2003/461#paragraf-4.odsek-1));
  s nepravidelným príjmom je len dôchodkovo poistený
  ([§ 4 ods. 2](law:sk/2003/461#paragraf-4.odsek-2)). Len dôchodkovo poistený
  je aj ten, kto na DoVP alebo DoPČ poberá starobný, predčasný starobný,
  invalidný alebo (po dovŕšení dôchodkového veku) výsluhový dôchodok
  ([§ 4 ods. 1 písm. b)](law:sk/2003/461#paragraf-4.odsek-1.pismeno-b)).
  Poistenie v nezamestnanosti sa nevzťahuje na poberateľa starobného,
  predčasného starobného ani invalidného dôchodku pri poklese o viac ako
  70 % ([§ 19 ods. 3](law:sk/2003/461#paragraf-19.odsek-3)) a po priznaní
  starobného alebo predčasného starobného dôchodku neplatí poistné na
  invalidné poistenie ani zamestnanec, ani zamestnávateľ
  ([§ 128 ods. 3](law:sk/2003/461#paragraf-128.odsek-3)). Poistné na
  financovanie podpory v čase skrátenej práce sa platí len za zamestnanca v
  pracovnom pomere
  ([§ 128 ods. 1 písm. g)](law:sk/2003/461#paragraf-128.odsek-1.pismeno-g));
  zamestnávateľ, ktorý ho neplatí, platí poistné v nezamestnanosti 1 % namiesto
  0,5 % ([§ 136](law:sk/2003/461#paragraf-136)). Štatutárny orgán alebo
  jeho člen s najmenej 50 % účasťou na majetku zamestnávateľa nie je
  zamestnancom na účely garančného poistenia
  ([§ 4 ods. 4](law:sk/2003/461#paragraf-4.odsek-4)).
- **Sadzby sociálneho poistenia** určujú
  [§ 130 až 137](law:sk/2003/461#paragraf-130); maximálny mesačný
  vymeriavací základ je 11-násobok jednej dvanástiny všeobecného
  vymeriavacieho základu spred dvoch rokov, okrem úrazového poistenia
  ([§ 138 ods. 10](law:sk/2003/461#paragraf-138.odsek-10)). Jednotlivé sumy
  poistného sa zaokrúhľujú na eurocent nadol
  ([§ 129 ods. 2](law:sk/2003/461#paragraf-129.odsek-2)). Pri dohode s
  dôchodcom alebo študentom sa vymeriavací základ znižuje o odvodovú
  odpočítateľnú položku 200 eur mesačne
  ([§ 138a](law:sk/2003/461#paragraf-138a)).
- **Sadzby zdravotného poistenia** sú pre zamestnanca 5 % (pri osobe so
  zdravotným postihnutím 2,5 %) podľa
  [§ 12 ods. 1 zákona o zdravotnom poistení](law:sk/2004/580#paragraf-12.odsek-1)
  a pre zamestnávateľa 11 % (5,5 %) podľa prechodných ustanovení
  [§ 38ezg ods. 4](law:sk/2004/580#paragraf-38ezg.odsek-4) (2024 – 2025) a
  [§ 38ezk](law:sk/2004/580#paragraf-38ezk) (2026 – 2027). Mesačná
  odpočítateľná položka je 380 eur, s rastom príjmu nad 380 eur sa znižuje o
  jeho dvojnásobok a od príjmu 570 eur je nulová
  ([§ 16 ods. 16 a 17](law:sk/2004/580#paragraf-16.odsek-16)). Mesačný
  minimálny preddavok zamestnanca upravuje
  [§ 16a](law:sk/2004/580#paragraf-16a), ročné minimálne poistné
  [§ 13b](law:sk/2004/580#paragraf-13b).
- **Daň z príjmov.** Preddavok sa vyberá zo zdaniteľnej mzdy zníženej o
  poistné zamestnanca a o 1/12 nezdaniteľnej časti základu dane na daňovníka
  ([§ 35 ods. 1 zákona o dani z príjmov](law:sk/2003/595#paragraf-35.odsek-1));
  nezdaniteľná časť je 21-násobok životného minima a nad hranicou sa
  znižuje — do roku 2025 o štvrtinu základu dane, od roku 2026 o tretinu
  ([§ 11 ods. 2](law:sk/2003/595#paragraf-11.odsek-2)); pásma sadzby dane sú v
  [§ 15](law:sk/2003/595#paragraf-15); daňový bonus je 100 eur mesačne na
  dieťa do 15 rokov a 50 eur na dieťa od 15 do 18 rokov
  ([§ 33 ods. 1](law:sk/2003/595#paragraf-33.odsek-1)), najviac do
  percentuálneho limitu základu dane
  ([§ 33 ods. 6](law:sk/2003/595#paragraf-33.odsek-6)) a pri vyššom príjme sa
  znižuje ([§ 33 ods. 11](law:sk/2003/595#paragraf-33.odsek-11)). Ročné
  zúčtovanie upravuje [§ 38](law:sk/2003/595#paragraf-38).
- **Minimálna mzda.** Hodinová minimálna mzda je 1/174 mesačnej
  ([§ 2 ods. 2 zákona o minimálnej mzde](law:sk/2007/663#paragraf-2.odsek-2)).
- **Náhrady mzdy a stravovanie.** Priemerný zárobok sa zisťuje z
  predchádzajúceho kalendárneho štvrťroka, pri menej ako 21 dňoch alebo
  168 hodinách sa použije pravdepodobný zárobok
  ([§ 134 ods. 3 Zákonníka práce](law:sk/2001/311#paragraf-134.odsek-3)) a
  minimálna mzda je jeho spodnou hranicou
  ([§ 134 ods. 5](law:sk/2001/311#paragraf-134.odsek-5)); náhrada mzdy pri
  prekážkach na strane zamestnávateľa sa riadi
  [§ 142](law:sk/2001/311#paragraf-142); príspevok na stravovanie
  [§ 152 ods. 3 a 4](law:sk/2001/311#paragraf-152.odsek-3); výmera dovolenky
  [§ 103](law:sk/2001/311#paragraf-103).

## Nastavenie {#setup}

1. Nainštalujte modul enginu: v Enterprise sa
   [module:l10n_sk_hr_payroll_ee](module:l10n_sk_hr_payroll_ee) nainštaluje
   sám spolu so slovenskými mzdami Odoo; v Community nainštalujte
   [module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca). Ak sa majú
   výplatné pásky účtovať, pridajte účtovný mostík (pozri
   [Zaúčtovanie do hlavnej knihy](#accounting)).
2. Spoločnosť musí byť zo Slovenska. Slovenské typy voľna vidia len slovenské
   spoločnosti a v Enterprise aj slovenské polia zamestnanca.
3. Na každej zmluve zvoľte **formu zamestnania** typom štruktúry (Enterprise)
   alebo mzdovou štruktúrou (OCA). Názvy sa zobrazujú po anglicky:

   | Forma zamestnania | Typ štruktúry (Enterprise) | Mzdová štruktúra (OCA) |
   |---|---|---|
   | pracovný pomer | *Slovakia: Employee* | *Slovakia: Regular Pay* |
   | dohoda o vykonaní práce (DoVP) | *Slovakia: DoVP (agreement to perform work)* | *Slovakia: DoVP (agreement to perform work)* |
   | dohoda o pracovnej činnosti (DoPČ) | *Slovakia: DoPČ (agreement on work activity)* | *Slovakia: DoPČ (agreement on work activity)* |
   | dohoda o brigádnickej práci študentov (DoBPŠ) | *Slovakia: DoBPŠ (student work agreement)* | *Slovakia: DoBPŠ (student work agreement)* |

   Pole **Typ dohody** sa nastaví podľa výberu. Zmluva nesmie uvádzať iný typ
   dohody, ako zodpovedá jej štruktúre (typu štruktúry); Odoo ju neuloží a
   vyzve vás zmeniť štruktúru.
4. Vyplňte slovenské údaje zamestnanca opísané nižšie.

## Údaje zamestnanca a zmluvy {#employees}

| Pole | Čo robí |
|---|---|
| Podpísané vyhlásenie na zdanenie príjmov | Zamestnanec podpísal u tohto zamestnávateľa vyhlásenie: uplatní sa mesačná nezdaniteľná časť základu dane a daňový bonus. Naraz ich môže uplatňovať len jeden zamestnávateľ. |
| Deti do 15 rokov (daňový bonus), Deti 15–17 rokov (daňový bonus) | Počet detí na daňový bonus. |
| ZŤP / zdravotne postihnutý | Polovičné sadzby zdravotného poistenia (zamestnanca aj zamestnávateľa). |
| Uplatniť OOP na zdravotné poistenie | Uplatní odpočítateľnú položku na zdravotné poistenie pri nízkom príjme. Zobrazí sa len pri pracovnom pomere. |
| Typ dohody | Určuje ho štruktúra (typ štruktúry), pozri [Nastavenie](#setup). |
| Pravidelný mesačný príjem | Zobrazí sa pri dohodách. Rozhoduje o fondoch sociálneho poistenia: bez pravidelného príjmu sa platí len starobné a invalidné poistenie. Pri DoVP je predvolene vypnuté, pri DoPČ a DoBPŠ zapnuté; nastavte ho podľa dohody. Z DoBPŠ sa nemocenské poistenie ani poistenie v nezamestnanosti neplatí nikdy, bez ohľadu na toto pole. |
| Upozornenie na hodiny dohody | Zobrazí sa, keď pracovný kalendár zmluvy prekročí strop dohody: 350 hodín ročne pri DoVP (odhad ako týždenné hodiny × 52), 10 hodín týždenne pri DoPČ, 20 pri DoBPŠ. |
| Hodinová mzda (SK) | Len engine OCA: základná mzda sa vypočíta ako odpracované hodiny × táto sadzba namiesto mesačnej mzdy. Enterprise používa vlastný *Typ mzdy: hodinová* a *Hodinovú mzdu* Odoo. |
| Upozornenie na odmenu z dohody | Zobrazí sa, keď je hodinová odmena z dohody nižšia ako minimálna hodinová mzda platná dnes ([§ 119 ods. 1](law:sk/2001/311#paragraf-119.odsek-1), ktorý na dohody rozširuje [§ 223 ods. 2](law:sk/2001/311#paragraf-223.odsek-2)). Je to len upozornenie; výplatná páska odmenu nedopláca. |
| Priznaný dôchodok (SK) | Dôchodok, ktorý má pracovník priznaný. Na DoVP/DoPČ s ktorýmkoľvek z nich sa neplatí nemocenské poistenie ani poistenie v nezamestnanosti; poberateľ starobného, predčasného starobného alebo invalidného dôchodku nad 70 % neplatí poistenie v nezamestnanosti v žiadnej forme; po starobnom, predčasnom starobnom alebo (po dovŕšení dôchodkového veku) výsluhovom dôchodku neplatí invalidné poistenie ani jedna strana. Pozostalostné dôchodky v zozname nie sú, nič nemenia. |
| OOP z dohody (študent/dôchodca) | Pri dohode s dôchodcom alebo študentom zníži vymeriavací základ na starobné a invalidné poistenie a do rezervného fondu solidarity najviac o 200 eur. |
| Oslobodený od zdravotného poistenia (štátny poistenec) | Pri dohode: žiadne zdravotné poistenie, pre študenta alebo dôchodcu, za ktorého platí poistné štát. |
| Oslobodený od garančného poistenia (≥50 % štatutárny spoločník) | Bez garančného poistenia pre štatutárny orgán s najmenej 50 % účasťou. |
| Typ stravného, Dni stravného / mesiac | *Žiadne*, *Stravný lístok* alebo *Finančný príspevok* a počet dní (0 = odpracované dni z výplatnej pásky). |
| Vyživované osoby (exekúcia) | Osoby, ktoré zvyšujú nepostihnuteľnú sumu pri exekučných zrážkach. |

V engine OCA má zmluva navyše denné prepisy súm stravného. Enterprise na to
používa vlastné polia Odoo pre stravné lístky.

## Ako sa výplatná páska vypočíta {#payslip}

V poradí, v akom pravidlá bežia:

1. **Základná mzda.** Mzda zo zmluvy, pomerne znížená o hodiny neprítomnosti
   v období.
2. **Náhrady mzdy** v sume priemerného zárobku: *Náhrada mzdy za dovolenku*
   za hodiny dovolenky (len pracovný pomer), *Náhrada mzdy pri prekážke v
   práci* pri prekážkach podľa § 141 a *Employer Work Obstacle Pay (§ 142)*
   v sume 100 %, 50 %, 100 % alebo 60 % pri štyroch prekážkach na strane
   zamestnávateľa. Priemerný hodinový zárobok sa berie z potvrdených
   výplatných pások predchádzajúceho kalendárneho štvrťroka; ak v ňom
   zamestnanec neodpracoval 168 hodín, modul použije mzdu zo zmluvy delenú
   rozvrhnutými hodinami obdobia, nikdy však menej ako hodinovú minimálnu
   mzdu.
3. **Mzdové zvýhodnenia a doplatok do minimálneho mzdového nároku**, ak je
   nainštalovaný
   [module:l10n_sk_hr_payroll_surcharges](module:l10n_sk_hr_payroll_surcharges).
4. **Hrubá mzda.**
5. **Sociálne poistenie** zamestnanca aj zamestnávateľa, každý fond zo
   zastropovaného základu a zaokrúhlený na eurocent nadol. Nemocenské
   poistenie a poistenie v nezamestnanosti sa platia len pri pravidelnom
   príjme a pole *Priznaný dôchodok* ich (aj invalidné poistenie) odoberie
   tam, kde to zákon určuje — pozri [Na čo slúži](#purpose). Poistné na
   financovanie podpory sa platí len pri pracovnom pomere; pri dohode platí
   zamestnávateľ poistenie v nezamestnanosti 1 %. Úrazové poistenie nemá
   strop.
6. **Zdravotné poistenie** z celej hrubej mzdy, v bežnej sadzbe alebo v sadzbe
   pre ZŤP, s odpočítateľnou položkou, ak je uplatnená. Štátny poistenec na
   dohode neplatí nič.
7. **Doplatok do minimálneho zdravotného poistenia**: ak poistné zamestnanca a
   zamestnávateľa spolu nedosiahne poistné zo životného minima (minimálny
   preddavok), rozdiel sa zrazí zamestnancovi. Pri ZŤP a pri študentovi na
   DoBPŠ sa nepočíta a minimum sa pomerne znižuje o dni PN (vstup *PN days*,
   inak dni voľna PN) a o dni mimo trvania zmluvy.
8. **Základ dane z príjmu** = hrubá mzda − poistné zamestnanca na sociálne a
   zdravotné poistenie.
9. **Nezdaniteľná časť základu dane** (NČZD): pri podpísanom vyhlásení celá
   mesačná suma. Zníženie pri vyššom príjme sa rieši až v ročnom zúčtovaní,
   ako to ukladá § 35 ods. 1.
10. **Preddavok na daň z príjmu** podľa progresívnych pásiem platných v
    období.
11. **Daňový bonus na dieťa**: na každé dieťa podľa veku, bonus každého
    dieťaťa nad mesačnou hranicou znížený, najviac do percentuálneho limitu
    základu dane podľa počtu detí.
12. **Exekučné zrážky zo mzdy**, **Náhrada príjmu pri dočasnej PN** a
    **Ročné zúčtovanie dane**, ak sú (pozri nižšie).
13. **Stravné**: príspevok zamestnávateľa a pri stravných lístkoch podiel
    zamestnanca.
14. **Čistá mzda.**

**Práceneschopnosť.** *Náhrada príjmu pri dočasnej PN* je náhrada, ktorú
platí zamestnávateľ: 25 % denného vymeriavacieho základu za 1. až 3. deň a
55 % od 4. dňa, v roku 2025 do 10. dňa a od roku 2026 do 14. dňa, so
zastropovaným základom. Dni PN sa berú z voľna PN alebo zo vstupu *Dni
práceneschopnosti (PN)*; denný vymeriavací základ treba zadať ako vstup
*Denný vymeriavací základ pri PN (DVZ)*.

**Exekúcie.** S modulom
[module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base)
a evidovaným exekučným príkazom vypočíta zrážku register príkazov. Inak
zadajte dlžnú sumu ako vstup *Exekučné zrážky zo mzdy (neprednostná
pohľadávka)* alebo *(prednostná pohľadávka)*: jedna pohľadávka na výplatnú
pásku, tretina (neprednostná) alebo dve tretiny (prednostná) čistej mzdy nad
nepostihnuteľnou sumou a celý zvyšok nad trojnásobkom základnej
nepostihnuteľnej sumy.

**Stravné.** Príspevok zamestnávateľa na deň je 55 % stravného pri pracovnej
ceste v trvaní 5 až 12 hodín, zaokrúhlený na eurocent nahor — najviac, koľko
§ 152 ods. 3 na jedno jedlo dovoľuje. Pri *Stravnom lístku* platí zamestnanec
zvyšok hodnoty stravovacej poukážky v sume 75 % tohto stravného, čo je
najnižšia hodnota podľa § 152 ods. 4. Pri *Finančnom príspevku* sa príspevok
vyplatí s čistou mzdou.

## Zákonné údaje {#rates}

Všetky sadzby a sumy sú datované, výplatná páska teda použije údaj platný k
jej dátumu. Dodávané hodnoty:

| Údaj | 2025 | 2026 |
|---|---|---|
| Sociálne poistenie, zamestnanec | nemocenské 1,4 %, starobné 4 %, invalidné 3 %, v nezamestnanosti 1 % | rovnako |
| Sociálne poistenie, zamestnávateľ | nemocenské 1,4 %, starobné 14 %, invalidné 3 %, v nezamestnanosti 0,5 % (pri dohode 1 %), financovanie podpory 0,5 % (len pracovný pomer), garančné 0,25 %, úrazové 0,8 %, rezervný fond solidarity 4,75 % | rovnako |
| Maximálny mesačný vymeriavací základ | 15 730 € | 16 764 € |
| Zdravotné poistenie, zamestnanec (ZŤP) | 4 % (2 %) | 5 % (2,5 %) |
| Zdravotné poistenie, zamestnávateľ (ZŤP) | 11 % (5,5 %) | 11 % (5,5 %) |
| Odpočítateľná položka na zdravotné poistenie | 380 €, nulová od 570 € | rovnako |
| Minimálny základ zdravotného poistenia (mesačne) | 273,99 € | 284,13 € |
| NČZD na daňovníka, mesačne / ročne | 479,48 € / 5 753,79 € | 497,23 € / 5 966,73 € |
| Pásma dane (ročný základ dane) | 19 % do 48 441,43 €, nad tým 25 % | 19 % do 43 983,36 €, 25 % do 60 349,20 €, 30 % do 75 010,32 €, nad tým 35 % |
| Daňový bonus mesačne | 100 € do 15 rokov, 50 € od 15 do 18 rokov | rovnako |
| Limit daňového bonusu (1 … 6 a viac detí) | 29 / 36 / 43 / 50 / 57 / 64 % základu dane | rovnako |
| Daňový bonus sa znižuje nad (ročný základ dane) | 25 740 € | 27 432 € |
| Minimálna mzda, mesačná / hodinová | 816 € / 4,690 € | 915 € / 5,259 € |
| Stravné 5 až 12 hodín | 8,30 € | 9,30 € |
| Náhradu príjmu pri PN platí zamestnávateľ | 1. až 10. deň | 1. až 14. deň |

Údaj do nového roka posuniete tak, že pridáte novú datovanú hodnotu v
*Mzdy → Konfigurácia → Mzda → Parametre pravidla* (Enterprise) alebo v
*Mzdy → Konfigurácia → Parametre pravidiel* (OCA). Ročné zníženie NČZD a ročné pásma sú samostatné parametre, ktoré
používa len ročné zúčtovanie.

## Voľno {#leave}

Moduly enginov dodávajú slovenské typy voľna, každý priradený k mzdovému
kódu, ktorý určuje, ako s ním výplatná páska naloží. Ich názvy sa zobrazujú
po anglicky:

| Mzdový kód | Typy voľna | Na výplatnej páske |
|---|---|---|
| DOVOLENKA | dovolenka (*Holiday*) | v sume priemerného zárobku |
| PN | práceneschopnosť (*Sick Leave (PN)*), karanténa (*Quarantine / Isolation*) | náhrada príjmu od zamestnávateľa |
| OCR | ošetrovanie člena rodiny (*Family Care (OČR)*) | zamestnávateľ neplatí |
| NEPLATENE | neplatené voľno (*Unpaid Leave*), neplatené vzdelávanie (*Study Leave, unpaid*) | neplatené |
| OBSTACLE | platená prekážka v práci (*Paid Work Obstacle*), darovanie krvi, platené vzdelávanie, výkon verejnej funkcie, občianska povinnosť a tri prekážky s ročným limitom | v sume priemerného zárobku |
| PREKAZKA_* | štyri prekážky na strane zamestnávateľa podľa § 142 | v percente podľa § 142 |
| MATERSKA, RODICOVSKA, OTCOVSKA | materská, rodičovská a otcovská dovolenka | zamestnávateľ neplatí |

V engine OCA môžete priradiť aj vlastné typy voľna nastavením poľa
**Slovenský mzdový kód**.

**Plány nárokov na dovolenku.** Tri plány pripisujú dovolenku mesačne po 1/12
ročnej výmery: *Základná dovolenka – 4 týždne (20 dní)*,
*Dovolenka – 5 týždňov (25 dní, 33+/rodič)* a
*Dovolenka – 8 týždňov (40 dní, pedagogický zamestnanec)*. Ktorý platí, je
právna skutočnosť, ktorú modul neodvodí; priraďte ho každému zamestnancovi
alokáciou (*Voľné dni → Alokácie*). Tri alternatívne plány, ktoré pridelia
celý rok k 1. januáru, sa dodávajú archivované.

**Voľno s limitom.** *Krátkodobé OČR (ošetrovné) – limit 14 dní/rok* a tri
platené prekážky, ktoré vyžadujú alokáciu — lekárske vyšetrenie (7 dní ročne),
sprevádzanie rodinného príslušníka (7 dní) a sprevádzanie zdravotne
postihnutého dieťaťa (10 dní) — strážia ročný limit už pri zadaní voľna.

## Ročné zúčtovanie dane {#tax-reconciliation}

*Mzdy → Výplatné pásky → SK ročné zúčtovanie dane* (v engine OCA priamo v
hlavnom menu *Výplatná listina*) vedie jeden záznam na zamestnanca a daňový
rok pre ročné zúčtovanie preddavkov na daň.

1. Vytvorte záznam pre zamestnanca a rok. Pri zapnutom **Načítať z výplatných
   pások** tlačidlo **Vypočítať** sčíta základy dane, zrazené preddavky a
   vyplatený daňový bonus z výplatných pások roka; ak ho vypnete, súčty
   zadáte ručne.
2. Zadajte údaje, ktoré vyplývajú len z dokladov zamestnanca: **NČZD na
   manželku/manžela** (oprávnenú, už zníženú sumu), **Doplnkové dôchodkové
   sporenie (DDS, III. pilier)** (najviac 180 €) a **Zamestnanecká prémia**.
3. Záznam vypočíta ročnú NČZD na daňovníka s jej znížením pri vyššom príjme,
   ročnú daň podľa ročných pásiem, ročný nárok na daňový bonus a
   **Preplatok (+) / Nedoplatok (−)**.
4. Zvoľte **Zúčtovaciu výplatnú pásku** — výplatnú pásku mesiaca, v ktorom sa
   výsledok vysporiada — a kliknite na **Zaúčtovať zúčtovanie**. Výsledok sa
   pridá na túto výplatnú pásku ako vstup *Ročné zúčtovanie dane* a páska sa
   prepočíta; preplatok zvýši čistú mzdu, nedoplatok ju zníži.

Zamestnanec musí o ročné zúčtovanie požiadať do 15. februára, zamestnávateľ ho
vykoná do 31. marca a rozdiel vráti najneskôr pri zúčtovaní mzdy za apríl
([§ 38 ods. 1](law:sk/2003/595#paragraf-38.odsek-1),
[ods. 6](law:sk/2003/595#paragraf-38.odsek-6)). Tieto termíny modul nesleduje.
Ročné zúčtovanie zdravotného poistenia vykonáva zdravotná poisťovňa, nie
zamestnávateľ, a nie je súčasťou modulu.

## Zaúčtovanie do hlavnej knihy {#accounting}

[module:l10n_sk_hr_payroll_account_ee](module:l10n_sk_hr_payroll_account_ee)
(Enterprise) a
[module:l10n_sk_hr_payroll_account_oca](module:l10n_sk_hr_payroll_account_oca)
(OCA) priradia slovenským mzdovým pravidlám účty slovenskej účtovej osnovy,
takže potvrdená výplatná páska zaúčtuje vyrovnaný účtovný zápis:

| Účet | Riadky |
|---|---|
| 521000 Mzdové náklady | základná mzda, náhrada mzdy za dovolenku a pri prekážkach na strane zamestnanca aj zamestnávateľa, refundácie a — ak sú nainštalované — mzdové zvýhodnenia a doplatok do minimálneho mzdového nároku (MD) |
| 331000 Zamestnanci | čistá mzda (D) |
| 336000 Zúčtovanie s orgánmi SP a ZP | poistné zamestnanca, doplatok zdravotného poistenia a strana D každého odvodu zamestnávateľa |
| 524000 Zákonné sociálne poistenie | odvody zamestnávateľa (MD) |
| 342000 Ostatné priame dane | zrazený preddavok na daň; daňový bonus a ročné zúčtovanie proti nemu |
| 379000 Iné záväzky | exekučné a iné zákonné zrážky |
| 527000 Zákonné sociálne náklady / 333000 | príspevok zamestnávateľa na stravovanie proti záväzku voči zamestnancom; náhrada príjmu pri PN na 527000 |

- **Enterprise.** Vlastný modul Odoo `l10n_sk_hr_payroll_account` sa dodáva s
  prázdnym priradením účtov, sám teda nezaúčtuje nič. Mostík toto priradenie
  nahradí; Odoo potom priradí účty pre každú spoločnosť a vytvorí mzdový
  denník. Nainštaluje sa sám, keď je nainštalovaný modul Odoo aj nadstavba
  pre Enterprise.
- **OCA.** Účty sa nastavia na mzdových pravidlách pre každú spoločnosť pri
  inštalácii modulu, pre všetky spoločnosti, ktoré už majú slovenskú osnovu,
  a neskôr vždy, keď spoločnosť slovenskú osnovu načíta. Inštaluje sa
  zámerne a vyžaduje modul OCA `payroll_account`. Na zmluve zvoľte
  **Účtovnú knihu výplat**.
- **Mzdové zvýhodnenia.** Ich pravidlá patria modulu, od ktorého mostíky
  nezávisia. Účty sa im priradia pri nastavení spoločnosti a modul mzdových
  zvýhodnení si ich priradí sám, keď sa nainštaluje až po mostíku; iných
  pravidiel sa nedotkne.

## Výkazy pre úrady {#declarations}

Výkazy sú samostatné moduly postavené na
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
a fungujú s oboma enginmi:

| Modul | Výkaz | Komu |
|---|---|---|
| [module:l10n_sk_hr_payroll_mvp](module:l10n_sk_hr_payroll_mvp) | Mesačný výkaz poistného a príspevkov | Sociálna poisťovňa |
| [module:l10n_sk_hr_payroll_vpp](module:l10n_sk_hr_payroll_vpp) | Výkaz poistného a príspevkov pri nepravidelnom príjme (dohody) | Sociálna poisťovňa |
| [module:l10n_sk_hr_payroll_rlfo](module:l10n_sk_hr_payroll_rlfo) | Prihlášky a odhlášky zamestnancov | Sociálna poisťovňa |
| [module:l10n_sk_hr_payroll_eldp](module:l10n_sk_hr_payroll_eldp) | Evidenčný list dôchodkového poistenia | Sociálna poisťovňa |
| [module:l10n_sk_hr_payroll_health](module:l10n_sk_hr_payroll_health) | Mesačný výkaz preddavkov na poistné | zdravotné poisťovne |
| [module:l10n_sk_hr_payroll_monthly_tax_overview](module:l10n_sk_hr_payroll_monthly_tax_overview) | Prehľad o zrazených a odvedených preddavkoch | finančná správa |
| [module:l10n_sk_hr_payroll_annual_tax_report](module:l10n_sk_hr_payroll_annual_tax_report) | Hlásenie o vyúčtovaní dane | finančná správa |

## Obmedzenia {#limitations}

- **Minimálna hodinová mzda pri dohode** sa kontroluje len pri hodinovej
  odmene (*Hodinová mzda (SK)* v OCA, hodinový typ mzdy v Enterprise) a voči
  sume pri 40-hodinovom týždni; odmena dohodnutá paušálom a vyššia hranica
  pri kratšom ustanovenom týždennom pracovnom čase sa nekontrolujú.
- **Minimálny preddavok na zdravotné poistenie** sa znižuje len pri ZŤP,
  DoBPŠ, PN a dňoch mimo trvania zmluvy. Iné dni, keď je za zamestnanca
  platiteľom poistného štát (materská, rodičovský príspevok, dôchodca), modul
  nepozná; bez vstupu *PN days* sa namiesto kalendárnych dní použijú pracovné
  dni voľna PN a rozhodnutie zamestnanca s viacerými zamestnávateľmi minimum
  neuplatniť ([§ 16a ods. 5](law:sk/2004/580#paragraf-16a.odsek-5)) sa
  nemodeluje.
- **Odpočítateľná položka na zdravotné poistenie** sa za neúplný mesiac
  pomerne neznižuje a znižuje len základ zamestnanca.
- **Náhrada príjmu pri PN** sa na výplatnej páske nezdaňuje, denný
  vymeriavací základ treba zadať ručne a namiesto kalendárnych dní, ktoré
  počíta zákon, sa použijú pracovné dni voľna.
- **Priemerný zárobok** počíta hrubú mzdu bez riadkov náhrad mzdy z modulu a
  overuje len podmienku 168 hodín, nie 21 dní.
- **Dovolenka.** Nevyčerpaná dovolenka sa prenáša bez obmedzenia a
  neprepadá ([§ 113](law:sk/2001/311#paragraf-113)); kedy sa vyčerpá, určuje
  zamestnávateľ. Do verzie 19.0.1.18.3 (OCA) / 19.0.1.17.5 (Enterprise) ju
  plány po roku zrušili. Aktualizácia zruší čakajúci dátum zániku na
  existujúcich prideleniach, ale dni, ktoré už prepadli, sa neobnovia —
  skontrolujte ich. Dovolenka za odpracované dni podľa § 105 sa
  nemodeluje.
- **Sezónna DoPČ.** Vyššia odpočítateľná položka pri sezónnej práci je v
  údajoch, ale chýba pole, ktorým by sa sezónna dohoda označila.
- **Oba enginy.** Časť odvodu zamestnávateľa na starobné poistenie, ktorá ide
  do II. piliera, sa na výplatnej páske neuvádza osobitne.
- **Nadstavba pre Enterprise** nahrádza kód slovenských pravidiel Odoo; po
  aktualizácii Odoo overte, či do nich nepribudlo niečo nové.
- Údaje sa dodávajú za roky 2024 – 2026. Pred použitím pre neskoršie obdobie
  ich overte voči zákonu.
