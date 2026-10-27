---
title: Česko — peněžní deník (daňová evidence)
summary: Peněžní deník pro daňovou evidenci — členění podle zavedené praxe, přiřazení české účtové osnovy, peněžní deník v PDF, údaje pro Přílohu č. 1 včetně oddílu D a zápis podle § 7b odst. 4.
verified: 19.0.1.0.5
---

## K čemu slouží {#purpose}

Česká část skupiny modulů peněžního deníku. Základ — jak z úhrad vznikají
řádky, generování, kontrola, tisk — popisuje
[návod k peněžnímu deníku CZ/SK](module:l10n_cssk_cash_journal_base). Tento
modul přidává to, co je české:

- **členění** peněžního deníku jako katalog kategorií;
- **přiřazení české účtové osnovy** k těmto kategoriím;
- **peněžní deník v PDF**;
- **údaje pro Přílohu č. 1** přiznání k dani z příjmů fyzických osob —
  ř. 101, ř. 102 a oddíl D — a **zápis o zjištění skutečného stavu** podle
  § 7b odst. 4.

Je určen pro OSVČ, která vede **daňovou evidenci**.

## Právní rámec {#legal}

- **Uspořádání není předepsáno.** Daňová evidence obsahuje údaje o příjmech a
  výdajích *„v členění potřebném pro zjištění základu daně“* a o majetku a
  dluzích — [§ 7b odst. 1 zákona o daních z příjmů](law:cz/1992/586). Sloupce
  žádný předpis nestanoví, proto katalog sleduje zavedenou praxi: daňové a
  nedaňové položky na obou stranách, průběžné položky a samostatná nepeněžní
  část pro odpisy a úpravy základu daně. Pojem *peněžní deník* pochází z
  jednoduchého účetnictví ([§ 13b zákona o účetnictví](law:cz/1991/563)),
  které OSVČ vést nemůže ([§ 1f](law:cz/1991/563)); slovenskou volbu
  *jednoduché účtovníctvo* proto česká společnost zvolit nemůže.
- **Pojistné podnikatele není daňovým výdajem.** Pojistné na sociální
  zabezpečení a příspěvek na státní politiku zaměstnanosti a pojistné na
  veřejné zdravotní pojištění hrazené poplatníkem s příjmy ze samostatné
  činnosti nelze uznat za výdaj —
  [§ 25 odst. 1 písm. g) zákona o daních z příjmů](law:cz/1992/586). Účet 526
  je proto přiřazen nedaňové kategorii, na rozdíl od Slovenska.
- **Zjištění skutečného stavu.** Poplatník provede zjištění skutečného stavu
  zásob, hmotného majetku, pohledávek a dluhů k poslednímu dni zdaňovacího
  období, provede o něm zápis a o případné rozdíly upraví základ daně podle
  § 24 a 25 — [§ 7b odst. 4 zákona o daních z příjmů](law:cz/1992/586).

## Nastavení {#setup}

Nainstalujte modul. Nainstaluje společný základ, načte katalog a přiřadí
účtovou osnovu každé společnosti se sídlem v Česku; společnost, která českou
osnovu načte později, se přiřadí v tu chvíli. Pak pokračujte nastaveními ze
[společného návodu](module:l10n_cssk_cash_journal_base#setup) — způsob vedení
evidence nastavte na *Daňová evidence*, zvolte rozdělení částečné úhrady a
při začátku v průběhu roku i začátek deníku.

Výchozí přiřazení podle začátku čísla účtu:

| Účty | Kategorie |
|---|---|
| 601, 602, 606, 607 | P2 Prodej výrobků a služeb |
| 604 | P1 Prodej zboží |
| 641 – 648, 661, 663, 665 – 668 | P3 Ostatní zdanitelný příjem |
| 662 (úroky) | PN9 Ostatní nedaňový příjem |
| 501, 112 | V1 Materiál |
| 504, 132 | V2 Zboží |
| 502, 503, 511, 512, 518 | V6 Provozní režie a služby |
| 521 – 523 | V4 Mzdy |
| 524, 525 | V5 Odvody za zaměstnance |
| 526 | VN5 Pojistné podnikatele — nedaňové |
| 527, 528, 531, 532, 538, 544, 548, 562, 563, 568, 569 | V9 Ostatní daňový výdaj |
| 513, 543, 545, 549 | VN9 Ostatní nedaňový výdaj |
| 01x – 04x | VN2 Nákup dlouhodobého majetku — výdajem není nákup, ale odpis |
| 551 | Z1 Odpisy (nepeněžní) |
| 591, 595 | VN4 Daň z příjmů |
| 343 | VN3 Odvod DPH při výdeji, PN3 Nadměrný odpočet při příjmu |
| 231, 461, 479 | VN6 Splátka úvěru při výdeji, PN2 Přijatý úvěr při příjmu |
| 491 | VN1 Osobní spotřeba při výdeji, PN1 Vklad podnikatele při příjmu |
| 261 | C1 Průběžné položky |

**Záměrně nepřiřazené:** 311 a 321 (modul přes ně dohledá fakturu), 314 a 324
(zálohy — sloupec závisí na tom, za co jsou, proto se nespárovaná záloha
označí ke kontrole) a účty, za kterými nikdy nestojí úhrada. Kategorie
*V3 Drobný majetek* a *Z2 Úprava základu daně* nejsou přiřazeny žádnému účtu;
přiřaďte je tam, kde je potřebujete.

## Kategorie {#categories}

| Kód | Kategorie | Ovlivňuje základ daně |
|---|---|---|
| P1, P2, P3 | Prodej zboží, prodej výrobků a služeb, ostatní zdanitelný příjem | ano (ř. 101) |
| PN1, PN2, PN3, PN9 | Vklad podnikatele, přijatý úvěr, nadměrný odpočet DPH, ostatní | ne |
| V1 – V6, V9 | Materiál, zboží, drobný majetek, mzdy, odvody za zaměstnance, provozní režie a služby, ostatní | ano (ř. 102) |
| VN1 – VN6, VN9 | Osobní spotřeba, nákup dlouhodobého majetku, odvod DPH, daň z příjmů, pojistné podnikatele, splátka úvěru, ostatní | ne |
| C1 | Průběžné položky | — |
| Z1, Z2 | Odpisy, úprava základu daně (nepeněžní) | ano (ř. 102) |

## Peněžní deník {#book}

*Účetnictví → Účetnictví → Peněžní deník → Tisk*, výstup **PDF**, vytiskne u
české společnosti deník se sloupci:

- **Pokladna**, **Banka**, **Průběžné položky** a **DPH**, každý se sloupcem
  *příjem* a *výdej*, s hrubou částkou, která se pohnula;
- sloupce členění — Prodej zboží, Prodej výrobků a služeb, Ostatní zdanitelný
  příjem, Nedaňový příjem, Materiál, Zboží, Drobný majetek, Mzdy, Odvody za
  zaměstnance, Provozní režie a služby, Ostatní daňový výdaj, Nedaňový výdaj —
  s částkou bez DPH; storno je záporné ve vlastním sloupci;
- **Zůstatek pokladna** a **Zůstatek banka** po každém řádku, od počátečního
  stavu v hlavní knize k předchozímu dni.

Vlastní kategorie spadne do *Ostatního zdanitelného příjmu* / *Ostatního
daňového výdaje* nebo do odpovídajícího nedaňového sloupce; odpisy se objeví v
*Ostatním daňovém výdaji*. Výstup **Tabulka** obsahuje seznam řádků a součty za
kategorie (bez listu s českým uspořádáním).

## Údaje pro Přílohu č. 1 {#priloha}

*Účetnictví → Účetnictví → Peněžní deník → Příloha č. 1 — údaje z deníku*:
zvolte období (výchozí je aktuální rok) a klikněte na **Vypočítat**.

| Oddíl | Co zobrazí |
|---|---|
| Příloha č. 1 | **ř. 101** příjmy a **ř. 102** výdaje podle § 7 — jen řádky ovlivňující základ daně, včetně odpisů a dalších nepeněžních řádků; **ř. 104** = ř. 101 − ř. 102 |
| Oddíl D | stavy na začátku a na konci období z hlavní knihy: 1 hmotný majetek, 2 hotovost (211), 3 bankovní účty (221), 4 zásoby (účtová třída 1), 5 pohledávky (31x), 6 ostatní majetek, 7 dluhy (32x), 8 rezervy (45x), 9 mzdy (331); poslední tři kladně |
| Kontrola | DPH v přijatých a v uhrazených platbách; průběžné položky příjem − výdej |

Úpravy podle § 5 a § 23, které nezaúčtujete jako zápis, patří na ř. 105 /
ř. 106 a nepočítají se zde. Obsahuje-li období řádky ke kontrole, upozornění
oznámí, že údaje nejsou úplné.

### Zápis o zjištění skutečného stavu (§ 7b odst. 4) {#zapis}

Tlačítko **Zápis podle § 7b odst. 4** vytiskne *Zápis o zjištění skutečného
stavu*: poplatníka, datum (konec zvoleného období), položky oddílu D na
začátku a na konci období a řádky pro datum a podpis. Zvolte období končící
posledním dnem zdaňovacího období.

Údaje v zápisu jsou **účetní** stavy. Zákon vyžaduje zjistit skutečný stav —
spočítat zásoby, prověřit majetek, odsouhlasit pohledávky a dluhy — a zapsat
případné rozdíly; výtisk slouží jako formulář k tomu.

## Omezení {#limitations}

- Součet pod sloupcem hodnot sčítá nesouvisející řádky; nevšímejte si ho.
- Položka nabídky je viditelná v každé společnosti včetně slovenských.
- Čísla řádků odpovídají Příloze č. 1, jak ji modul zná; ověřte je proti
  tiskopisu pro příslušný rok.
- Tabulka XLSX nemá list s českým uspořádáním; uspořádání deníku poskytuje
  PDF.
