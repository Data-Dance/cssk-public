---
title: Slovenské mzdy (OCA)
summary: Slovenská mesačná výplatná páska pre aplikáciu OCA payroll v Odoo Community — úplná mzdová štruktúra pre pracovný pomer a tri dohody.
verified: 19.0.1.24.0
family: l10n_sk_hr_payroll_base#engines
---

Úplná slovenská mzdová štruktúra pre aplikáciu OCA `payroll`: štyri štruktúry, jedna na každú formu zamestnania, so spoločnými pravidlami — sociálne a zdravotné poistenie, základ dane, nezdaniteľná časť základu dane na daňovníka, progresívna daň z príjmu, daňový bonus na dieťa, náhrada mzdy za dovolenku a pri prekážkach v sume priemerného zárobku, náhrada príjmu pri PN, exekučné zrážky a stravné. Dodáva aj datované parametre, z ktorých pravidlá čítajú, slovenské typy voľna so *Slovenským mzdovým kódom* a plánmi nárokov a ročné zúčtovanie dane. Slovenské polia sú na karte zamestnanca v záložke mzdy a na šablónach zmlúv; parametre pravidiel sú v *Mzdy → Konfigurácia → Parametre pravidiel*.

Inštaluje sa zámerne, vyžaduje modul OCA `payroll` a funguje v Odoo Community. Na zaúčtovanie do hlavnej knihy pridajte účtovný mostík pre OCA, na mzdové zvýhodnenia skupinu modulov príplatkov.

Dôchodok poberaný k 1. januáru sa zohľadní iba v ročnom zúčtovaní dane. Jeho ročnú sumu vrátane 13. dôchodku zadajte do poľa *Dôchodok k 1. januáru (ročne)* na verzii zmluvy; ročné zúčtovanie ju prevezme z verzie platnej k 1. januáru a o túto sumu zníži nezdaniteľnú časť základu dane na daňovníka, a ak je dôchodok vyšší, neuplatní ju vôbec ([§ 11 ods. 6](law:sk/2003/595#paragraf-11)). Mesačné preddavky si podľa [§ 35 ods. 1](law:sk/2003/595#paragraf-35) ponechávajú celú nezdaniteľnú časť.

## Podklady ročného zúčtovania

Preberajú sa potvrdené pásky (`done`) príslušnej firmy a zamestnanca podľa
konca mzdového obdobia vo zvolenom roku. Rozpracované, čakajúce a zrušené
pásky aj zvolená páska vysporiadania sa vynechajú. Toto zjednotenie výberu
s výkazmi samo nepreukazuje úhradu, zákonné priradenie príjmu do daňového
roka ani splnenie podmienok RZD. Rozšírenie uchovávajúce nahradené finančné
verzie musí navyše vynechať nahradené originály.
## Podklady priemerného zárobku {#average-sources}

Skutočný priemerný hodinový zárobok z rozhodujúceho štvrťroka sa použije po
odpracovaní aspoň **21 dní alebo 168 hodín**. Krátke pracovné dni pri kratšom
úväzku sa počítajú ako dni; nerozhodujú iba hodiny. Pri nesplnení oboch hraníc
zostáva existujúci výpočet pravdepodobného zárobku. Započítajú sa iba potvrdené
pásky rovnakej firmy a začiatku pracovného vzťahu. Zmena mzdovej verzie počas
vzťahu históriu zachová, nový nástup nepreberá priemer predošlého vzťahu.
Súbežné vzťahy používa natívny HR model na samostatných kartách zamestnanca.

Natívne dobropisové pásky odčítajú mzdu aj odpracovaný čas. Po storne a náhrade
preto zostanú správne sumy a čas náhradnej pásky. Potvrdenie mzdy nepreukazuje
bankovú úhradu.

Predvolená mzda pre priemer zostáva GROSS mínus existujúce kódy náhrad mzdy.
Rozšírenia môžu spresniť `_l10n_sk_average_counted_wage`, vybrať účinné podklady
cez `_l10n_sk_average_payslips` a doplniť čas cez `_l10n_sk_average_worked_time`.
Daňový a odvodový GROSS sám neurčuje pracovnoprávne zaradenie benefitu.
Táto oprava ešte neimplementuje rozdelenie odmien za obdobie dlhšie než štvrťrok
podľa § 134 ods. 6, všetky stupne minimálnych nárokov ani osobitný overovaný
vstup pravdepodobnej mzdy.

Zdroj: [Zákonník práce § 134](https://static.slov-lex.sk/static/SK/ZZ/2001/311/20261202.html),
vrátane odsekov 1–7, overené v publikovanom znení od 2. decembra 2026.
Pri skutočnom mzdovom období preveriť ďalšie novelizácie.
