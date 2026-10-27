---
title: Časová os odpracovaných dní a vstupov miezd
summary: Časová os, kontingenčná tabuľka a zoznam odpracovaných dní a ďalších vstupov, z ktorých sa počítala každá výplatná páska, podľa zamestnancov v čase, v aplikácii mzdy OCA.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Výplatná páska sa počíta z **odpracovaných dní** (dni a hodiny podľa druhu —
bežná práca, dovolenka, choroba…) a z **ďalších vstupov** (sumy zadané za
obdobie). V aplikácii mzdy OCA (*Výplatná listina*) ich vidno len vnútri
každej pásky. Odoo Enterprise ich kontroluje na Ganttovom diagrame pracovných
záznamov; tento modul ponúka alternatívu pre Community: riadky všetkých
výplatných pások na jednej časovej osi a v kontingenčnej tabuľke na kontrolu.

Modul **nie je viazaný na žiadnu krajinu**: závisí len od modulov `payroll` a
`web_timeline` (OCA). Na každý riadok odpracovaných dní a vstupov uloží
zamestnanca a dátumy obdobia výplatnej pásky (polia *Employee*, *Period
Start*, *Period End*), aby sa riadky dali samostatne zoskupovať a umiestniť v
čase.

## Nastavenie {#setup}

Nič sa nenastavuje. Musí byť k dispozícii modul `web_timeline` z repozitára
OCA `web`. Pri inštalácii sa tri polia doplnia aj pre existujúce riadky
výplatných pások.

## Odpracované dni {#worked-days}

*Výplatná listina → Worked Days Timeline* otvorí časovú os zoskupenú podľa
zamestnancov. Každý riadok odpracovaných dní je pruh od začiatku po koniec
**obdobia jeho výplatnej pásky** s kódom a počtom dní a hodín; riadky s kódom
`WORK100` (bežné pracovné dni) sú zelené. Kliknutím na pruh riadok otvoríte;
podržaním *Ctrl* a kolieskom myši priblížite.

Prepnite na **kontingenčnú tabuľku** pre kontrolnú maticu — zamestnanec a kód
v riadkoch, mesiace v stĺpcoch, hodiny a dni ako miery — alebo na **zoznam**,
ktorý sčíta dni a hodiny. Vyhľadávanie ponúka filter *Worked (WORK100)* a
zoskupenia podľa *Employee*, *Code* a *Period*.

## Ďalšie vstupy {#inputs}

*Výplatná listina → Other Inputs* zobrazí vstupy všetkých výplatných pások
ako kontingenčnú tabuľku (zamestnanec a kód podľa mesiacov, súčet *Suma*)
alebo ako zoznam so súčtom; zoskupiť sa dajú rovnako.

## Obmedzenia {#limitations}

- **Pruhy pokrývajú obdobie výplatnej pásky, nie samotné dni.** Riadok
  odpracovaných dní zaznamenáva, koľko dní daného druhu páska započítala, nie
  v ktoré dni; každý riadok mesačnej pásky preto pokrýva celý mesiac a
  dovolenka uprostred mesiaca sa nezobrazí v skutočných dňoch.
- Zobrazia sa len riadky vypočítaných výplatných pások; kým pásky neexistujú,
  nie je čo ukázať. Zahrnuté sú aj riadky konceptov a zrušených pások — filter
  podľa stavu chýba.
- Vlastnú farbu má len `WORK100`; ostatné kódy majú predvolenú farbu.
- Modul nemá vlastný slovenský ani český preklad; jeho menu, filtre a názvy
  polí sú po anglicky.
