---
title: Saldo otevřených záloh (XLSX)
summary: Tabulka vystavených a přijatých zálohových faktur s tím, co bylo zaplaceno, pokryto daňovými doklady, odečteno a co ještě zůstává otevřené.
verified: 19.0.1.0.2
---

## K čemu slouží {#purpose}

Zálohové faktury se neúčtují, takže je žádná účetní sestava neukáže. Tento
sešit ano. Obsahuje každou zálohu vystavenou v modulu
[module:sale_order_advance_invoice](module:sale_order_advance_invoice)
a přijatou v modulu
[module:purchase_order_advance_invoice](module:purchase_order_advance_invoice),
s tím, kolik je na ní zaplaceno, kolik pokrývají daňové doklady a kolik už
odečetly konečné faktury. Při měsíční nebo roční uzávěrce v něm zkontrolujete,
které zálohy jsou ještě otevřené, ke kterým chybí daňový doklad a které nebyly
nikdy zaplaceny.

## Vytvoření {#usage}

*Účetnictví → Výkazy → Saldo otevřených záloh (XLSX)*:

| Pole | Význam |
|---|---|
| Společnost | společnost, za kterou se sestava dělá (zobrazí se při více společnostech) |
| I vyrovnané zálohy | uvede i zálohy, u kterých není nic otevřené, nic nečeká a nic není nezaplaceno |

**Exportovat XLSX** stáhne soubor `Advances Saldo - <společnost>.xlsx`.

Ve výchozím stavu se záloha uvede, platí-li **kterákoli** z podmínek: její
otevřená částka není nulová, čeká na daňový doklad, nebo není zaplacena
nebo je zaplacena jen zčásti. Zrušené zálohy se neuvádějí nikdy.

## Obsah sešitu {#output}

Dva listy, **Vystavené zálohy** a **Přijaté zálohy**, se stejnými sloupci,
řádek za každou zálohu, seřazené podle data a čísla. Názvy listů a sloupců
jsou v jazyce uživatele, který sestavu exportuje:

| Sloupec | Význam |
|---|---|
| Číslo | `ADV…` nebo `PADV…` |
| Partner, Datum, Měna | zákazník nebo dodavatel, datum zálohy, její měna |
| Celkem | částka zálohové faktury včetně DPH |
| Zaplaceno | u vystavených přijaté platby, u přijatých součet propojených plateb |
| Datum úhrady | datum poslední platby |
| Pokryto daňovými doklady | částka **zaúčtovaných** daňových dokladů včetně DPH |
| Odečteno | částka včetně DPH odečtená na **zaúčtovaných** konečných fakturách |
| Otevřeno (zaplaceno − odečteno) | zaplaceno a dosud neodečteno |
| Stav platby, Účetní stav | jako na záloze |

Na obou listech se za odečtené považují jen zaúčtované faktury. U
vystavených záloh se počítají odpočty na vyúčtování nadřazené objednávky
i odpočty zálohy bez objednávky přes *Přepojit zálohové faktury*.
*Zaplaceno* u vystavených záloh zahrnuje jen dokončené platby, ne platby
kartou, které jsou jen autorizované.

Všechny částky jsou v měně zálohy, bez přepočtu a bez součtů.

## Omezení {#limitations}

- Sestava ukazuje stav v okamžiku exportu. Nemá datum „k“, takže stav ke
  konkrétnímu minulému dni nezopakuje.
