---
title: Import bankovních výpisů — GPC
summary: Importuje elektronické bankovní výpisy GPC (výpisový formát ABO českých a slovenských bank) se zůstatky, účty protistrany a symboly VS/KS/SS.
verified: 19.0.2.0.1
---

## K čemu slouží {#purpose}

**GPC** je elektronický výpis s pevnou délkou záznamů, který většina českých
a slovenských bank nabízí ke stažení vedle jiných formátů — Fio banka, KB, ČS,
ČSOB a další. Nese to, podle čeho účetní páruje platby: účet a kód banky
protistrany a **variabilní, konstantní a specifický symbol**.

Modul přidává GPC do průvodce importem výpisů OCA
(`account_statement_import_file`) v edici Community. V edici Enterprise ho do
vlastního importu výpisů Odoo přidává modul
[module:account_statement_import_gpc_ee](module:account_statement_import_gpc_ee)
— viz [níže](#enterprise).

## Co se načte {#format}

Soubor GPC je posloupnost 130znakových záznamů:

| Záznam | Obsah | Výsledek |
|---|---|---|
| `074` | záhlaví výpisu: účet, starý a nový zůstatek se znaménkem, číslo výpisu, datum | jeden bankovní výpis s názvem `GPC <účet>/<číslo>` s počátečním a konečným zůstatkem |
| `075` | transakce: vlastní účet, účet a kód banky protistrany, číslo dokladu, částka v haléřích, účetní kód, VS, KS, SS, název protistrany, měna, datum | jeden řádek výpisu |
| `076`, `078`, `079` | doplňující řádky zprávy | připojí se k popisu předchozího řádku |

Ostatní záznamy se ignorují — banky přidávají vlastní.

Znaménko částky určuje účetní kód: `1` debet, `2` kredit, `4` storno debetu
(peníze se vracejí), `5` storno kreditu (peníze odcházejí).

Na každém řádku výpisu:

- **Popis**: název protistrany (nebo `GPC <číslo dokladu>`), pak `VS:…`,
  `KS:…`, `SS:…` a účet protistrany `číslo/kód banky`.
- **Partner**: hledá se podle čísla účtu protistrany mezi bankovními účty v
  Odoo; název zůstane na řádku.
- **Symboly**: je-li nainstalován modul
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements),
  VS, KS a SS se zapíšou i do vlastních polí symbolů řádku, z nichž je bere
  párování podle variabilního symbolu.
- **Datum**: datum transakce ze záznamu `075`.

Soubor za více dní (jedno `074` za den) dá jeden výpis za každý den. Blok
`074` bez transakcí se přeskočí.

Soubor se dekóduje jako Windows-1250, a pokud to selže, jako Latin-1. Měna se
čte z transakcí; rozpoznávají se CZK, EUR, USD, GBP, PLN, HUF, CHF, DKK, SEK a
NOK.

## Nastavení {#setup}

- Bankovní deník (*Účetnictví → Konfigurace → Účetnictví → Účetní deníky*)
  musí mít vyplněný bankovní účet. Záhlaví GPC nese účet **bez kódu banky** ;
  deník se najde porovnáním předčíslí a čísla s účtem deníku, takže funguje
  IBAN `CZ` / `SK`, `předčíslí-číslo/kód banky` i samotné číslice.
- Měna deníku musí být měnou výpisu.
- Výpis si z banky stáhněte ve formátu GPC (někdy nabízený jako *ABO* nebo
  `.gpc`).

## Import výpisu {#usage}

*Účetnictví → Účetnictví → Import Statement* nebo **Import Statement (OCA)**
na kartě bankovního deníku na přehledu Účetnictví (*Dashboard*) (popisky průvodce OCA jsou v
češtině zatím nepřeložené). Vyberte soubor a stiskněte **Import and View**.

Opakovaný import téhož souboru je bezpečný: každý řádek nese klíč importu
složený z účtu, data, čísla dokladu a částky se znaménkem a již naimportované
řádky se přeskočí. Soubor, který se překrývá s dřívějším, přinese jen nové
řádky.

## Enterprise {#enterprise}

Modul [module:account_statement_import_gpc_ee](module:account_statement_import_gpc_ee)
přidá GPC do importu výpisů Enterprise vedle CAMT, OFX, QIF a CSV: použijte
**Importovat soubor** na kartě bankovního deníku na přehledu Účetnictví (*Dashboard*).
Soubor se rozpozná podle prvního záznamu (`074` nebo `075`); vše popsané výše
platí stejně.

Enterprise porovnává účet ze souboru s deníkem, do kterého se importuje;
modul toto porovnání rozšíří i na předčíslí a číslo, takže deník s účtem
uloženým jako IBAN nebo `předčíslí-číslo/kód banky` své soubory GPC přijme.
Soubor s **více účty** Enterprise odmítne, protože importuje do deníku, ze
kterého byl import spuštěn: stáhněte soubor pro každý účet zvlášť.

## Omezení {#limitations}

- Jen deset výše uvedených měn. Soubor v jiné měně se zastaví hlášením
  *Missing currency code in the bank statement file.*
- GPC nenese kód banky, takže dva účty se stejným předčíslím a číslem ve dvou
  bankách nelze rozlišit; přednost má deník, ze kterého importujete. Účet,
  který číslice ze souboru jen *obsahuje*, se za něj nepovažuje — import se
  zastaví a podobný deník jmenuje.
- Při přechodu účtu ze souborů GPC na bankovní napojení (například
  [API Fio](module:account_statement_fio)) se řádky naimportované z GPC
  nerozpoznají, protože obě cesty používají jiné klíče importu. Přejděte na
  hranici výpisu.
