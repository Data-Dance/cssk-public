---
title: Ťarchopisy — úpravy Data Dance
summary: Pomenuje tlačený ťarchopis odberateľovi, skryje tlačidlo Dobropis a zobrazí ťarchopisy odberateľom medzi dobropismi. Účtovanie necháva na Odoo.
verified: 19.0.1.0.1
---

## Na čo slúži {#purpose}

Modul Odoo *Ťarchopisy* (`account_debit_note`) pridá na zaúčtované faktúry
tlačidlo **Ťarchopis**: vytvorí novú faktúru prepojenú s pôvodnou na sumu,
o ktorú sa fakturované plnenie **zvyšuje**. To je slovenský ťarchopis a český
*opravný daňový doklad* zvyšujúci základ dane.

Tento modul upravuje tri veci okolo neho:

1. nadpis tlačeného ťarchopisu odberateľovi;
2. tlačidlo **Dobropis** na faktúrach, ktoré skryje;
3. zoznam *Dobropisy* odberateľom, v ktorom zobrazí aj ťarchopisy
   odberateľom.

Účtovanie dokladov nemení — pozri [Účtovanie](#posting).

## Právny rámec {#legal}

Dodatočné zvýšenie ceny je v oboch krajinách opravou základu dane a doklad,
ktorý ho zachytáva, je sám daňovým dokladom:

- **Slovensko.** Základ dane sa opraví pri zvýšení ceny tovaru alebo služby —
  [§ 25 ods. 1 písm. c) zákona o DPH](law:sk/2004/222#paragraf-25.odsek-1).
  Doklad, ktorý mení pôvodnú faktúru a osobitne a jednoznačne sa na ňu
  vzťahuje, je faktúrou podľa
  [§ 71 ods. 2](law:sk/2004/222#paragraf-71.odsek-2) a podľa
  [§ 74 ods. 3 písm. c)](law:sk/2004/222#paragraf-74.odsek-3.pismeno-c) musí
  obsahovať poradové číslo pôvodnej faktúry a údaje, ktoré sa menia.
- **Česká republika.** Základ sa opravuje podľa § 42
  [českého zákona o DPH](law:cz/2004/235) a opravný daňový doklad musí mať
  náležitosti podľa § 45 ods. 1 — okrem iného číslo pôvodného dokladu, dôvod
  opravy a rozdiel základu dane a dane.

Sprievodca ťarchopisom v Odoo zapíše číslo pôvodnej faktúry a zadaný dôvod
do poľa *Referencia* nového dokladu, ktoré sa na faktúre tlačí; riadky
ťarchopisu sú samotným rozdielom. Ďalšie údaje tento modul nepridáva.

## Tlačený ťarchopis {#report}

Ťarchopis odberateľovi sa tlačí s nadpisom **Ťarchopis**, **Návrh
ťarchopisu** alebo **Zrušený ťarchopis** a s jeho číslom. V češtine znejú
nadpisy *Opravný daňový doklad*, *Návrh opravného daňového dokladu* a
*Zrušený opravný daňový doklad*, v angličtine *Debit Note*, *Draft Debit
Note* a *Cancelled Debit Note*.

## Dobropisy a tlačidlo Dobropis {#credit-notes}

- Tlačidlo **Dobropis** na zaúčtovaných faktúrach odberateľom a dodávateľov
  je skryté. Dobropis možno vytvoriť zo zoznamu faktúr: označte doklad a
  použite *Akcia → Stornovať*.
- *Účtovníctvo → Zákazníci → Dobropisy* zobrazuje dobropisy odberateľom **a
  ťarchopisy odberateľom** — vlastný zoznam Odoo zobrazuje faktúry aj
  dobropisy s filtrom na dobropisy. Ťarchopisy od dodávateľov v ňom nie sú.

## Účtovanie {#posting}

Modul účtovanie nemení: faktúry, prijaté faktúry, dobropisy, ťarchopisy aj
účtovné zápisy účtuje Odoo so všetkými svojimi kontrolami a so všetkým, čo
k účtovaniu pridávajú ostatné nainštalované moduly.

Ťarchopis preto nemožno zaúčtovať so **záporným súčtom**, rovnako ako
žiadnu inú faktúru: zníženie ceny je dobropis.

Do verzie 19.0.1.0.0 modul nahrádzal účtovanie v Odoo starou kópiou, ktorá
pre všetky zápisy v databáze vynechávala niektoré kontroly — záporný súčet,
nedôveryhodný bankový účet spoločnosti, účet nezodpovedajúci denníku alebo
patriaci inej spoločnosti, archivovaný analytický účet — a obchádzala
rozšírenia účtovania z iných modulov. Verzia 19.0.1.0.1 ju odstránila.

## Obmedzenia {#limitations}

- Modul nepridáva žiadne náležitosti opravného dokladu nad rámec toho, čo
  ťarchopis v Odoo už obsahuje.
