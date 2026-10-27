---
title: Import bankovních výpisů — KB BEST
summary: Importuje elektronické výpisy Komerční banky ve formátu BEST (*.OKM / *.KMO) se zůstatky, účty protistrany a symboly VS/KS/SS.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Kanály přímého bankovnictví Komerční banky — MojeBanka Business, Profibanka a
Přímý kanál — exportují elektronické výpisy ve formátu KB **BEST** jako soubory
`*.OKM` nebo `*.KMO`. Modul je importuje přes průvodce importem výpisů OCA
(`account_statement_import_file`), v edici Community i Enterprise. Platby ve
stejném formátu zapisuje modul
[module:account_payment_kb_best](module:account_payment_kb_best).

## Co se načte {#format}

| Záznam | Obsah | Výsledek |
|---|---|---|
| `HO` | záhlaví souboru s označením BEST | podle něj se soubor rozpozná |
| `51` | obratový záznam za účet a den: účet a IBAN, počáteční a konečný zůstatek, číslo výpisu, datum | jeden bankovní výpis `BEST <účet>/<číslo>` se zůstatky |
| `52` | účetní transakce | jeden řádek výpisu |
| `53` | neúčetní položka (splátky úroků a poplatků z úvěru) | přeskočí se — nemění zůstatek |

Na každém řádku:

- **Částka a znaménko** podle účetního kódu: `0` debet, `1` kredit, `2` storno
  debetu, `3` storno kreditu.
- **Popis**: název protistrany, zpráva pro příjemce, `VS:…`, `KS:…`, `SS:…`,
  účet protistrany; chybí-li zpráva, vlastní popis transakce od KB.
- **Reference** (pole *Popis*): váš vlastní popis („popis pro mě“) za stranu,
  na které jste.
- **Účet protistrany**: tuzemský účet a kód banky; u zahraniční platby nebo
  platby SEPA IBAN, který KB uvádí v prvním poli popisu.
- **Partner**: hledá se podle účtu protistrany mezi bankovními účty v Odoo.
- **Symboly**: je-li nainstalován modul
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements),
  i ve vlastních polích symbolů řádku. Specifický symbol `9999999999` je
  pokyn KB ke skrytí jména partnera, ne symbol, a vynechá se.

Soubor může obsahovat více dní a více účtů; každý účet a den je jeden výpis.

## Nastavení {#setup}

- Bankovní deník s účtem u KB (*Účetnictví → Konfigurace → Účetnictví →
  Účetní deníky*) v měně výpisu. Účet může být uložen jako IBAN nebo jako
  `předčíslí-číslo/0100`: modul porovnává kód banky, předčíslí a číslo, ne
  zápis.
- V kanálu KB exportujte výpisy ve formátu BEST.

## Import výpisu {#usage}

*Účetnictví → Účetnictví → Import Statement* nebo **Import Statement (OCA)**
na kartě bankovního deníku na přehledu Účetnictví (*Dashboard*); vyberte
soubor a stiskněte **Import and View** (popisky průvodce OCA jsou v češtině
zatím nepřeložené).

Vlastní identifikátor zaúčtování KB je součástí klíče importu každého řádku,
takže dvojí import téhož souboru nic nepřidá a soubor, který se překrývá s
dřívějším, přinese jen nové řádky.

## Omezení {#limitations}

- Den, který má jen neúčetní položky (`53`), nevytvoří žádný výpis.
- Psáno podle specifikace KB platné od 20. června 2026 a podle vzorových
  souborů KB; starší varianty formátu nebyly vyzkoušeny.
