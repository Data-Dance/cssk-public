---
title: Prehľad miezd (dashboard)
summary: Hlavné mzdové ukazovatele — hrubá mzda, čistá mzda, odvody zamestnávateľa, celková cena práce a daň z príjmov — ako dlaždice, mesačný graf a kontingenčná tabuľka v aplikácii mzdy OCA.
verified: 19.0.1.2.0
---

## Na čo slúži {#purpose}

Aplikácia mzdy OCA (*Výplatná listina*) počíta výplatné pásky, ale nemá
prehľad o tom, koľko mzdy stoja v čase. Modul do nej pridá dve obrazovky:

- **Prehľad** s dlaždicami súhrnných hodnôt hlavných ukazovateľov za celú
  históriu;
- **Analýza** — kontingenčnú tabuľku a čiarový graf riadkov výplatných pások
  podľa mesiacov, zamestnancov a ukazovateľov.

Modul **nie je viazaný na žiadnu krajinu**: závisí len od modulu `payroll`
(OCA) a nepridáva žiadne polia. Ukazovatele hľadá podľa **kódu** mzdového
pravidla, takže to, čo zobrazí, závisí od kódov vašich pravidiel (pozri
[Ktoré ukazovatele sa zobrazia](#figures)).

## Nastavenie {#setup}

Nič sa nenastavuje. Nainštalujte ho k aplikácii mzdy OCA; obe obrazovky sú
prístupné používateľom aj manažérom miezd.

## Prehľad (dashboard) {#dashboard}

*Výplatná listina → Prehľad* zobrazí sedem dlaždíc pre každú spoločnosť
vybranú v prepínači spoločností:

| Dlaždica | Výpočet |
|---|---|
| Hrubé mzdy spolu | súčet riadkov výplatných pások s kódom `GROSS` |
| Čisté mzdy spolu | súčet riadkov s kódom `NET` |
| Odvody zamestnávateľa | súčet riadkov s kódom `SOCIALEMPLOYERTOTAL` (slovenské pravidlá) alebo `SOCIALERTOT` + `HEALTHERTOT` + `SOCIAL_DISCOUNT` (české pravidlá) |
| Celková cena práce | `GROSS` + odvody zamestnávateľa |
| Daň z príjmov | súčet riadkov s kódom `INCOMETAXTOTAL` (slovenské) alebo `INCOMETAXTOT` (české) |
| Výplatné pásky | počet výplatných pások |
| Zamestnanci | počet rôznych zamestnancov s výplatnou páskou |

Započítavajú sa len výplatné pásky v stave **Hotovo**; koncepty, pásky čakajúce
na overenie a zrušené pásky sa vynechajú. Každá spoločnosť má vlastné dlaždice
vo vlastnej mene a používateľ vidí len spoločnosti, do ktorých má prístup a
ktoré má vybrané; pri viacerých spoločnostiach je pod dlaždicou názov
spoločnosti.

Dlaždice sú súčty za **celú históriu miezd**: nedajú sa filtrovať podľa
obdobia ani zamestnanca. Na to slúži obrazovka Analýza.

## Obrazovka Analýza {#analysis}

*Výplatná listina → Analýza* otvorí kontingenčnú tabuľku riadkov výplatných
pások — ukazovatele v riadkoch, mesiace v stĺpcoch — s použitými filtrami
**Hlavné ukazovatele (hrubá/čistá/zamestnávateľ/daň)** a **Hotové výplatné
pásky**, obmedzenú na spoločnosti vybrané v prepínači spoločností. V grafe je
každý ukazovateľ samostatnou čiarou v čase, nikdy nie naskladaný, lebo hrubá
mzda už obsahuje čistú mzdu aj zrážky.

Vyhľadávanie pridáva filtre pre jednotlivé ukazovatele (*Hrubá mzda*, *Čistá
mzda*, *Náklady zamestnávateľa*, *Daň z príjmov*) a zoskupenia podľa
*Obdobia*, *Zamestnanca*, *Ukazovateľa* a *Kategórie*. Po odstránení filtra
hlavných ukazovateľov môžete analyzovať ľubovoľný iný kód pravidla — prémiu,
príplatok, zrážku — a po odstránení filtra hotových pások aj koncepty.

## Ktoré ukazovatele sa zobrazia {#figures}

Dlaždice poznajú kódy pravidiel oboch krajín pre jadro OCA: slovenské
[module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca) aj české
[module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca). České
pravidlá vedú sociálne a zdravotné poistenie zamestnávateľa v samostatných
súčtoch a zľavu na poistnom zamestnávateľa (`SOCIAL_DISCOUNT`) na vlastnom
riadku, preto sa sčítajú všetky tri — rovnaká suma ako české pravidlo
`EMPLOYERCOST` bez hrubej mzdy. Pri vlastných mzdových pravidlách sa
ukazovatele zobrazia, len ak pravidlá používajú rovnaké kódy.

## Obmedzenia {#limitations}

- Ukazovatele sa hľadajú len podľa kódu pravidla; pozri
  [Ktoré ukazovatele sa zobrazia](#figures).
- Na obrazovke Analýza sa rozsah spoločností riadi prepínačom spoločností;
  nie je to pravidlo záznamov, lebo jadro OCA ho na riadkoch výplatných pások
  nemá.
