---
title: CZ účetní závěrka — závěrkové účty 701 / 702 / 710
summary: Umožní účtovat na české závěrkové účty 701, 702 a 710, aby šlo uzávěrku roku i počáteční stavy vůbec zaúčtovat.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

V podvojném účetnictví se účetní knihy uzavírají a otevírají přes závěrkové
účty účtové třídy 7:

| Účet | Název | Úloha |
|---|---|---|
| 701 | Počáteční účet rozvažný | protiúčet počátečních zůstatků rozvahových účtů |
| 702 | Konečný účet rozvažný | protiúčet konečných zůstatků rozvahových účtů |
| 710 | Účet zisků a ztrát | převezme konečné zůstatky nákladových a výnosových účtů |

Česká účtová osnova v Odoo (`l10n_cz`) dodává tyto tři účty jako
podrozvahové a Odoo odmítne každý účetní doklad, který podrozvahový účet
kombinuje s běžným. Uzavření třídy 5 nebo 6 na účet 710, uzavření
rozvahových účtů na účet 702 i zaúčtování počátečních stavů proti účtu 701
jsou přesně takové kombinace, takže v dodaném stavu **nejde zaúčtovat ani
jedno z nich** — a to nejen na konci roku, ale už při zadání počátečních
stavů při přechodu na Odoo.

Modul opravuje právě tohle a nic dalšího.

## Právní rámec {#legal}

- Účetní jednotka uzavírá účetní knihy k poslednímu dni účetního období a
  otevírá je k prvnímu dni účetního období —
  [§ 17 odst. 2 písm. b) a odst. 1 písm. b) zákona o účetnictví](law:cz/1991/563).
- Počáteční zůstatky rozvahových účtů musí navazovat na konečné zůstatky,
  jimiž se bezprostředně předcházející období uzavřelo —
  [§ 19 odst. 4 zákona o účetnictví](law:cz/1991/563).
- Směrná účtová osnova pro podnikatele řadí závěrkové účty do účtové třídy 7
  *Závěrkové a podrozvahové účty*: skupina 70 *Účty rozvažné* a skupina 71
  *Účet zisků a ztrát* —
  [příloha č. 4 vyhlášky č. 500/2002 Sb.](law:cz/2002/500). Jsou to účty
  závěrkové, ne podrozvahové (ty tvoří skupiny 75 až 79).

## Co se změní {#retype}

Modul změní typ účtu u 701000, 702000 a 710000 z *Off-Balance Sheet* (v
českém překladu Odoo *Podrozvahový*) na *Equity* (v českém překladu Odoo
„Základní kapitál“):

- u každé společnosti, která už českou osnovu má, jednorázově při instalaci
  modulu — a jen tam, kde je účet stále podrozvahový; typ, který jste
  nastavili sami, zůstane;
- u společností, které českou osnovu načtou později, přes šablonu účtové
  osnovy.

Modul nemá žádná nastavení ani nové obrazovky. Co to pro vás znamená:

- Uzávěrkové a otevírací zápisy i počáteční stavy proti účtu 701 jde
  zaúčtovat.
- Českých statutárních výkazů se změna nedotkne: řádky přiřazují podle
  **čísla** účtu, ne podle typu účtu.
- Obecná rozvaha Odoo teď tyto tři účty ukazuje ve vlastním kapitálu. Po
  spárovaném uzavření a otevření jsou nulové, ale v období s uzavřením a
  dosud bez otevření (nebo naopak) na nich zůstatek vidět je.

## Omezení {#limitations}

- Modul uzávěrkové zápisy **nevytváří**. Zaúčtujte je sami, nebo nástrojem,
  jako je modul OCA `account_fiscal_year_closing`, pro který se česká
  šablona uzávěrky nedodává (slovenský modul
  [module:l10n_sk_fiscal_year_closing](module:l10n_sk_fiscal_year_closing)
  ji pro slovenskou osnovu má).
- Mění se jen společnosti s českou osnovou (`cz`). Podrozvahové účty, které
  si sami založíte ve skupinách 75 až 79, svůj typ podle očekávání ponechají.
- Pokud uzávěrkové a otevírací zápisy účtujete, vedte je v samostatném
  deníku a zařaďte ho mezi *Deníky závěrky roku* společnosti
  ([module:l10n_cssk_core](module:l10n_cssk_core)), aby je statutární výkazy
  i přiznání k dani z příjmů vynechaly; jinak je k poslednímu dni roku každý
  uzavřený účet nulový. V této verzi pole není na žádném formuláři; nastaví
  ho administrátor, například importem do seznamu společností.
