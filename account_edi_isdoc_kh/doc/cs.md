---
title: ISDOC — tuzemský režim přenesení daňové povinnosti
summary: Faktury v tuzemském režimu přenesení daňové povinnosti (§ 92a ZDPH) odcházejí v ISDOC jako takové, s kódem předmětu plnění, který vykazuje kontrolní hlášení.
verified: 19.0.1.0.0
family: account_edi_isdoc#reverse-charge
---

## Co dělá {#purpose}

V tuzemském režimu přenesení daňové povinnosti přiznává daň odběratel, ne vy
([§ 92a ZDPH](law:cz/2004/235#p92a)), a oba plnění vykazujete v kontrolním
hlášení s **kódem předmětu plnění** — vy v oddílu A.1, odběratel v B.1.
ISDOC 6.0.2 má pro to vlastní prvky, které samotný
[module:account_edi_isdoc](module:account_edi_isdoc) nezapisuje. S tímto
doplňkem dostane každý exportovaný řádek vydané faktury nebo dobropisu
v režimu přenesení:

| ISDOC | Hodnota |
|---|---|
| ClassifiedTaxCategory / LocalReverseCharge / LocalReverseChargeCode | kód předmětu plnění, např. `4` stavební a montážní práce |
| ClassifiedTaxCategory / VATApplicable | `true` — plnění je zdanitelné, daň jen přiznává odběratel |
| TaxSubTotal / TaxCategory / LocalReverseChargeFlag | `true` na vlastním řádku rekapitulace DPH, odděleném od osvobozených plnění, která jsou rovněž v 0 % |

Sazba a daň zůstávají nulové: daňový doklad v režimu přenesení je uvádět
nemusí ([§ 29 odst. 3 písm. e)](law:cz/2004/235)) a daň si dopočte
odběratel. *VATApplicable* dokladu je `true`, i když jsou v režimu přenesení
všechny řádky.

## Které řádky {#lines}

Tytéž řádky, které kontrolní hlášení
([module:l10n_cz_kh](module:l10n_cz_kh)) zařadí do oddílu A.1: řádek s daní
označenou jako přenesení, nebo s prodejní daní *0% RC* z účtové osnovy
(řádek 25 přiznání).

Kód předmětu plnění je rovněž ten z kontrolního hlášení: **Kód předmětu
plnění (§92a)** produktu, jinak daně v režimu přenesení (daně označené
jako přenesení). Zapisuje se podle číselníku kontrolního hlášení. Vlastní
číselník ISDOC je starší a povolenky na emise čísluje `2`; kontrolní hlášení
je čísluje `11` a zapisuje se `11`, protože odběratel kód uvádí v B.1.

## Chybí-li kód {#missing-code}

Řádek v režimu přenesení bez kódu předmětu plnění nelze exportovat: dialog
*Odeslat* ohlásí *„Tyto řádky v režimu přenesení daňové povinnosti nemají
kód předmětu plnění KH“*
a řádky vyjmenuje. Doplňte kód na produkt (nebo na daň v režimu přenesení)
a odešlete znovu. Kontrolní hlášení takový řádek odmítne také.

Instaluje se sám, jsou-li nainstalovány
[module:account_edi_isdoc](module:account_edi_isdoc) i
[module:l10n_cz_kh](module:l10n_cz_kh).

## Omezení {#limitations}

- Jen vydané faktury a dobropisy. Zálohová faktura z prodejní objednávky
  ([module:account_edi_isdoc_sale](module:account_edi_isdoc_sale)) není
  daňový doklad a označení přenesení nenese.
- *LocalReverseChargeQuantity* (množství v měrné jednotce komodity) se
  nezapisuje; kontrolní hlášení ho nevykazuje.
- Při importu nenajde řádek v režimu přenesení v 0 % — tak, jak ho zapisuje
  tento doplněk — nákupní daň s přenesením v této sazbě, takže zůstane bez
  daně a historie faktury to uvede ([příjem](module:account_edi_isdoc#import)).
  Sazbu zvolte na faktuře.
