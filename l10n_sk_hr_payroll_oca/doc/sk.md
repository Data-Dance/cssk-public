---
title: Slovenské mzdy (OCA)
summary: Slovenská mesačná výplatná páska pre aplikáciu OCA payroll v Odoo Community — úplná mzdová štruktúra pre pracovný pomer a tri dohody.
verified: 19.0.1.20.1
family: l10n_sk_hr_payroll_base#engines
---

Úplná slovenská mzdová štruktúra pre aplikáciu OCA `payroll`: štyri štruktúry, jedna na každú formu zamestnania, so spoločnými pravidlami — sociálne a zdravotné poistenie, základ dane, nezdaniteľná časť základu dane na daňovníka, progresívna daň z príjmu, daňový bonus na dieťa, náhrada mzdy za dovolenku a pri prekážkach v sume priemerného zárobku, náhrada príjmu pri PN, exekučné zrážky a stravné. Dodáva aj datované parametre, z ktorých pravidlá čítajú, slovenské typy voľna so *Slovenským mzdovým kódom* a plánmi nárokov a ročné zúčtovanie dane. Slovenské polia sú na karte zamestnanca v záložke mzdy a na šablónach zmlúv; parametre pravidiel sú v *Mzdy → Konfigurácia → Parametre pravidiel*.

Inštaluje sa zámerne, vyžaduje modul OCA `payroll` a funguje v Odoo Community. Na zaúčtovanie do hlavnej knihy pridajte účtovný mostík pre OCA, na mzdové zvýhodnenia skupinu modulov príplatkov.

## Podklady ročného zúčtovania

Preberajú sa potvrdené pásky (`done`) príslušnej firmy a zamestnanca podľa
konca mzdového obdobia vo zvolenom roku. Rozpracované, čakajúce a zrušené
pásky aj zvolená páska vysporiadania sa vynechajú. Toto zjednotenie výberu
s výkazmi samo nepreukazuje úhradu, zákonné priradenie príjmu do daňového
roka ani splnenie podmienok RZD. Rozšírenie uchovávajúce nahradené finančné
verzie musí navyše vynechať nahradené originály.
