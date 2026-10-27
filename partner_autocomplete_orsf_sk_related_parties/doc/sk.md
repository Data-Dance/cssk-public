---
title: Väzby v slovenských registroch (ORSF)
summary: Načíta z ORSF štatutárov a spoločníkov jedného partnera vrátane spoločníkov, ktorí sú firmami, a ďalšie firmy, s ktorými sú spojení — ako podklad na určenie závislých osôb podľa zákona o dani z príjmov.
verified: 19.0.2.1.0
---

## Na čo slúži {#purpose}

Ceny medzi **závislými osobami** musia zodpovedať cenám medzi nezávislými
osobami, a pritom nič v databáze Odoo nevie, ktorí partneri sú závislí od vás
alebo od seba navzájom. Graf vlastníckych a personálnych väzieb v ORSF na časť
tejto otázky odpovedá mechanicky: kto má vo firme funkciu a v ktorých ďalších
firmách majú funkciu tie isté osoby.

Modul pridá k slovenskému kontaktu záložku, ktorá na požiadanie načíta tento
graf pre jedného partnera a vypíše, čo našla — aj firmy, ktoré vo vašej
databáze ako kontakty nie sú.

## Právny rámec {#legal}

Odkazy sú na [zákon o dani z príjmov](law:sk/2003/595).

- **Kto je závislá osoba.** [§ 2 písm. n)](law:sk/2003/595#paragraf-2.pismeno-n):
  blízka osoba; ekonomicky, personálne alebo inak prepojená osoba alebo subjekt;
  osoba alebo subjekt, ktorý je na účely konsolidácie súčasťou konsolidovaného
  celku. [§ 2 písm. o)](law:sk/2003/595#paragraf-2.pismeno-o) vymedzuje
  ekonomické a personálne prepojenie: podiel najmenej 25 % na základnom imaní,
  hlasovacích právach alebo zisku, a pri personálnom prepojení vzťah členov
  štatutárnych, dozorných alebo obdobných orgánov k právnickej osobe — vrátane
  vzťahu medzi subjektmi pod kontrolou alebo vedením tej istej osoby.
- **Čo z toho vyplýva.** [§ 17 ods. 5](law:sk/2003/595#paragraf-17.odsek-5):
  súčasťou základu dane závislej osoby je aj rozdiel, o ktorý sa ceny alebo
  podmienky vo významných kontrolovaných transakciách líšia od cien alebo
  podmienok medzi nezávislými osobami, ak tento rozdiel znižuje základ dane
  alebo zvyšuje daňovú stratu.
- **Dokumentácia.** [§ 18 ods. 1](law:sk/2003/595#paragraf-18.odsek-1):
  o kontrolovaných transakciách a použitej metóde je daňovník povinný viesť
  dokumentáciu.

Register ukazuje len časť tohto testu. Vidno v ňom spoločných štatutárov, teda
personálne prepojenie, z ktorého je graf zostavený. Nevidno v ňom blízke osoby,
väčšinu podielov nad úrovňou funkcií ani „iné prepojenie“. **Zoznam berte ako
podklad pre účtovníka, nikdy nie ako záver.**

## Nastavenie {#setup}

ORSF poskytuje graf väzieb len prihlásenému kontu a kľúč API preň nevydáva. V
*Nastavenia → Všeobecné nastavenia → Kontakty*, pri poskytovateľovi **ORSF.SK**
(pozri [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk)),
vyplňte **E-mail konta ORSF** a **Heslo konta ORSF**. Prihlásenie sa potom
získava a obnovuje automaticky.

Heslo sa ukladá **ako čitateľný text** v databáze aj v každej zálohe. Použite
samostatné konto ORSF, nikdy nie osobné. Prihlásenie sa použije len na
načítanie grafu; automatické dopĺňanie a vyhľadávanie zostávajú anonymné.

## Načítanie väzieb {#usage}

1. Otvorte kontakt. Musí mať IČO v poli *IČO* (*Company ID*) alebo z
   predchádzajúceho automatického doplnenia.
2. Záložka **Väzby v registri (SK)** — zobrazí sa pri kontaktoch so štátom
   Slovensko alebo bez štátu.
3. Stlačte **Načítať z registra**. Môže to urobiť každý, kto smie kontakt
   upravovať.

Predchádzajúci zoznam sa nahradí tým, čo register uvádza teraz, a pri
vysvetlivke sa zobrazí čas načítania. Stĺpce:

| Stĺpec | Význam |
|---|---|
| Stupeň | **1** — fyzická osoba alebo firma s funkciou priamo v tomto partnerovi, napríklad konateľ alebo spoločník, ktorý je firmou. **2** — iná firma, s ktorou je tá istá osoba alebo firma spojená. |
| Názov, IČO | osoba (stupeň 1, bez IČO), firma s funkciou (stupeň 1, s IČO) alebo iná firma (stupeň 2) |
| Cez osobu | osoba — pri spoločníkovi, ktorý je firmou, táto firma — ktorá oba subjekty spája; pri firme 1. stupňa prázdne |
| Funkcia | funkcia v znení registra — konateľ, spoločník, člen predstavenstva |
| Súvisiaci kontakt | kontakt vo vašej databáze s týmto IČO v poli *IČO*, ak existuje |

Na kontakte sa zoznam nedá upravovať. Šípka na konci riadka otvorí súvisiaci
kontakt, ak existuje, a tlačidlo **Väzby v registri** v hornej časti kontaktu
otvorí zoznam samostatne.

Obrazovky hovoria o **väzbách v registri**, nie o závislých osobách: väzba v
registri je podnet, závislou osobou ju robí až zákonný test uvedený vyššie.

**Vždy len jeden partner, zámerne.** ORSF poskytuje graf pod podmienkou, že
volajúci nebudú hromadne načítavať osoby (odvoláva sa na oprávnený záujem podľa
čl. 6 ods. 1 písm. f) GDPR). Hromadná akcia, plánovaná úloha ani výber viacerých
záznamov preto neexistuje a nebude.

## Obmedzenia {#limitations}

- ORSF formát grafu nezverejňuje. Modul číta bežné formáty grafov a všetko, čo
  nepozná, preskočí, takže zmena formátu sa prejaví menším počtom riadkov, nie
  nesprávnymi riadkami. Pred použitím zoznamu porovnajte niekoľko partnerov s
  registrom.
- Siaha len po stupeň 2: firmy osôb z tohto partnera, nie firmy osôb z tých
  firiem.
- Fyzické osoby sa rozpoznávajú podľa toho, že nemajú IČO; všetko s IČO sa
  považuje za firmu.
- Neúspešné prihlásenie, vypršané prihlásenie alebo limit požiadaviek sa hlási
  ako „ORSF nevrátil graf pre IČO …“; príčina je v
  logu servera.
