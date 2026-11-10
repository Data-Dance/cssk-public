---
title: SK Oznámenia zdravotným poisťovniam (601)
summary: Overené personálne udalosti vo formáte XML a Latin2TXT601 so spoločným workflow a uchovaním podaní.
verified: 19.0.1.0.0
---

## Účel {#purpose}

Príprava oznámení zamestnávateľa pre VšZP25, Dôveru24 a Union27. Zdrojom je
skontrolovaná personálna udalosť, nie páska ani ďalšia mzdová kniha. Modul
nepotrebuje mzdový engine a využíva spoločnú evidenciu výkazov a doručenia.

## Pramene a rozhrania {#sources}

Implementácia vychádza z MU12/14/2014 aktualizovaného10.12.2025 vo
[Vestníku ÚDZS1/2026](https://www.udzs-sk.sk/wp-content/uploads/2026/01/VE_1_2026_sv.pdf).
README pri schéme uvádza postup extrakcie a hashe. XSD je odvodené z PDF,
nie samostatne stiahnutý originálny súbor úradu. XML používa UTF8, TXT601
ISO8859-2, CRLF, koncové oddeľovače a10/25/9 polí. Dátum zmeny RRRRMMDD
potvrdzuje aj [popis poisťovne](https://www.dovera.sk/najcastejsie-otazky/elektronicka-pobocka/e-pobocka-platitel).

## Postup {#workflow}

Personalista s oprávnením HR manager otvorí Mzdové výkazy / SK oznámenie601.
Vyberie poisťovňu, dátum a číslo dávky, identifikáciu platiteľa, vlastný bankový
účet a kontakt. Doplní zamestnanca, overený kód, Z(začiatok)/K(koniec)/X(storno
riadku), skutočný dátum zmeny a referenciu podkladu. Výber osoby predvyplní
identitu; BIČ smie byť iba skutočne pridelený identifikátor.

Samostatne sa potvrdzuje povinnosť zamestnávateľa hlásiť udalosť. Faktický
interval ePN alebo poistenca štátu neznamená automaticky ďalšie oznámenie.
Voliteľný zdrojový zdravotný kalendár musí byť skontrolovaný, patriť tej istej
osobe/firme a súhlasiť s hranicami zjednoteného intervalu. Mesačný orez
kalendára sám neurčuje vznik/zánik pracovného vzťahu každý mesiac. Storno
môže odkazovať na nahradený kalendár. Súbeh pracovného pomeru u rovnakého
zamestnávateľa potláča2D. Ak je nainštalovaný slovenský mzdový modul,
dátumovaný údaj o vyňatí blokuje začiatok2D; ukončenie a storno zostávajú
možné. Bez mzdového modulu sa oprávnenosť overuje ručne.

Generovanie preverí rozhranie a uchová presný súbor aj zdroj. Označenie
podania iba zaeviduje externý úkon, súbor neodosiela a nepotvrdzuje prijatie
poisťovňou. Návrat do návrhu zachová podané kópie. Úplná opravná dávka O má
výslovný odkaz na podanú dávku rovnakej firmy/poisťovne. Obsah opravy a reakciu
poisťovne treba skontrolovať; storno sa neodvodzuje automaticky a neprepisuje
zdrojový poistný ani mzdový kalendár.

## Hranice a overenie {#limits}

Publikovaný XML vzor má koncové medzery za2S(štrajk). Negatívny test najprv
overuje platný kontrolný súbor. Pre2S možno použiť TXT601, ak sa mená dajú
zapísať v Latin2; modul ich potichu neprepisuje. Bežné XML podporuje Unicode.
Pri súbehu oboch obmedzení treba schému potvrdenú poisťovňou alebo portál.

Modul neodvodzuje skutočné dni práce/odpočinku dohodára, priradenie
nepravidelného príjmu, externé oznámenia ePN ani pridelené identifikátory.
Potrebuje skontrolované podklady. Správna štruktúra súboru nie je dôkazom
právnej správnosti udalosti ani prijatia úradom. Natívny formulár je overený
pre platiteľa s IČO; založenie FO bez IČO nie je jeho overený rozsah. Nové
publikované rozhranie vyžaduje preverenie ďalšieho vzoru.

Testy preverujú XML/TXT, pripnutú odvodenú schému, povinné údaje, začiatok aj
koniec v ten istý deň, historickú udalosť s aktuálnym vzorom odoslania, HR
oprávnenia, oddelenie firiem, uchovanie opráv, kalendárne väzby a nemennosť
obsahu pri migrácii úložiska. Syntetické identity sa poisťovni neposielali.
