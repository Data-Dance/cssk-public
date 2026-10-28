---
title: ISDOC — tuzemské prenesenie daňovej povinnosti (CZ)
summary: České faktúry v tuzemskom prenesení daňovej povinnosti (§ 92a ZDPH) odchádzajú v ISDOC ako také, s kódom predmetu plnenia, ktorý vykazuje kontrolné hlásenie.
verified: 19.0.1.0.0
family: account_edi_isdoc#reverse-charge
---

## Čo robí {#purpose}

V českom tuzemskom prenesení daňovej povinnosti priznáva daň odberateľ, nie
vy ([§ 92a ZDPH](law:cz/2004/235#p92a)), a obaja plnenie vykazujete
v kontrolnom hlásení s **kódom predmetu plnenia** (*kód předmětu plnění*) —
vy v oddiele A.1, odberateľ v B.1. ISDOC 6.0.2 má na to vlastné prvky, ktoré
samotný [module:account_edi_isdoc](module:account_edi_isdoc) nezapisuje.
S týmto doplnkom dostane každý exportovaný riadok vydanej faktúry alebo
dobropisu v prenesení:

| ISDOC | Hodnota |
|---|---|
| ClassifiedTaxCategory / LocalReverseCharge / LocalReverseChargeCode | kód predmetu plnenia, napr. `4` stavebné a montážne práce |
| ClassifiedTaxCategory / VATApplicable | `true` — plnenie je zdaniteľné, daň priznáva len odberateľ |
| TaxSubTotal / TaxCategory / LocalReverseChargeFlag | `true` na vlastnom riadku rekapitulácie DPH, oddelenom od oslobodených plnení, ktoré sú tiež v 0 % |

Sadzba a daň zostávajú nulové: doklad v prenesení ich uvádzať nemusí
([§ 29 odst. 3 písm. e) ZDPH](law:cz/2004/235)) a daň si dopočíta
odberateľ. *VATApplicable* dokladu je `true`, aj keď sú v prenesení všetky
riadky.

## Ktoré riadky {#lines}

Tie isté riadky, ktoré kontrolné hlásenie
([module:l10n_cz_kh](module:l10n_cz_kh)) zaradí do oddielu A.1: riadok s daňou
označenou ako prenesenie, alebo s predajnou daňou *0% RC* z účtovej osnovy
(riadok 25 priznania).

Kód predmetu plnenia je tiež ten z kontrolného hlásenia: **KH commodity code
(§92a)** produktu, inak dane s prenesením (dane označenej ako
prenesenie). Zapisuje sa podľa číselníka kontrolného hlásenia. Vlastný
číselník ISDOC je starší a povolenky na emisie čísluje `2`; kontrolné
hlásenie ich čísluje `11` a zapisuje sa `11`, lebo odberateľ kód uvádza v B.1.

## Ak kód chýba {#missing-code}

Riadok v prenesení bez kódu predmetu plnenia nemožno exportovať: dialóg
*Odoslať* ohlási *„Tieto riadky v prenesení daňovej povinnosti nemajú kód
predmetu plnenia KH“*
a riadky vymenuje. Doplňte kód na produkt (alebo na daň s prenesením)
a odošlite znova. Kontrolné hlásenie taký riadok odmietne tiež.

Nainštaluje sa sám, keď sú nainštalované
[module:account_edi_isdoc](module:account_edi_isdoc) aj
[module:l10n_cz_kh](module:l10n_cz_kh).

## Obmedzenia {#limitations}

- Len vydané faktúry a dobropisy. Zálohová faktúra z predajnej objednávky
  ([module:account_edi_isdoc_sale](module:account_edi_isdoc_sale)) nie je
  daňový doklad a označenie prenesenia nenesie.
- *LocalReverseChargeQuantity* (množstvo v mernej jednotke komodity) sa
  nezapisuje; kontrolné hlásenie ho nevykazuje.
- Pri importe nenájde riadok v prenesení v 0 % — tak, ako ho zapisuje tento
  doplnok — nákupnú daň s prenesením v tejto sadzbe, takže zostane bez dane
  a história faktúry to uvedie ([prijímanie](module:account_edi_isdoc#import)).
  Sadzbu zvoľte na faktúre.
