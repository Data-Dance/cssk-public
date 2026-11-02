---
title: Rozpad sloupců MIS Builder
summary: Rozdělí sloupec MIS Builder na jeden sloupec za každý deník, partnera, společnost, produkt nebo jiné pole, a za nimi součet.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

V [module:mis_builder](module:mis_builder) se výkaz se sloupcem za každý deník,
partnera nebo společnost musel skládat ručně: jeden sloupec za každou hodnotu,
každý s vlastním analytickým filtrem, a udržovat ho s přibývajícími hodnotami.
Tento modul umožní jedinému sloupci rozdělit se podle libovolného pole
účetních položek.

## Nastavení {#setup}

Otevřete výkaz MIS (*Účetnictví › Výkazy › MIS Reports*) a na kartě *Columns*
sloupec. V části **Rozpad**:

| Pole | Význam |
|---|---|
| Sloupce podle | Libovolné pole typu many2one nebo výběr na účetních položkách sloupce: *Deník*, *Partner*, *Společnost*, *Produkt*, *Měna*, *Účet*, *Analytický účet*… Prázdné: bez rozpadu. |
| Nejvíce sloupců | Největší počet sloupců hodnot (výchozí 12). Zobrazí se hodnoty s nejvíce položkami; ostatní jsou jen v součtu. |

Při výpočtu výkazu se sloupec změní na jeden sloupec za každou hodnotu
nalezenou v jeho datech, pojmenovaný podle hodnoty a seřazený podle názvu,
a za nimi samotný sloupec jako **(celkem)**.

## Jak se chová {#behaviour}

- Filtry sloupce (data, analytické filtry, filtry výkazu) platí pro každý
  sloupec hodnoty.
- Součtové a porovnávací sloupce, které odkazují na rozpadnutý sloupec,
  fungují dál: použijí součet.
- **Rozkliknutí** sloupce hodnoty otevře přesně účetní položky této hodnoty.
- **Poznámky** fungují na každém sloupci: poznámka u sloupce hodnoty patří této
  hodnotě, poznámka u součtu celému sloupci.
- Položky bez hodnoty v poli (například bez partnera) tvoří vlastní sloupec
  *Nezadáno*.

## Omezení {#limitations}

Rozpadnout lze jen sloupce se zdrojem položek: *Actuals* a alternativní zdroje,
například rozpočty vedené po účtech, podle kteréhokoli pole těchto položek.
Rozpočty vedené po ukazatelích, součtové ani porovnávací sloupce ne.
