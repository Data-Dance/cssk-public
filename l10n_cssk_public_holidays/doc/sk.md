---
title: Sviatky: Slovensko a Česko
summary: Dopĺňa slovenské a české dni pracovného pokoja do kalendára sviatkov OCA, rok po roku, so zákonnými výnimkami.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Dovolenka a dochádzka nesmú počítať deň pracovného pokoja ako pracovný deň.
Modul OCA `calendar_public_holiday` (používa ho `hr_holidays_public` a
dochádzkové a mzdové moduly OCA) vedie jeden záznam sviatkov na rok a krajinu,
ale prázdny. Tento modul ho naplní slovenskými a českými **dňami pracovného
pokoja**.

Generujú sa iba dni pracovného pokoja. Sviatok, ktorý zákon v danom roku robí
pracovným dňom, sa v tom roku vynechá, lebo dovolenka a dochádzka ho musia
počítať ako pracovný deň. Mzdový príplatok za sviatok sa riadi vlastnými
pravidlami a modul ho neovplyvňuje.

## Právny rámec {#legal}

**Slovensko** — [§ 1 a § 2 zákona č. 241/1993 Z. z.](law:sk/1993/241#paragraf-2):
1. január, 6. január, Veľký piatok, Veľkonočný pondelok, 1. máj, 8. máj,
5. júl, 29. august, 15. september, 1. november a 24. – 26. december. Výnimky,
ktoré modul uplatňuje:

- 1. september (Deň Ústavy) je dňom pracovného pokoja len do roku 2023 a
  17. november len do roku 2024.
  [§ 2 ods. 3](law:sk/1993/241#paragraf-2.odsek-3) ich (spolu s 28. októbrom)
  ponecháva ako štátne sviatky, ktoré nie sú dňami pracovného pokoja.
- 8. máj a 15. september sú pracovnými dňami **len v roku 2026**: prechodné
  ustanovenie [§ 4b](law:sk/1993/241#paragraf-4b) uvádza iba tento rok, takže
  v roku 2027 sa vracajú, ak sa zákon znova nezmení.

**Česko** — [§ 1 až § 3 zákona č. 245/2000 Sb.](law:cz/2000/245):
1. január, Veľký piatok (od roku 2016), Veľkonočný pondelok, 1. máj, 8. máj,
5. júl, 6. júl, 28. september, 28. október, 17. november a 24. – 26. december.

## Ako to funguje {#usage}

- Pri inštalácii sa vygeneruje aktuálny a nasledujúci rok pre obe krajiny (ak
  krajina v databáze existuje).
- Mesačná plánovaná akcia *Štátne sviatky: vytvoriť ďalší rok (SK, CZ)*
  udržiava aktuálny a nasledujúci rok, takže nový rok pribudne sám.
- Záznamy sú v *Kalendár → Konfigurácia → Public Holidays*.

Generovanie len dopĺňa chýbajúce dni. Riadky, ktoré už na daný dátum
existujú, zostanú aj s vašimi úpravami; regionálny riadok (s vyplnenými
regiónmi) sa za celoštátny deň nepovažuje. Ak chcete zmenu vynútiť, zmažte
riadok alebo celý rok a plánovanú akciu spustite znova (*Nastavenia →
Technické → Naplánované akcie*, *Spustiť manuálne*).

## Obmedzenia {#limitations}

- Pravidlá sú tabuľkou v kóde. Pri zmene zákona treba modul aktualizovať; už
  vygenerované roky sa samy neopravia — zmažte dotknutý rok a vygenerujte ho
  znova.
- Len Slovensko a Česko, len celoštátne dni.
- Nedele sa negenerujú: kalendár eviduje sviatky, pracovný čas určuje pracovný
  kalendár zamestnanca.
