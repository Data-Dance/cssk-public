---
title: Platební soubory KB BEST
summary: Tuzemské úhrady, inkasa a zahraniční platby / platby SEPA z účtu u Komerční banky exportované ve formátu BEST z platebního příkazu OCA.
verified: 19.0.1.1.0
---

## K čemu slouží {#purpose}

**BEST** je vlastní klientský formát Komerční banky s pevnou délkou záznamů
pro její kanály přímého bankovnictví — **MojeBanka Business**, **Profibanka**
a **Přímý kanál**. Modul zapisuje platební soubory BEST z **platebního
příkazu** OCA (`account_payment_order`), takže dávku faktur z účtu u KB
uhradíte nahráním jednoho souboru. Funguje v edici Community i Enterprise.

Specifikací je *Klientský formát BEST podporovaný v KB* platný od 20. června
2026.

Výpisy ve stejném formátu importuje modul
[module:account_statement_import_kb_best](module:account_statement_import_kb_best).

## Platební metody {#methods}

Názvy metod a popisky platebních příkazů OCA jsou v této verzi anglicky.

| Platební metoda | Platební příkaz | Záznam BEST | Soubor |
|---|---|---|---|
| KB BEST (domestic transfer) | odchozí (*Payment Orders*) | `01`, tuzemská úhrada | `BEST-DP-<deník>-<datum a čas>.ikm` |
| KB BEST (domestic direct debit / inkaso) | příchozí (*Debit Orders*) | `01` s kódem operace inkaso | `BEST-DP-….ikm` |
| KB BEST (foreign / SEPA transfer) | odchozí | `02` se strukturovanou adresou `03` | `BEST-ZP-<deník>-<datum a čas>.ikm` |

Soubory jsou ve Windows-1250 s konci řádků CR LF; tuzemské záznamy zachovávají
českou diakritiku, zahraniční používají jen znakovou sadu SWIFT.

## Nastavení {#setup}

1. **Bankovní deník** (*Účetnictví → Konfigurace → Účetnictví → Účetní
   deníky*) musí mít **účet u KB** — kód banky `0100` — jako IBAN `CZ` nebo
   `předčíslí-číslo/0100`. Jakýkoli jiný účet se odmítne. Za měnu účtu u KB se
   považuje měna deníku (nemá-li deník žádnou, měna společnosti).
2. **Způsob platby** pro každou používanou metodu (*Účetnictví → Konfigurace →
   Účetnictví → Payment Modes*) s deníkem KB.
3. **Partneři**: bankovní účet u každého, komu platíte. U zahraniční platby,
   která není SEPA, i ulici, město a zemi partnera a BIC jeho banky (nebo název,
   město a zemi banky).
4. Doporučujeme [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols),
   aby se symboly faktur dostaly na řádky platebního příkazu samy (viz
   [module:account_abo](module:account_abo#setup)).

## Vytvoření platebního souboru {#usage}

1. *Účetnictví → Dodavatelé → Payment Orders* (u inkasa *Zákazníci → Debit
   Orders*), **Nové**, zvolte způsob platby KB BEST, **Create Payment Lines
   from Journal Items**.
2. Zkontrolujte na řádcích variabilní, konstantní a specifický symbol
   (*Variable Symbol*, *Constant Symbol*, *Specific Symbol*); prázdný se vezme
   ze značky `VS:` / `KS:` / `SS:` v poli *Communication*.
3. **Confirm Payments**, **Generate Payment File**.
4. Nahrajte soubor `.ikm` do MojeBanky Business, Profibanky nebo Přímého
   kanálu, autorizujte ho tam a příkaz označte tlačítkem **File Successfully
   Uploaded**.

## Pravidla, která soubor dodržuje {#rules}

Jsou to pravidla KB; modul je uplatní dřív než banka a zastaví se s hlášením,
které platbu jmenuje:

**Každá platba**

- částka musí být kladná;
- datum splatnosti v minulosti se posune na dnešek (minulé banka odmítne);
- každá platba dostane pořadové číslo odvozené z jejího řádku platebního
  příkazu, protože KB vyžaduje, aby bylo jedinečné pro celý den napříč všemi
  soubory, ne jen v rámci jednoho souboru.

**Tuzemská (záznam 01)**

- účet příjemce musí být český (IBAN `CZ…` nebo `předčíslí-číslo/kód banky`);
- platba v jiné měně, než je měna účtu u KB, se odešle s příznakem konverze;
  tuzemská platba v jiné měně než CZK smí jít jen na **jiný účet u KB** — do
  jiné banky musí být v CZK, nebo se odešle jako zahraniční;
- inkaso z jiné banky než KB musí být v CZK;
- konstantní symboly, které KB v dávce odmítá, se odmítnou i zde: `???5`
  (opravné zúčtování), `??51` (exekuce), `0006` a `0007`;
- text z pole *Communication* se stane až čtyřmi řádky po 35 znacích zprávy
  pro příjemce a jeho prvních 30 znaků vaším vlastním popisem;
- vlastní VS a SS se posílají prázdné: banka je stejně nahradí symboly
  příjemce.

**Zahraniční (záznam 02)**

- platba jde jako **SEPA**, je-li v EUR, na IBAN v zemi SEPA a se sdílenými
  poplatky; vše ostatní je standardní zahraniční platba;
- do EHP jsou povoleny jen **sdílené poplatky (SHA)**;
- platba v EUR do EHP vyžaduje IBAN příjemce;
- platba mimo SEPA vyžaduje jméno, ulici, město a zemi příjemce a BIC jeho
  banky nebo její název, město a zemi;
- VS a KS se zapíšou do informace pro příjemce jako `/VS/…` a `/KS/…`, odkud
  je KB načte zpět do historie transakcí;
- strukturovaná adresa `03` se přidá, má-li partner vyplněné město a zemi.

## Společný modul BEST {#format}

Struktury BEST — oba platební záznamy i výpis — jsou v modulu
[module:account_kb_best_base](module:account_kb_best_base), na kterém stojí
tento modul i
[module:account_statement_import_kb_best](module:account_statement_import_kb_best).
Vlastní obrazovku nemá.

## Omezení {#limitations}

- Jen z účtu u KB; je to vlastní formát KB.
- Jen platební příkazy Community — varianta pro hromadné platby Enterprise
  tohoto modulu neexistuje.
- Prioritu a poplatky nastavíte na každém řádku příkazu: **Priority**
  (*Urgent* je expresní zpracování KB) a **Charge Bearer** (*Shared*, *Payer* =
  `OUR`, *Beneficiary* = `BEN`). Výchozí je běžná priorita a sdílené poplatky;
  do EHP je přípustné jen *Shared* (viz výše).
- Příkaz se zastaví u první platby, která porušuje pravidlo; opravte ji a
  generujte znovu.
- Formát XML pro platby SEPA u KB řeší samostatný modul
  [module:account_payment_kb_sepa](module:account_payment_kb_sepa).
