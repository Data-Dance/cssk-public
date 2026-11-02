---
title: Detaily ukazatelů MIS Builder
summary: Rozbalí ukazatel MIS Builder podle partnera, produktu, deníku, měsíce nebo jiného pole účetních položek, nejen podle účtů.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

[module:mis_builder](module:mis_builder) umí pod ukazatelem zobrazit jeho účty
(*Display details by account*). Otázka ale často zní jinak - kteří zákazníci
tvoří tržby, ve kterých měsících vznikly náklady. Tento modul umožní ukazatel
rozbalit podle libovolného pole účetních položek.

## Nastavení {#setup}

Otevřete šablonu výkazu MIS a v ní ukazatel. Vedle *Display details by
account*:

| Pole | Význam |
|---|---|
| Detaily podle | Pole účetních položek: *Partner*, *Produkt*, *Deník*, *Analytický účet*, *Datum* (řádek za měsíc)… |
| Nejvíce řádků detailu | Největší počet řádků detailu (výchozí 20); zobrazí se hodnoty s nejvíce položkami. |

## Jak se chová {#behaviour}

- Každý řádek detailu je ukazatel vypočtený s filtry sloupce a touto hodnotou,
  v každém sloupci výkazu - i ve sloupcích rozpadu.
- Rozkliknutí buňky detailu otevře přesně účetní položky této hodnoty.
- Rozbalí se jen ukazatel vypočtený přímo z účetních výrazů (například
  `-balp[60%]`). Ukazatel složený z jiných ukazatelů zůstane jedním řádkem:
  jeho detaily by vyžadovaly přepočítat každý ukazatel, ze kterého vychází,
  pro každou hodnotu.
- *Detaily podle* a *Display details by account* se navzájem vylučují.
