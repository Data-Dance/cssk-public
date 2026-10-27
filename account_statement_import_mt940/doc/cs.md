---
title: Import bankovních výpisů — MT940 / MultiCash
summary: Importuje bankovní výpisy SWIFT MT940 — soubory *.STA z MultiCash, X-business a Business 24 — se symboly VS/KS/SS, účty protistrany a zůstatky.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

České banky předávají výpisy účetním programům ve formátu **SWIFT MT940**:
MultiCash je zapisuje jako soubory `*.STA` (ve verzi 3.x do složky `MCCWIN`,
ve verzi 4.x do `DATA`) a stejnou strukturu používají X-business a
Business 24. Část SWIFT je všude stejná; pole `:86:` („informace pro majitele
účtu“) ne, a právě v něm jsou variabilní, konstantní a specifický symbol, účet
a název protistrany a zpráva k platbě.

Modul takové soubory importuje přes průvodce importem výpisů OCA
(`account_statement_import_file`), v edici Community i Enterprise. Je to
výpisová polovina MultiCash; platební polovinu řeší modul
[module:account_multicash](module:account_multicash).

## Co se načte {#format}

| Pole | Výsledek |
|---|---|
| `:25:` účet | deník, k němuž výpis patří |
| `:28C:` číslo výpisu | název výpisu `MT940 <účet>/<číslo>` |
| `:60F:` / `:60M:` počáteční zůstatek | počáteční zůstatek výpisu a jeho měna |
| `:61:` transakce | řádek výpisu: částka, znaménko (`C` kredit, `D` debet, `RC`/`RD` storna), datum zaúčtování (jinak datum valuty), typ transakce SWIFT, reference klienta |
| `:86:` podrobnosti | popis, VS/KS/SS, účet a název protistrany |
| `:62F:` / `:62M:` konečný zůstatek | konečný zůstatek výpisu |

**Pole `:86:`.** Banky ho zapisují jako podpole `?NN` a neshodnou se na
číslování — Česká spořitelna dává `KS:` do `?20` a `VS:` do `?21`,
Raiffeisenbank `KS` do `?21` a `VS` do `?22`. Modul proto symbol rozpozná podle
předpony (`VS`, `KS`, `SS`, s dvojtečkou i bez ní, s úvodními nulami i bez
nich), nikdy podle pozice. Protistrana se bere z `?30` (kód banky nebo BIC),
`?31` (účet), `?38` (IBAN) a `?32`/`?33` (název); zpráva z `?00`, `?20`–`?29`
a `?60`–`?63`. Opakující se šum, například číslo výpisu Raiffeisenbank a
nulové poplatky, se vynechá. Pole `:86:` bez podpolí se ponechá jako volný
text a značky typu `VS:` se z něj přesto vyberou.

Na každém řádku výpisu:

- **Popis**: název protistrany, zpráva, `VS:…`, `KS:…`, `SS:…`, účet
  protistrany.
- **Partner**: hledá se podle účtu protistrany mezi bankovními účty v Odoo.
- **Symboly**: je-li nainstalován modul
  [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#bank-statements),
  i ve vlastních polích symbolů řádku.
- Původní text `:61:`/`:86:` zůstane uložen u řádku, reference klienta jde do
  pole *Popis* (*Reference*), typ SWIFT do pole *Typ transakce*.

Jeden soubor může obsahovat více dní a více účtů; každý výpis přistane ve svém
deníku. Výpis rozdělený do více zpráv (počáteční zůstatek `:60M:`, stejné
číslo výpisu, počáteční zůstatek rovný předchozímu konečnému) se spojí do
jednoho.

Soubor se čte jako UTF-8, je-li platným UTF-8, jinak v kódové stránce 852 nebo
Windows-1250 podle toho, která dá více českých písmen.

## Nastavení {#setup}

- Každý účet ze souboru potřebuje bankovní deník s tímto bankovním účtem
  (*Účetnictví → Konfigurace → Účetnictví → Účetní deníky*) v měně výpisu.
- **Účet může být zapsán libovolně.** Česká spořitelna zapisuje `:25:` jako
  `0800/192000145399` (nejprve kód banky), jiné banky jako IBAN. Modul
  porovnává kód banky, předčíslí a číslo, takže deník s účtem uloženým jako
  IBAN nebo jako `19-2000145399/0800` se najde v obou případech.

## Import výpisu {#usage}

*Účetnictví → Účetnictví → Import Statement* nebo **Import Statement (OCA)**
na kartě bankovního deníku na přehledu Účetnictví (*Dashboard*). Vyberte soubor
`.STA` a stiskněte **Import and View**.

Opakovaný import téhož výpisu se odmítne řádek po řádku: klíč importu řádku se
skládá z účtu, čísla výpisu, data valuty, pořadí řádku ve výpisu, částky a
reference banky. Soubor, který se překrývá s dřívějším importem, přinese jen
nové řádky.

## Omezení {#limitations}

- Struktura pole `:86:` byla ověřena podle zveřejněných popisů České
  spořitelny (*MultiCash 3.2*, platí i pro Business 24) a Raiffeisenbank
  (MT940 verze 2–4 pro MultiCash a X-business). MT940 jiných bank se čte přes
  stejná pole SWIFT, jejich `:86:` však nebylo porovnáno se zveřejněnou
  strukturou; u volného textu v `:86:` je popisem text tak, jak přišel.
- Párování deníku podle kódu banky, předčíslí a čísla funguje pro české a
  slovenské účty. Zahraniční účet se musí shodovat s účtem deníku tak, jak je
  zapsán.
- Klíč importu obsahuje pořadí řádku ve výpisu. Vydá-li banka výpis znovu s
  jinak seřazenými řádky, řádky se mohou naimportovat dvakrát.
- MT940 má dvoumístné roky; data se čtou v rozsahu 1980–2079.
