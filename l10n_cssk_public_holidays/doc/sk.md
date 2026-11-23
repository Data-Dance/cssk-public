---
title: Sviatky: Slovensko a Česko
summary: Dopĺňa slovenské a české dni pracovného pokoja do kalendára sviatkov OCA, rok po roku, so zákonnými výnimkami, a slovenské udržiava aj ako štátne sviatky pracovných kalendárov.
verified: 19.0.1.0.2
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

## Pracovné kalendáre {#calendars}

Voľné dni a mzdy kalendár sviatkov nečítajú. Sviatok poznajú len ako *štátny
sviatok* pracovných kalendárov (*Voľné dni → Konfigurácia → Štátne sviatky*).
Modul preto slovenské sviatky udržiava aj tam:

- každá spoločnosť, ktorej krajinou je Slovensko, dostane jeden štátny sviatok
  za každý celoštátny riadok, bez určeného pracovného kalendára, takže platí
  pre všetky kalendáre spoločnosti, terajšie aj budúce;
- riadok, ktorý premenujete, presuniete, zmeníte na regionálny alebo zmažete,
  vezme svoj štátny sviatok so sebou a opakované generovanie nič nezdvojí;
- deň, na ktorý už spoločnosť má ručne zadaný štátny sviatok, sa ponechá
  tomuto záznamu;
- spoločnosť vytvorenú neskôr zachytí najbližší beh plánovanej akcie, od
  prvého dňa mesiaca pred týmto behom; ak chcete sviatky hneď, spustite ju
  ručne.

Zápis robí plánovaná akcia a zapisuje dni od prvého dňa predchádzajúceho
kalendárneho mesiaca. Mzdy za mesiac sa počítajú začiatkom nasledujúceho,
takže práve skončený mesiac je ešte otvorený: pri behu 5. septembra akcia
zapíše aj 29. august a 5. júl nechá tak. V januári vygeneruje aj
predchádzajúci rok, aby bol december na mieste.

Štátny sviatok, ktorý je pre spoločnosť nový, spôsobí, že Voľné dni
prepočítajú žiadosti o voľno, ktoré cezeň prechádzajú. Schválený týždeň
dovolenky cez piatok 29. augusta sa zmení z piatich dní na štyri, deň sa
vráti do nároku a Voľné dni to zamestnancovi oznámia v histórii žiadosti.
Pre otvorený mesiac je to správny počet; so starším obdobím to modul bez
vyžiadania nerobí. Sviatok, ktorý už v kalendároch je, sa znova nezapisuje,
takže opakovaný beh nič neprepočíta a nikomu nič neoznámi.

Inštalácia alebo aktualizácia modulu požiada plánovanú akciu o okamžitý beh,
takže sviatky pribudnú o chvíľu; kde plánované akcie nebežia, spustite ju
ručne. Riadok, ktorý pridáte alebo zmeníte ručne, sa uplatní hneď a bez
ohľadu na dátum. Ak chcete do kalendárov dostať
aj staršie sviatky, zavolajte `cssk_sync_calendar_leaves(date_from=…)` na
modeli `calendar.public.holiday`, napríklad zo serverovej akcie.

Systémový parameter `l10n_cssk_public_holidays.calendar_leave_countries`
obsahuje zoznam krajín oddelených čiarkou. Predvolená hodnota je `SK`. České
spoločnosti sú vynechané, kým sa české mzdy neoveria so sviatkom vnútri
neprítomnosti; `SK,CZ` ich pridá a `none` funkciu vypne. Zmena sa prejaví pri
najbližšom behu plánovanej akcie, ktorá zároveň odstráni sviatky krajiny
vyradenej zo zoznamu, od predchádzajúceho mesiaca.

## Obmedzenia {#limitations}

- Pravidlá sú tabuľkou v kóde. Pri zmene zákona treba modul aktualizovať; už
  vygenerované roky sa samy neopravia — zmažte dotknutý rok a vygenerujte ho
  znova.
- Len Slovensko a Česko, len celoštátne dni.
- Štátny sviatok zadaný ručne len pre jeden pracovný kalendár nepustí na ten
  deň celopodnikový záznam modulu, takže ostatné kalendáre spoločnosti ho
  nedostanú. Ručne zadaný záznam odstráňte alebo deň zadajte aj pre ostatné
  kalendáre.
- Nedele sa negenerujú: kalendár eviduje sviatky, pracovný čas určuje pracovný
  kalendár zamestnanca.
