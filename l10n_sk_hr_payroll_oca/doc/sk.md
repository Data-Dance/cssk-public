---
title: Slovenské mzdy (OCA)
summary: Slovenská mesačná výplatná páska pre aplikáciu OCA payroll v Odoo Community — úplná mzdová štruktúra pre pracovný pomer a tri dohody.
verified: 19.0.1.22.0
family: l10n_sk_hr_payroll_base#engines
---

Úplná slovenská mzdová štruktúra pre aplikáciu OCA `payroll`: štyri štruktúry, jedna na každú formu zamestnania, so spoločnými pravidlami — sociálne a zdravotné poistenie, základ dane, nezdaniteľná časť základu dane na daňovníka, progresívna daň z príjmu, daňový bonus na dieťa, náhrada mzdy za dovolenku a pri prekážkach v sume priemerného zárobku, náhrada príjmu pri PN, exekučné zrážky a stravné. Dodáva aj datované parametre, z ktorých pravidlá čítajú, slovenské typy voľna so *Slovenským mzdovým kódom* a plánmi nárokov a ročné zúčtovanie dane. Slovenské polia sú na karte zamestnanca v záložke mzdy a na šablónach zmlúv; parametre pravidiel sú v *Mzdy → Konfigurácia → Parametre pravidiel*.

Inštaluje sa zámerne, vyžaduje modul OCA `payroll` a funguje v Odoo Community. Na zaúčtovanie do hlavnej knihy pridajte účtovný mostík pre OCA, na mzdové zvýhodnenia skupinu modulov príplatkov.

Daňovo relevantný dôchodok poberaný k 1. januáru ovplyvňuje aj mesačný nárok na NČZD. Pole *Poberá daňovo relevantný dôchodok* zaznamenajte na natívnej verzii účinnej od priznania dôchodku podľa uchovaného vyhlásenia daňovníka. Mesačný výpočet číta verziu platnú k 1. januáru svojho roka. Januárový dôchodca nemá mesačnú NČZD ani pri podpísanom vyhlásení a nízkom dôchodku. Priznanie v máji 2026 zachová mesačnú NČZD za rok 2026 a od januára 2027 ju odníme bez úpravy májovej verzie či zablokovania prepočtu decembra 2026. Samotný invalidný, vdovský alebo sirotský dôchodok príznak nenastavuje. Relevantný poistný dôchodok bez príznaku na januárovej verzii zastaví mesačné uplatnenie zrozumiteľnou správou pred pravidlami. Ak dôchodcovi januárová verzia chýba, najskôr zaznamenajte historický daňový údaj. Zákonné parametre a pásma sa nemenia.

Ročný rozdiel pri nízkom dôchodku sa uplatňuje v RZD alebo osobnom priznaní. Ročnú sumu vrátane 13. dôchodku overte pre každé RZD. Pole *Dôchodok k 1. januáru (ročne)* poskytne predvolenú sumu z januárovej verzie; overená oprava sumy priamo v RZD sa zachová. Kladná suma na verzii bez príznaku sa odmietne. Výpočet RZD odmietne aj januárový príznak bez kladnej overenej ročnej sumy alebo sumu bez príznaku. Ročné zníženie upravuje [§ 11 ods. 6](law:sk/2003/595#paragraf-11). Mesačný nárok vychádza z [§ 35](law:sk/2003/595#paragraf-35) a [§ 36](law:sk/2003/595#paragraf-36) spolu s [FAQ Finančnej správy, otázky 3, 7, 9](https://podpora.financnasprava.sk/260857-Nezdanite%C4%BEn%C3%A1-%C4%8Das%C5%A5-z%C3%A1kladu-dane-na-da%C5%88ovn%C3%ADka-za-rok-2026). Spätné priznanie potrebuje historický údaj a príslušný opravný postup; zaúčtované pásky sa potichu neprepisujú.

## Podklady ročného zúčtovania

Preberajú sa potvrdené pásky (`done`) príslušnej firmy a zamestnanca podľa
konca mzdového obdobia vo zvolenom roku. Rozpracované, čakajúce a zrušené
pásky aj zvolená páska vysporiadania sa vynechajú. Toto zjednotenie výberu
s výkazmi samo nepreukazuje úhradu, zákonné priradenie príjmu do daňového
roka ani splnenie podmienok RZD. Rozšírenie uchovávajúce nahradené finančné
verzie musí navyše vynechať nahradené originály.
