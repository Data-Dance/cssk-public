---
title: Slovenské mzdy (OCA)
summary: Slovenská mesačná výplatná páska pre aplikáciu OCA payroll v Odoo Community — úplná mzdová štruktúra pre pracovný pomer a tri dohody.
verified: 19.0.1.21.0
family: l10n_sk_hr_payroll_base#engines
---

Úplná slovenská mzdová štruktúra pre aplikáciu OCA `payroll`: štyri štruktúry, jedna na každú formu zamestnania, so spoločnými pravidlami — sociálne a zdravotné poistenie, základ dane, nezdaniteľná časť základu dane na daňovníka, progresívna daň z príjmu, daňový bonus na dieťa, náhrada mzdy za dovolenku a pri prekážkach v sume priemerného zárobku, náhrada príjmu pri PN, exekučné zrážky a stravné. Dodáva aj datované parametre, z ktorých pravidlá čítajú, slovenské typy voľna so *Slovenským mzdovým kódom* a plánmi nárokov a ročné zúčtovanie dane. Slovenské polia sú na karte zamestnanca v záložke mzdy a na šablónach zmlúv; parametre pravidiel sú v *Mzdy → Konfigurácia → Parametre pravidiel*.

Inštaluje sa zámerne, vyžaduje modul OCA `payroll` a funguje v Odoo Community. Na zaúčtovanie do hlavnej knihy pridajte účtovný mostík pre OCA, na mzdové zvýhodnenia skupinu modulov príplatkov.

Dôchodok poberaný k 1. januáru sa zohľadní iba v ročnom zúčtovaní dane. Jeho ročnú sumu vrátane 13. dôchodku zadajte do poľa *Dôchodok k 1. januáru (ročne)* na verzii zmluvy; ročné zúčtovanie ju prevezme z verzie platnej k 1. januáru a o túto sumu zníži nezdaniteľnú časť základu dane na daňovníka, a ak je dôchodok vyšší, neuplatní ju vôbec ([§ 11 ods. 6](law:sk/2003/595#paragraf-11)). Mesačné preddavky si podľa [§ 35 ods. 1](law:sk/2003/595#paragraf-35) ponechávajú celú nezdaniteľnú časť.
