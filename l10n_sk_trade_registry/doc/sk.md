---
title: SK výpis z registra (§ 3a, stav, predmety podnikania, závierky)
summary: Uchováva zápis slovenského subjektu v registri ako údaje, skladá z nich vetu podľa § 3a Obchodného zákonníka pre vaše doklady a upozorní na partnerov, ktorých register vedie ako zrušených.
verified: 19.0.2.0.1
---

## Na čo slúži {#purpose}

Slovenský podnikateľ musí na dokladoch uvádzať, v ktorom registri je zapísaný
a pod akým číslom. Slovenská lokalizácia Odoo má na to pri spoločnosti jediné
textové pole **Obchodný register** (*Trade Registry*). Vyplní sa raz a potom sa
naň zabudne — a tlačí sa ďalej aj po tom, čo sa súd alebo číslo zmenili.

Tento modul:

- uchováva tri údaje zápisu — **Register**, **Registrový súd** (orgán, ktorý
  zápis vedie) a **Číslo zápisu** — ako samostatné polia pri vašej spoločnosti
  aj pri ktoromkoľvek kontakte;
- skladá z nich správnou slovenčinou vetu o zápise a udržiava s ňou v súlade
  pole **Obchodný register** spoločnosti;
- pri každom slovenskom kontakte ukáže, čo o ňom uvádza register: právnu
  formu, stav, predmety podnikania, uložené účtovné závierky a predchádzajúce
  názvy a sídla;
- na faktúre a došlej faktúre upozorní, ak je partner zrušený, vymazaný alebo
  pozastavený.

Údaje sa zadávajú ručne alebo ich z registra vyplní modul
[module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk),
ktorého mapovanie polí na ne ukazuje automaticky.

## Právny rámec {#legal}

Podľa [§ 3a ods. 1 Obchodného zákonníka](law:sk/1991/513#paragraf-3a.odsek-1)
je každý podnikateľ povinný na svojich obchodných listoch a objednávkach
vyhotovených v písomnej alebo elektronickej forme (*obchodné dokumenty*)
uvádzať obchodné meno, sídlo alebo miesto podnikania, právnu formu právnickej
osoby a identifikačné číslo. Podnikatelia zapísaní v obchodnom registri alebo v
inej evidencii podnikateľov uvádzajú aj **označenie registra, ktorý podnikateľa
zapísal, a číslo zápisu**. Podľa
[§ 3a ods. 2 a 3](law:sk/1991/513#paragraf-3a.odsek-2) to platí aj pre písomný
úradný styk a pre webové sídlo podnikateľa.

## Nastavenie {#setup}

*Nastavenia → Spoločnosti*, otvorte svoju slovenskú spoločnosť. Nad poľom
**Obchodný register** sú tri nové polia:

| Pole | Príklad |
|---|---|
| Register | Obchodný register |
| Registrový súd | Mestský súd Bratislava III |
| Číslo zápisu | Sro/12345/B — oddiel a vložka tak, ako ich píše register |

Modul z nich zloží vetu a zapíše ju do poľa **Obchodný register**, ktoré
slovenská lokalizácia Odoo tlačí na faktúrach:

> Zapísaná v Obchodnom registri Mestského súdu Bratislava III, oddiel: Sro,
> vložka č.: 12345/B

- Názov registra sa dá do lokálu a orgán do genitívu (*Mestský súd* →
  *Mestského súdu*, *Okresný úrad* → *Okresného úradu*). Názvy, ktoré modul
  nepozná, sa zapíšu presne tak, ako boli zadané.
- *Zapísaná* pri spoločnosti, *Zapísaný* pri fyzickej osobe (živnostníkovi).
- *oddiel / vložka č.* len pri Obchodnom registri. Ostatné registre dostanú
  *číslo zápisu: …* s číslom v zadanom tvare, napr. *Zapísaný v Živnostenskom
  registri Okresného úradu Trnava, číslo zápisu: 250-12345*.

**Vaše vlastné znenie má prednosť.** Ak do poľa **Obchodný register** napíšete
niečo iné, modul ho odvtedy nechá tak. Zložená veta je zobrazená aj ako
upraviteľné pole **Veta podľa § 3a** pri kontakte spoločnosti; úprava tam sa
prenesie aj do poľa **Obchodný register** a platí, kým sa niektorý z údajov
zápisu znova nezmení. Ak všetky tri údaje vymažete, vymaže sa aj veta, ktorú
modul zapísal.

## Register pri kontakte {#partner}

Záložka **Register (SK)** pri kontakte so štátom Slovensko (alebo bez štátu):

| Skupina | Polia |
|---|---|
| Zápis | Register, Registrový súd, Číslo zápisu, Právna forma, Dátum vzniku, Veta podľa § 3a |
| Stav | Stav v registri, Dátum zániku, Veľkostná kategória, Register overený (kedy sa register naposledy čítal), Posledná závierka, Roky bez závierky |

Pod nimi, vyplnené z registra a len na čítanie:

- **Predmety podnikania** — každý s platnosťou a prípadným pozastavením.
  Predmet podnikania je oprávnenie na určitú činnosť, nie štatistický kód NACE.
  Ak je niektorý pozastavený bez dátumu ukončenia, záložka na to upozorní:
  subjekt je aktívny, ale túto činnosť vykonávať nesmie.
- **Účtovné závierky (RÚZ)** — obdobie, typ a dátum podania, schválenia a
  zostavenia. Len metaúdaje, žiadne čísla.
- **Predchádzajúce názvy a sídla** — s obdobím platnosti; pomôžu priradiť starší
  doklad k dnešnému partnerovi.

Tlačidlo **Požiadať ORSF o opätovné načítanie registrov** požiada ORSF, aby
subjekt znova načítal zo zdrojových registrov, keď je jeho kópia neúplná.
Čerstvé údaje sú k dispozícii asi o minútu; potom na kontakte spustite
*Actions → Update*. Tlačidlo vyžaduje modul ORSF.

## Zrušení partneri {#dissolved}

Keď je **Stav v registri** *Zrušená*, *Vymazaná* alebo *Pozastavená*:

- žltý pás v hornej časti kontaktu oznámi, že subjekt podľa registra
  neobchoduje, s dátumom zániku, ak je známy, a v zozname kontaktov je kontakt
  sivý (stĺpec so stavom sa tam dá zobraziť);
- faktúra, dobropis alebo pokladničný doklad spoločnosti so slovenskou daňovou
  krajinou zobrazí upozornenie so stavom, dátumom a dátumom overenia v
  registri. Pri došlej faktúre doplní, že dodávateľ v čase dodania nemusel
  existovať, a treba preto overiť nárok na odpočítanie dane;
- pri zaúčtovaní takého dokladu sa upozornenie zapíše aj do jeho chatteru.

Upozornenie zaúčtovanie nikdy nezablokuje. Konečná faktúra alebo neskoro
doručená faktúra od zaniknutého partnera môže byť úplne v poriadku; rozhoduje
dátum na doklade a posúdiť to môže len človek.

Všetkých takých partnerov naraz zobrazí *Účtovníctvo → Zákazníci → Zrušené
subjekty (SK)* alebo filter **Zrušené subjekty (SK)** v ktoromkoľvek zozname
kontaktov — zákazníkov, dodávateľov aj kontaktov.

## Obmedzenia {#limitations}

- Slovenská lokalizácia Odoo tlačí pole **Obchodný register** len na faktúrach,
  s označením *Obchodný register:*. § 3a sa týka aj objednávok, listov a
  webového sídla; tam vetu doplňte sami.
- Skloňovanie pozná krátky zoznam: Obchodný a Živnostenský register, registre
  nadácií, občianskych združení a neziskových organizácií a Mestský, Okresný a
  Krajský súd a Okresný úrad. Všetko ostatné sa vytlačí v zadanom tvare, čo
  môže znieť ťažkopádne. Vetu si raz skontrolujte.
- *Zapísaná* sedí pri spoločnosti; pri družstve alebo inom tvare v strednom
  rode vetu prepíšte.
- **Roky bez závierky** sa počítajú od predchádzajúceho kalendárneho roka bez
  ohľadu na lehotu na uloženie: začiatkom roka ukáže partner, ktorého posledná
  závierka je za predminulý rok, hodnotu 1, hoci lehota na uloženie poslednej
  ešte nemusela uplynúť.
- Okrem údajov zápisu pochádza všetko z ORSF. Bez neho zostanú stav, zoznamy aj
  upozornenie prázdne, ak stav nezadáte ručne.
