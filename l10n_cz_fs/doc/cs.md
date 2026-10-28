---
title: CZ účetní výkazy (rozvaha / VZZ)
summary: Česká rozvaha, výkaz zisku a ztráty, přehled o peněžních tocích a přehled o změnách vlastního kapitálu sestavené z účetnictví a připravené k podání s přiznáním k dani z příjmů právnických osob.
verified: 19.0.1.2.0
---

## K čemu slouží {#purpose}

Česká národní vrstva účetních výkazů popsaných v
[module:l10n_cssk_fs_base](module:l10n_cssk_fs_base). Instaluje šest verzí
výkazů platných od 1. 1. 2025:

| Verze | Výkaz |
|---|---|
| Rozvaha 2025 (plný rozsah) | rozvaha v plném rozsahu; aktiva v brutto / korekce / netto |
| Rozvaha 2025 (zkrácený rozsah) | rozvaha ve zkráceném rozsahu |
| Výkaz zisku a ztráty 2025 (plný rozsah) | výkaz zisku a ztráty v druhovém členění, plný rozsah |
| Výkaz zisku a ztráty 2025 (zkrácený rozsah) | totéž ve zkráceném rozsahu |
| Přehled o peněžních tocích 2025 | přehled o peněžních tocích, nepřímá metoda |
| Přehled o změnách vlastního kapitálu 2025 | přehled o změnách vlastního kapitálu |

Každý účet české účtové osnovy se dostane právě do jednoho řádku, takže
*AKTIVA CELKEM* se rovnají *PASIVA CELKEM* a výsledek hospodaření ve výkazu
zisku a ztráty se rovná výnosům minus nákladům. Rozvahu a výkaz zisku a ztráty
podává modul [module:l10n_cz_dppo](module:l10n_cz_dppo) jako výkazy přiznání k
dani z příjmů právnických osob.

## Právní rámec {#legal}

- **Součásti.** Účetní závěrku tvoří rozvaha, výkaz zisku a ztráty a příloha;
  účetní závěrka obchodních společností zahrnuje i přehled o peněžních tocích
  a přehled o změnách vlastního kapitálu, které malé a mikro účetní jednotky
  nejsou povinny sestavovat —
  [§ 18 odst. 1 a 2 zákona o účetnictví](law:cz/1991/563).
- **Plný nebo zkrácený rozsah.** Účetní závěrka se sestavuje v plném nebo
  zkráceném rozsahu; ve zkráceném ji mohou sestavit účetní jednotky, které
  nemají povinnost auditu —
  [§ 18 odst. 4 zákona o účetnictví](law:cz/1991/563). Uspořádání stanoví
  prováděcí [vyhláška č. 500/2002 Sb.](law:cz/2002/500): rozvaha malé účetní
  jednotky ve zkráceném rozsahu obsahuje položky označené písmeny a římskými
  číslicemi a navíc C.II.1 až C.II.3, rozvaha mikro účetní jednotky jen
  položky označené písmeny ([§ 3a odst. 2](law:cz/2002/500)). Obchodní
  společnost sestavuje výkaz zisku a ztráty vždy v plném rozsahu; zkrácený
  (položky označené římskými číslicemi, písmeny a výpočtové položky) mohou
  sestavit jen malé a mikro účetní jednotky, které nejsou obchodní
  společností a nemají povinnost auditu ([§ 3a odst. 3 a 4](law:cz/2002/500)).
  Pořadí položek stanoví příloha č. 1 (rozvaha) a č. 2 (výkaz zisku a ztráty
  v druhovém členění).
- **Druh závěrky.** Závěrka sestavená k poslednímu dni účetního období je
  řádná, v ostatních případech mimořádná —
  [§ 19 odst. 1 zákona o účetnictví](law:cz/1991/563).
- **Zveřejnění.** Účetní jednotky zapsané ve veřejném rejstříku zveřejňují
  účetní závěrku uložením do sbírky listin —
  [§ 21a zákona o účetnictví](law:cz/1991/563).

## Nastavení {#setup}

Kromě [nastavení mechanismu](module:l10n_cssk_fs_base#setup) modul nic
zvláštního nevyžaduje. Pro export jsou potřeba dvě pole společnosti:

- *DIČ* — vyžaduje je každý export;
- *Finanční úřad* — vyžaduje se navíc, je-li nainstalován český modul pro
  podání ([module:l10n_cz_statutory](module:l10n_cz_statutory)).

**Štítky účtů pro výkaz zisku a ztráty v plném rozsahu.** Několik položek
plného rozsahu nelze rozlišit číslem účtu, proto čtou štítek účtu
(*Účetnictví → Konfigurace → Účtová osnova*, pole *Štítky*). Pro daný tok
založte analytický účet a dejte mu štítek:

| Štítek | Položka | Účet |
|---|---|---|
| VZZ IV.1 | výnosy z podílů – ovládaná nebo ovládající osoba | 665… |
| VZZ V.1 / V.2 | výnosy z ostatního dlouhodobého finančního majetku (dluhopisy, zápůjčky) – ovládaná osoba / ostatní | 665… |
| VZZ VI.1 | výnosové úroky – ovládaná nebo ovládající osoba | 662…, 666… |
| VZZ J.1 | nákladové úroky – ovládaná nebo ovládající osoba | 562… |
| VZZ E.1.2 | úpravy hodnot dlouhodobého nehmotného a hmotného majetku – dočasné | 559… |
| VZZ E.2 | úpravy hodnot zásob | 559… |

Částky bez štítku jdou do IV.2, VI.2, J.2 a E.3 (účet 558, zákonné opravné
položky, které zákon připouští jen k pohledávkám, je vždy E.3), takže
jednotka bez takových toků nic nastavovat nemusí. Účet smí nést jen jeden z
těchto štítků.

## Příprava výkazů {#usage}

*Účetnictví → Výkazy → Zákonné výkazy → Rozvaha* (nebo *Výkaz zisku a
ztráty*, *Přehled o peněžních tocích*, *Přehled o změnách vlastního
kapitálu*), *Nový*. Pro období od roku 2025 se předvyplní příslušná verze
2025 — u rozvahy a výkazu zisku a ztráty **plný rozsah**, který smí použít
každá jednotka a který každá obchodní společnost musí použít pro výkaz zisku
a ztráty. Pro zkrácený rozsah vyberte před výpočtem v poli *Verze* verzi
*(zkrácený rozsah)*. Klikněte na **Vypočítat** a strom zkontrolujte podle
[příručky mechanismu](module:l10n_cssk_fs_base#review).

**Co obsahují řádky:**

- **Rozvaha v plném rozsahu.** Všechny položky přílohy č. 1 v jejím pořadí
  až po B.I.2.1. Software nebo C.II.2.4.3. Stát – daňové pohledávky. Několik
  účtů se vykazuje na straně, kterou určí jejich vlastní zůstatek: přečerpaný
  bankovní účet (221) v C.II.2. Závazky k úvěrovým institucím, debetní
  zůstatek 336 nebo 341–347 v C.II.2.4.2 / C.II.2.4.3, kreditní zůstatek 373
  v C.II.8.7, odložená daňová pohledávka (debetní 481) v C.II.1.4. Osnova
  nemá účty dlouhodobých pohledávek, proto jsou položky C.II.1. kromě
  C.II.1.4 — a C.I.4., C.I.9.1., C.I.9.2. a vyměnitelné dluhopisy — *ruční*
  řádky: nulové, dokud nad ně nezadáte částku (o tutéž částku pak snižte
  krátkodobou položku).
- **Rozvaha ve zkráceném rozsahu.** Položky označené písmeny a římskými
  číslicemi: v aktivech A.,
  B.I.–B.III., C.I.–C.IV., D., v pasivech A.I.–A.VI., B., C.I., C.II., D.
  V obou rozsazích mají aktiva *Brutto* a *Korekci* (oprávky a opravné položky). Časové
  rozlišení se vykazuje v položkách D. Časové rozlišení aktiv / pasiv.
  **A.V. Výsledek hospodaření běžného účetního období** je pohyb účtových
  tříd 5 a 6 za období — tatáž částka jako výsledek ve výkazu zisku a
  ztráty —, takže rozvaha je vyrovnaná ještě před převodem výsledku na 431.
- **Výkaz zisku a ztráty v plném rozsahu.** Všechny položky přílohy č. 2
  včetně D.2.1–D.2.2 (524–526 / 527–528), E.1.1 (551, 557) a položek čtených
  ze štítků účtů popsaných v [Nastavení](#setup).
- **Výkaz zisku a ztráty ve zkráceném rozsahu.** Položky označené písmeny a
  římskými číslicemi s částí podpoložek (A.1–A.3, D.1–D.2, III.1–III.3,
  F.1–F.5, L.1–L.2), výpočtové položky a *Čistý obrat za účetní období*. Účet
  665 se vykazuje celý v položce IV.
- **Přehled o peněžních tocích.** Každý nepeněžní účet patří do provozní (A),
  investiční (B) nebo finanční (C) činnosti, takže A + B + C se rovná změně
  peněžních prostředků mezi *P.* (začátek) a *R.* (konec); řádek
  *G. Kontrola* ukáže případný rozdíl.
- **Přehled o změnách vlastního kapitálu.** Počáteční a konečný stav
  vlastního kapitálu a změny za rok po složkách; řádek *Kontrola* ukáže
  případný rozdíl.

## Podání {#filing}

- **S přiznáním k dani z příjmů právnických osob.** Vypočtenou rozvahu a
  výkaz zisku a ztráty připojte k přiznání v
  [module:l10n_cz_dppo](module:l10n_cz_dppo); podá je jako výkazy přiznání v
  rozsahu připojených výkazů. Oba musí být ve stejném rozsahu.
- **Exportovat XML** u výkazu vytvoří strukturovaný soubor ve vlastním
  formátu modulu. Pro samotné české účetní výkazy žádné oficiální schéma
  neexistuje, verze to uvádějí a soubor se exportuje bez ověření XSD. Není
  určen k podání; jako pracovní podklad použijte obrazovku a export do XLSX
  ([module:l10n_cssk_fs_xlsx](module:l10n_cssk_fs_xlsx)).
- PDF výkazů pro sbírku listin modul nevytváří.

## Omezení {#limitations}

- **Jen umístění časového rozlišení v D.** Vyhláška dovoluje vykázat časové
  rozlišení buď v C.II.3. / C.III., nebo v D. ([§ 3 odst. 3 a
  4](law:cz/2002/500)); oba rozsahy používají D.
- **Zkrácená a plná verze se liší u několika účtů.** Zkrácená rozvaha
  vykazuje 491 v A.IV. (plná v A.I.1, jak říká § 14 vyhlášky) a účty 221,
  336, 341–347, 373 a 481 netto jen na jedné straně. Součty sedí; kde na
  těchto účtech záleží, použijte plný rozsah.
- **Rozsah pro mikro účetní jednotky** (jen položky označené písmeny) není k
  dispozici; mikro jednotka může použít zkrácený rozsah.
- **Výsledky minulých let se do A.IV. musí dostat zápisy v účetnictví.**
  A.IV. čte účty 426, 428, 429 a 431 (ve zkráceném rozsahu i 491). Pokud předchozí rok nebyl uzavřen
  — jeho výsledek nebyl převeden na 431 účetní závěrkou a otevřením účetních
  knih —, není tento výsledek na žádném řádku a **AKTIVA a PASIVA se liší
  právě o tuto částku**. Zaúčtujte za ten rok uzavření a otevření (nebo
  převod na 431), řádek neupravujte. Do verze 19.0.1.1.1 četla A.V.
  kumulativní zůstatek tříd 5 a 6, a součty tak seděly jen proto, že
  výsledky minulých let skončily v A.V.
- C.II. Pohledávky nejsou z účetnictví rozděleny na dlouhodobé a krátkodobé
  (osnova pro to nemá účty); dlouhodobé částky zadejte nad ruční řádky
  C.II.1. plného rozsahu.
- Souhrnné opravné položky 091, 092, 095, 096 a 391 se vykazují u B.I.4,
  B.II.4.3, B.II.5.1, B.III.5 a C.II.2.1. Pokud se některá vztahuje k jiné
  položce, proberte vykázání s účetním.
- Výkazy lze založit až od roku 2025; starší verze neexistuje.
- Podrozvahové účty třídy 7 do žádného výkazu nepatří; pokud mají zůstatek,
  mohou se objevit v *Nepřiřazené účty* a tam je lze ignorovat.
- Přiřazení účtů vychází ze standardní české účtové osnovy a je třeba je
  odsouhlasit s účetním, zejména rozdělení pohledávek a závazků a přiřazení
  opravných položek.
