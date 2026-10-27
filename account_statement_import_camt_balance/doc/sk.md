---
title: Import CAMT — výpisy, ktoré prejdú kontrolou zostatku
summary: Opravuje dva prípady, keď správny výpis CAMT.053 v importe CAMT od OCA neprejde kontrolou zostatku — denné konečné zostatky a transakcie rozdelené do viacerých blokov podrobností.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Modul OCA `account_statement_import_camt` importuje bankové výpisy ISO 20022
**CAMT.053**. Niektoré banky zapisujú výpisy úplne správne, import ich však
načíta tak, že výpis nesedí so zostatkom — zistené na skutočných výpisoch
Tatra banky. Tento modul oba prípady opravuje. Nepridáva obrazovku ani
nastavenia; nainštalujte ho popri importe CAMT od OCA a importujte ako
doteraz.

## Čo mení {#changes}

**Konečný zostatok za každý deň.** Mesačný výpis môže obsahovať jeden
počiatočný zostatok za mesiac a konečný zostatok (`CLBD`) za každý deň s
pohybmi. Import OCA vezme prvý `CLBD`, takže výpis „končí“ zostatkom prvého
dňa a nikdy nesedí. Tento modul vezme **najneskorší** konečný zostatok a
**najskorší** počiatočný zostatok (`OPBD` alebo `PRCD`) — podľa ich dátumov,
a ak dátum nemajú, podľa poradia v súbore. Výpisu s jediným konečným
zostatkom sa nedotkne.

**Jedna transakcia rozdelená do viacerých blokov podrobností.** Import OCA
vytvorí za každý blok `TxDtls` položky jeden riadok výpisu a blok bez vlastnej
sumy zdedí celú sumu položky. Banka, ktorá jeden poplatok opíše v dvoch
blokoch — v jednom referencie, v druhom sumu —, tak dostane poplatok
zaúčtovaný dvakrát. Keď riadky položky **nedávajú v súčte** sumu položky,
modul jej bloky zlúči do **jedného riadku** na sumu položky; každý údaj vezme
z prvého bloku, ktorý ho má, a poznámky spojí. Skutočná hromadná položka,
ktorej bloky majú vlastné sumy a v súčte dávajú sumu položky, si ponechá
riadok za každú platbu.

## Použitie {#usage}

Spôsob importu sa nemení: *Účtovníctvo → Účtovníctvo → Importovať výpis*
(alebo **Import výpisov (OCA)** na karte bankového denníka), vyberte súbor
CAMT, **Importovať a zobraziť**. Počiatočný a konečný zostatok výpisu teraz
zodpovedajú jeho riadkom.

## Obmedzenia {#limitations}

- Ide o dočasné riešenie: obe opravy sú kandidátmi na zaradenie priamo do
  modulu OCA a po ich prijatí tam bude tento modul zbytočný.
- Rozhodnutie o zlúčení sa opiera len o sumy. Položka, ktorej bloky nesedia z
  iného dôvodu, sa tiež zlúči do jedného riadku; zlúčený riadok nesie partnera
  a referencie prvého bloku.
- Mení len import CAMT od OCA, nie vlastný import CAMT v Odoo Enterprise.
