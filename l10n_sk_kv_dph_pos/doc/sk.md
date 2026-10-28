---
title: SK Kontrolný výkaz DPH — pokladnica Odoo v D.1
summary: Vykazuje predaje každej relácie pokladnice Odoo (Point of Sale) v oddiele D.1 kontrolného výkazu DPH ako obrat z eKasy namiesto D.2.
verified: 19.0.1.0.0
---

## Na čo slúži {#purpose}

Slovenský platiteľ DPH vykazuje obrat evidovaný pokladnicami eKasa v oddiele
**D.1** kontrolného výkazu DPH a v D.2 len to, čo eKasa neevidovala. Predaj
cez pokladnicu Odoo (Point of Sale) je takýto obrat: pokladnica je
*pokladnicou eKasa*, napríklad virtuálnou registračnou pokladnicou Finančnej
správy cez [module:pos_vrp2](module:pos_vrp2).

Odoo účtuje predaje relácie jedným uzatváracím zápisom bez odberateľa, takže
slovenské pravidlá sekcií z [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph) ho
čítali ako dodanie súkromným osobám a vykazovali v **D.2**, ak jeho denník
nebol ručne nastavený na `D.1`. S týmto modulom ide uzatvárací zápis každej
relácie do **D.1**.

## Právny rámec {#legal}

- [Zákon o DPH](law:sk/2004/222), § 78a: kontrolný výkaz.
- Poučenie na vyplnenie kontrolného výkazu, oddiel D.1: údaje uvádza
  platiteľ, „ktorý je povinný evidovať tržby pokladnicou e-kasa klient“, a do
  D.2 patria „len tie dodania tovaru alebo služby, ktoré nezahrnul do D.1“.
- Zákon o evidencii tržieb (zákon č. 384/2025 Z. z., do roku 2025 zákon
  č. 289/2008 Z. z.) ukladá predávajúcemu evidovať každú tržbu na predajnom
  mieste pokladnicou eKasa.

## Ako to funguje {#usage}

Nič sa nenastavuje: modul sa nainštaluje sám, keď je nainštalovaný slovenský
kontrolný výkaz aj Point of Sale.

- **Uzatvárací zápis relácie** sa vykáže v D.1: obrat vrátane DPH a základ a
  daň v základnej a v znížených sadzbách (pozri riadok D.1 v
  [module:l10n_sk_kv_dph](module:l10n_sk_kv_dph#sections)). Vrátenia v
  relácii sú v ňom započítané.
- **Fakturovaná objednávka** z pokladnice je faktúra a zostáva v A.1 (alebo
  v D.2 pri súkromnom odberateľovi); doklad o jej úhrade nie je obrat.
- Denník s vlastným **Prepisom sekcie kontrolného výkazu** si ho ponechá.

Sekcie uložené na už zaúčtovaných zápisoch sa inštaláciou modulu
neprepočítajú; prepočíta ich administrátor, ako opisuje spoločný návod.

## Obmedzenia {#limitations}

- Rozpoznáva sa len uzatvárací zápis relácie. Predaj z pokladnice zaúčtovaný
  inak stále potrebuje denník nastavený na `D.1`.
