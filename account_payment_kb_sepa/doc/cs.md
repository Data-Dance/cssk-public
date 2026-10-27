---
title: KB XML SEPA převod
summary: Upraví soubor SEPA převodu z OCA (pain.001.001.03) podle specifikace XML Komerční banky, je-li příkaz placen z účtu u KB.
verified: 19.0.1.0.0
---

## K čemu slouží {#purpose}

Komerční banka přijímá platby SEPA jako XML ISO 20022 **pain.001.001.03**
popsané v dokumentu *Klientský formát XML SEPA CT v KB* (platný od 20. června
2026). Modul OCA `account_banking_sepa_credit_transfer` takový soubor už
zapisuje. Specifikace KB se od výstupu OCA liší ve dvou podrobnostech a
soubor, který je nerespektuje, může být odmítnut. Tento modul mění právě tyto
dvě věci, a to jen u platebních příkazů placených **z účtu u KB** ve verzi
pain.001.001.03. Příkazy ze všech ostatních bank zůstanou tak, jak je zapíše
OCA.

## Co se u příkazu KB mění {#changes}

| | Výstup OCA | Pro KB |
|---|---|---|
| Poštovní adresa plátce a příjemce | země a volné řádky adresy (`AdrLine`) | strukturovaně: ulice (`StrtNm`), číslo domu (`BldgNb`), PSČ (`PstCd`), město (`TwnNm`), země (`Ctry`) |
| Chybí město nebo země | řádky adresy se přesto zapíšou | **žádná adresa** — KB vyžaduje město a zemi, jakmile je uveden kterýkoli prvek adresy, a pro SEPA je adresa nepovinná |
| Znaky | diakritika zůstane, pokud na platební metodě není zaškrtnuto *Convert to ASCII* | vždy převedeno na čisté ASCII — KB přijímá data SEPA jen bez diakritiky |

S modulem `base_address_extended` jdou název ulice a číslo domu do vlastních
prvků; jinak se celá ulice zapíše do `StrtNm`.

## Nastavení {#setup}

1. Bankovní deník musí mít **účet u KB** (kód banky `0100`) jako IBAN `CZ`
   nebo `předčíslí-číslo/0100`.
2. Použijte platební metodu OCA **SEPA Credit Transfer to suppliers** s
   *PAIN Version* `pain.001.001.03` (výchozí) ve způsobu platby s deníkem KB
   (*Účetnictví → Konfigurace → Účetnictví → Payment Modes*).
3. Nic dalšího: úprava se u takových příkazů zapne sama.

Pak plaťte jako u každého platebního příkazu SEPA — *Účetnictví → Dodavatelé
→ Payment Orders*, **Confirm Payments**, **Generate Payment File** — a XML
nahrajte do MojeBanky Business, Profibanky nebo Přímého kanálu.

## Omezení {#limitations}

- **Jen SEPA.** XML u KB nese platby v EUR ve schématu SEPA. Platby v jiných
  měnách nebo s poplatky `OUR`/`BEN` jdou přes formát BEST:
  [module:account_payment_kb_best](module:account_payment_kb_best), metoda
  *KB BEST (foreign / SEPA transfer)*.
- Jiné verze pain (například pain.001.001.09) se nemění.
- Pravidlo KB, že identifikace a reference nesmějí začínat ani končit `/` ani
  obsahovat `//`, se nevynucuje. Identifikátor end-to-end, který zapisuje OCA,
  ho splňuje; informace pro příjemce, které napíšete sami, projdou beze změny.
