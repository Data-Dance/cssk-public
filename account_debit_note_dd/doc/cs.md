---
title: Opravné daňové doklady zvyšující základ — úpravy Data Dance
summary: Pojmenuje tištěný opravný daňový doklad zvyšující základ, skryje tlačítko pro dobropis a zobrazí tyto doklady odběratelům mezi dobropisy. Účtování nechává na Odoo.
verified: 19.0.1.0.1
---

## K čemu slouží {#purpose}

Modul Odoo pro opravné doklady zvyšující základ (`account_debit_note`, v
anglickém rozhraní *Debit Notes*) přidá na zaúčtované faktury tlačítko
**Opravný daňový doklad**: vytvoří novou fakturu propojenou s původní na
částku, o kterou se fakturované plnění **zvyšuje** — v Česku opravný daňový
doklad zvyšující základ daně (vrubopis), na Slovensku ťarchopis.

Tento modul upravuje tři věci kolem něj:

1. nadpis tištěného dokladu pro odběratele;
2. tlačítko pro dobropis na fakturách, které skryje;
3. seznam *Opravné daňové doklady* odběratelům, ve kterém zobrazí i doklady
   zvyšující základ vystavené odběratelům.

Účtování dokladů nemění — viz [Účtování](#posting).

V českém rozhraní Odoo nesou tlačítko pro dobropis i tlačítko pro doklad
zvyšující základ stejný popisek *Opravný daňový doklad*. Po instalaci
modulu zůstane na faktuře jen to druhé.

## Právní rámec {#legal}

Dodatečné zvýšení ceny je v obou zemích opravou základu daně a doklad, který
ji zachycuje, je sám daňovým dokladem:

- **Česká republika.** Základ daně se opravuje podle § 42
  [zákona o DPH](law:cz/2004/235) a opravný daňový doklad musí obsahovat
  náležitosti podle § 45 odst. 1 — mimo jiné evidenční číslo původního
  daňového dokladu, důvod opravy a rozdíl mezi opraveným a původním základem
  daně a daní.
- **Slovensko.** Základ dane sa opraví pri zvýšení ceny —
  [§ 25 ods. 1 písm. c) slovenského zákona o DPH](law:sk/2004/222#paragraf-25.odsek-1);
  doklad, který mění původní fakturu, je fakturou podle
  [§ 71 ods. 2](law:sk/2004/222#paragraf-71.odsek-2) a podle
  [§ 74 ods. 3 písm. c)](law:sk/2004/222#paragraf-74.odsek-3.pismeno-c) musí
  obsahovat číslo původní faktury a údaje, které se mění.

Průvodce v Odoo zapíše číslo původní faktury a zadaný důvod do pole
*Popis* (v anglickém rozhraní *Reference*) nového dokladu, které se na faktuře tiskne; řádky dokladu jsou
samotným rozdílem. Další náležitosti tento modul nepřidává.

## Tištěný doklad {#report}

Doklad pro odběratele se tiskne s nadpisem **Opravný daňový doklad**, **Návrh
opravného daňového dokladu** nebo **Zrušený opravný daňový doklad** a s jeho
číslem. Slovensky zní nadpisy *Ťarchopis*, *Návrh ťarchopisu* a *Zrušený
ťarchopis*.

## Dobropisy a tlačítko pro dobropis {#credit-notes}

- Tlačítko pro dobropis (*Opravný daňový doklad* vedle tlačítka pro doklad
  zvyšující základ) na zaúčtovaných fakturách odběratelům a přijatých
  fakturách je skryté. Dobropis lze vytvořit ze seznamu faktur: označte
  doklad a použijte *Akce → Vytvořit opravný doklad*.
- *Účetnictví → Zákazníci → Opravné daňové doklady* zobrazuje dobropisy
  odběratelům **a doklady zvyšující základ vystavené odběratelům** — vlastní
  seznam Odoo zobrazuje faktury i dobropisy s filtrem na dobropisy. Doklady
  zvyšující základ od dodavatelů v něm nejsou.

## Účtování {#posting}

Modul účtování nemění: faktury, přijaté faktury, dobropisy, doklady
zvyšující základ i účetní zápisy účtuje Odoo se všemi svými kontrolami a se
vším, co k účtování přidávají ostatní nainstalované moduly.

Doklad zvyšující základ proto nelze zaúčtovat se **záporným součtem**, stejně
jako žádnou jinou fakturu: snížení ceny je dobropis.

Do verze 19.0.1.0.0 modul nahrazoval účtování v Odoo starou kopií, která pro
všechny zápisy v databázi vynechávala některé kontroly — záporný součet,
nedůvěryhodný bankovní účet společnosti, účet neodpovídající deníku nebo
patřící jiné společnosti, archivovaný analytický účet — a obcházela rozšíření
účtování z jiných modulů. Verze 19.0.1.0.1 ji odstranila.

## Omezení {#limitations}

- Modul nepřidává žádné náležitosti opravného daňového dokladu nad rámec
  toho, co doklad v Odoo už obsahuje.
