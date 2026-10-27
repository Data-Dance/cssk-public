---
title: Import CAMT — výpisy, které projdou kontrolou zůstatku
summary: Opravuje dva případy, kdy správný výpis CAMT.053 v importu CAMT od OCA neprojde kontrolou zůstatku — denní konečné zůstatky a transakce rozdělené do více bloků podrobností.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Modul OCA `account_statement_import_camt` importuje bankovní výpisy ISO 20022
**CAMT.053**. Některé banky zapisují výpisy zcela správně, import je však
načte tak, že výpis nesedí se zůstatkem — zjištěno na skutečných výpisech
Tatra banky. Tento modul oba případy opravuje. Nepřidává obrazovku ani
nastavení; nainstalujte ho vedle importu CAMT od OCA a importujte jako dosud.

## Co mění {#changes}

**Konečný zůstatek za každý den.** Měsíční výpis může obsahovat jeden
počáteční zůstatek za měsíc a konečný zůstatek (`CLBD`) za každý den s
pohyby. Import OCA vezme první `CLBD`, takže výpis „končí“ zůstatkem prvního
dne a nikdy nesedí. Tento modul vezme **nejpozdější** konečný zůstatek a
**nejdřívější** počáteční zůstatek (`OPBD` nebo `PRCD`) — podle jejich dat, a
nemají-li datum, podle pořadí v souboru. Výpisu s jediným konečným zůstatkem
se nedotkne.

**Jedna transakce rozdělená do více bloků podrobností.** Import OCA vytvoří
za každý blok `TxDtls` položky jeden řádek výpisu a blok bez vlastní částky
zdědí celou částku položky. Banka, která jeden poplatek popíše ve dvou blocích
— v jednom reference, ve druhém částku —, tak dostane poplatek zaúčtovaný
dvakrát. Když řádky položky **nedávají v součtu** částku položky, modul její
bloky sloučí do **jednoho řádku** na částku položky; každý údaj vezme z
prvního bloku, který ho má, a poznámky spojí. Skutečná hromadná položka, jejíž
bloky mají vlastní částky a v součtu dávají částku položky, si ponechá řádek
za každou platbu.

## Použití {#usage}

Způsob importu se nemění: *Účetnictví → Účetnictví → Import Statement* (nebo
**Import Statement (OCA)** na kartě bankovního deníku), vyberte soubor CAMT,
**Import and View**. Počáteční a konečný zůstatek výpisu nyní odpovídají jeho
řádkům.

## Omezení {#limitations}

- Jde o dočasné řešení: obě opravy jsou kandidáty na zařazení přímo do modulu
  OCA a po jejich přijetí tam bude tento modul zbytečný.
- Rozhodnutí o sloučení se opírá jen o částky. Položka, jejíž bloky nesedí z
  jiného důvodu, se také sloučí do jednoho řádku; sloučený řádek nese partnera
  a reference prvního bloku.
- Mění jen import CAMT od OCA, ne vlastní import CAMT v Odoo Enterprise.
