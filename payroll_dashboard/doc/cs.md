---
title: Přehled mezd (dashboard)
summary: Hlavní mzdové ukazatele — hrubá mzda, čistá mzda, odvody zaměstnavatele, celkové mzdové náklady a daň z příjmů — jako dlaždice, měsíční graf a kontingenční tabulka v aplikaci Mzdy OCA.
verified: 19.0.1.2.0
---

## K čemu slouží {#purpose}

Aplikace **Mzdy** (OCA) počítá výplatní pásky, ale nenabízí přehled o tom,
kolik mzdy stojí v čase. Modul do ní přidá dvě obrazovky:

- **Přehled** s dlaždicemi souhrnných hodnot hlavních ukazatelů za celou
  historii;
- **Analýza** — kontingenční tabulku a spojnicový graf řádků výplatních
  pásek podle měsíců, zaměstnanců a ukazatelů.

Modul **není vázán na žádnou zemi**: závisí jen na modulu `payroll` (OCA) a
nepřidává žádná pole. Ukazatele hledá podle **kódu** mzdového pravidla, takže
to, co zobrazí, závisí na kódech vašich pravidel (viz
[Které ukazatele se zobrazí](#figures)).

## Nastavení {#setup}

Nic se nenastavuje. Nainstalujte ho k aplikaci Mzdy (OCA); obě obrazovky jsou
přístupné uživatelům i manažerům mezd.

## Přehled (dashboard) {#dashboard}

*Mzdy → Přehled* zobrazí sedm dlaždic pro každou společnost vybranou v
přepínači společností:

| Dlaždice | Výpočet |
|---|---|
| Hrubé mzdy celkem | součet řádků výplatních pásek s kódem `GROSS` |
| Čisté mzdy celkem | součet řádků s kódem `NET` |
| Odvody zaměstnavatele | součet řádků s kódem `SOCIALEMPLOYERTOTAL` (slovenská pravidla) nebo `SOCIALERTOT` + `HEALTHERTOT` + `SOCIAL_DISCOUNT` (česká pravidla) |
| Celková cena práce | `GROSS` + odvody zaměstnavatele |
| Daň z příjmů | součet řádků s kódem `INCOMETAXTOTAL` (slovenská) nebo `INCOMETAXTOT` (česká) |
| Výplatní pásky | počet výplatních pásek |
| Zaměstnanci | počet různých zaměstnanců s výplatní páskou |

Započítávají se jen výplatní pásky ve stavu **Hotovo**; koncepty, pásky
čekající na ověření a zrušené pásky se vynechají. Každá společnost má vlastní
dlaždice ve vlastní měně a uživatel vidí jen společnosti, do kterých má
přístup a které má vybrané; při více společnostech je pod dlaždicí název
společnosti.

Dlaždice jsou součty za **celou historii mezd**: nelze je filtrovat podle
období ani zaměstnance. K tomu slouží obrazovka Analýza.

## Obrazovka Analýza {#analysis}

*Mzdy → Analýza* otevře kontingenční tabulku řádků výplatních pásek —
ukazatele v řádcích, měsíce ve sloupcích — s použitými filtry **Hlavní
ukazatele (hrubá/čistá/zaměstnavatel/daň)** a **Hotové výplatní pásky**,
omezenou na společnosti vybrané v přepínači společností. V grafu je každý
ukazatel samostatnou křivkou v čase, nikdy ne skládaný, protože hrubá mzda už
obsahuje čistou mzdu i srážky.

Vyhledávání přidává filtry pro jednotlivé ukazatele (*Hrubá mzda*, *Čistá
mzda*, *Náklady zaměstnavatele*, *Daň z příjmů*) a seskupení podle *Období*,
*Zaměstnance*, *Ukazatele* a *Kategorie*. Po odstranění filtru hlavních
ukazatelů lze analyzovat libovolný jiný kód pravidla — prémii, příplatek,
srážku — a po odstranění filtru hotových pásek i koncepty.

## Které ukazatele se zobrazí {#figures}

Dlaždice znají kódy pravidel obou zemí pro jádro OCA: slovenské
[module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca) i české
[module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca). Česká
pravidla vedou sociální a zdravotní pojištění zaměstnavatele v samostatných
součtech a slevu na pojistném zaměstnavatele (`SOCIAL_DISCOUNT`) na vlastním
řádku, proto se sčítají všechny tři — stejná částka jako české pravidlo
`EMPLOYERCOST` bez hrubé mzdy. S vlastními mzdovými pravidly se ukazatele
zobrazí, jen pokud pravidla používají stejné kódy.

## Omezení {#limitations}

- Ukazatele se hledají jen podle kódu pravidla; viz
  [Které ukazatele se zobrazí](#figures).
- Na obrazovce Analýza se rozsah společností řídí přepínačem společností;
  není to pravidlo záznamů, protože jádro OCA ho na řádcích výplatních pásek
  nemá.
