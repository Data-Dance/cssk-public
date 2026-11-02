---
title: Prehľad pre vedenie CZ/SK
summary: Jednostranový prehľad MIS Builder pre slovenskú a českú účtovú osnovu - peniaze, tržby a marže, doba inkasa a splatnosti, bežná likvidita a rentabilita aktív.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Údaje, na ktoré sa vedenie pýta najprv, na jednej strane a priamo z
účtovníctva: čo prišlo a odišlo z peňazí, čo sa predalo a s akou maržou, ako
dlho platia zákazníci a ako dlho my a či sú krátkodobé dlhy kryté. Je to
šablóna pre [module:mis_builder](module:mis_builder) postavená na triedach
účtov, ktoré majú slovenská a česká osnova spoločné.

## Použitie {#usage}

*Účtovníctvo › Výkazy › MIS Reports*, *Nový*, šablóna **Prehľad pre vedenie
(CZ/SK)**, a pridajte stĺpce, ktoré potrebujete - tento mesiac, tento rok,
rovnaké obdobie minulý rok, porovnanie. Údaje sa riadia dátumami a filtrami
stĺpca; každý sa dá rozkliknúť na účtovné položky.

## Z čoho sa údaje skladajú {#figures}

| Údaj | Účty |
|---|---|
| Peniaze a banka na začiatku / na konci | 21x, 22x, 261 - počiatočný a konečný zostatok |
| Príjmy / výdavky peňazí | pohyb má dať / dal na 21x, 22x, 261 (prevody medzi pokladnicou a bankou sa započítajú na oboch stranách) |
| Tržby | dalový zostatok 60x |
| Náklady na predaný tovar a materiál | 501, 504 |
| Hrubý zisk | tržby − náklady na predaný tovar a materiál |
| Výnosy spolu / Náklady spolu | trieda 6 / trieda 5 |
| Výsledok hospodárenia | výnosy spolu − náklady spolu |
| Hrubá / čistá marža | hrubý zisk / výsledok ÷ tržby |
| Pohľadávky / záväzky z obchodného styku | konečný zostatok 311 / 321 |
| Doba inkasa pohľadávok | pohľadávky ÷ tržby × dni obdobia |
| Doba splatnosti záväzkov | záväzky ÷ nákupy (účtové skupiny 50 a 51) × dni obdobia |
| Bežná likvidita | obežný majetok (trieda 1, peniaze, debetné zostatky 31x, 33x–35x, 37x, 38x) ÷ krátkodobé záväzky (kreditné zostatky 23x, 24x, 32x–34x, 36x–38x) |
| Rentabilita aktív | výsledok ÷ aktíva spolu (triedy 0 a 1, debetné zostatky tried 2 a 3) |

Marže a ukazovatele sa v súčtovom stĺpci nesčítavajú; zostatky tiež nie.

## Obmedzenia {#limitations}

Ide o manažérske ukazovatele z tried účtov, nie o účtovnú závierku:
spoločnosť, ktorá účtuje na nezvyčajné účty, si môže šablónu skopírovať
a upraviť (*Duplicate* v MIS Builder). Rentabilita aktív používa výsledok
obdobia, za mesiac je to teda mesačný údaj.
