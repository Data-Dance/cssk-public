---
title: Saldo otvorených preddavkov (XLSX)
summary: Tabuľka vystavených a prijatých zálohových faktúr s tým, čo bolo uhradené, pokryté faktúrami k platbe, odpočítané a čo ešte ostáva otvorené.
verified: 19.0.1.0.2
---

## Na čo slúži {#purpose}

Zálohové faktúry sa neúčtujú, takže ich žiadna účtovná zostava neukáže. Tento
zošit áno. Obsahuje každý preddavok vystavený v module
[module:sale_order_advance_invoice](module:sale_order_advance_invoice) a
prijatý v module
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice),
s tým, koľko je na ňom uhradené, koľko pokrývajú faktúry k platbe a koľko už
odpočítali konečné faktúry. Pri mesačnej alebo ročnej uzávierke v ňom
skontrolujete, ktoré preddavky sú ešte otvorené, ku ktorým chýba faktúra k
platbe a ktoré neboli nikdy uhradené.

## Vytvorenie {#usage}

*Účtovníctvo → Výkazy → Saldo otvorených preddavkov (XLSX)*:

| Pole | Význam |
|---|---|
| Spoločnosť | spoločnosť, za ktorú sa zostava robí (zobrazí sa pri viacerých spoločnostiach) |
| Aj vyrovnané preddavky | uvedie aj preddavky, pri ktorých nie je nič otvorené, nič nečaká a nič nie je neuhradené |

**Exportovať XLSX** stiahne súbor `Advances Saldo - <spoločnosť>.xlsx`.

Predvolene sa preddavok uvedie, ak platí **ktorákoľvek** z podmienok: jeho
otvorená suma nie je nulová, čaká na faktúru k platbe, alebo nie je
uhradený alebo je uhradený len sčasti. Zrušené preddavky sa neuvádzajú
nikdy.

## Obsah zošita {#output}

Dva hárky, **Vystavené preddavky** a **Prijaté preddavky**, s rovnakými
stĺpcami, riadok za každý preddavok, zoradené podľa dátumu a čísla. Názvy
hárkov a stĺpcov sú v jazyku používateľa, ktorý zostavu exportuje:

| Stĺpec | Význam |
|---|---|
| Číslo | `ADV…` alebo `PADV…` |
| Partner, Dátum, Mena | zákazník alebo dodávateľ, dátum preddavku, jeho mena |
| Celkom | suma zálohovej faktúry s DPH |
| Uhradené | pri vystavených prijaté platby, pri prijatých súčet prepojených platieb |
| Dátum úhrady | dátum poslednej platby |
| Pokryté faktúrami k platbe | suma **zaúčtovaných** faktúr k platbe s DPH |
| Odpočítané | suma s DPH odpočítaná na **zaúčtovaných** konečných faktúrach |
| Otvorené (uhradené − odpočítané) | uhradené a zatiaľ neodpočítané |
| Stav úhrady, Stav zaúčtovania | ako na preddavku |

Na oboch hárkoch sa za odpočítané považujú len zaúčtované faktúry.
Pri vystavených preddavkoch sa počítajú odpočty na vyúčtovaní nadradenej
objednávky aj odpočty preddavku bez objednávky cez *Prepojiť zálohové
faktúry*. *Uhradené* pri vystavených preddavkoch zahŕňa len dokončené platby,
nie platby kartou, ktoré sú len autorizované.

Všetky sumy sú v mene preddavku, bez prepočtu a bez súčtov.

## Obmedzenia {#limitations}

- Zostava ukazuje stav v okamihu exportu. Nemá dátum „k“, takže stav ku
  konkrétnemu minulému dňu nezopakuje.
