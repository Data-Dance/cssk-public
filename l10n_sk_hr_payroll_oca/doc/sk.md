---
title: Slovenské mzdy (OCA)
summary: Slovenská mesačná výplatná páska pre aplikáciu OCA payroll v Odoo Community — úplná mzdová štruktúra pre pracovný pomer a tri dohody.
verified: 19.0.1.24.3
family: l10n_sk_hr_payroll_base#engines
---

Úplná slovenská mzdová štruktúra pre aplikáciu OCA `payroll`: štyri štruktúry, jedna na každú formu zamestnania, so spoločnými pravidlami — sociálne a zdravotné poistenie, základ dane, nezdaniteľná časť základu dane na daňovníka, progresívna daň z príjmu, daňový bonus na dieťa, náhrada mzdy za dovolenku a pri prekážkach v sume priemerného zárobku, náhrada príjmu pri PN, exekučné zrážky a stravné. Dodáva aj datované parametre, z ktorých pravidlá čítajú, slovenské typy voľna so *Slovenským mzdovým kódom* a plánmi nárokov a ročné zúčtovanie dane. Slovenské polia sú na karte zamestnanca v záložke mzdy a na šablónach zmlúv; parametre pravidiel sú v *Mzdy → Konfigurácia → Parametre pravidiel*.

Inštaluje sa zámerne, vyžaduje modul OCA `payroll` a funguje v Odoo Community. Na zaúčtovanie do hlavnej knihy pridajte účtovný mostík pre OCA, na mzdové zvýhodnenia skupinu modulov príplatkov.

Daňovo relevantný dôchodok poberaný k 1. januáru ovplyvňuje aj mesačný nárok na NČZD. Pole *Poberá daňovo relevantný dôchodok* zaznamenajte na natívnej verzii účinnej od priznania dôchodku podľa uchovaného vyhlásenia daňovníka. Mesačný výpočet číta verziu platnú k 1. januáru svojho roka. Januárový dôchodca nemá mesačnú NČZD ani pri podpísanom vyhlásení a nízkom dôchodku. Priznanie v máji 2026 zachová mesačnú NČZD za rok 2026 a od januára 2027 ju odníme bez úpravy májovej verzie či zablokovania prepočtu decembra 2026. Samotný invalidný, vdovský alebo sirotský dôchodok príznak nenastavuje. Relevantný poistný dôchodok bez príznaku na januárovej verzii zastaví mesačné uplatnenie zrozumiteľnou správou pred pravidlami. Pri skutočnom nástupe počas roka bez januárovej verzie, alebo pri opätovnom prijatí po pracovnom pomere skončenom pred 1. januárom, zaznamenajte januárový dôchodkový status z vyhlásenia pri nástupe na prvej verzii nového pracovného pomeru. Nástup spätne nedatujte; neskoršie priznanie zostáva neskorším údajom. Verzia po mzdovom období alebo z ďalšieho roka status nepreukazuje. Zákonné parametre a pásma sa nemenia.

Ročný rozdiel pri nízkom dôchodku sa uplatňuje v RZD alebo osobnom priznaní. Ročnú sumu vrátane 13. dôchodku overte pre každé RZD. Pole *Dôchodok k 1. januáru (ročne)* poskytne predvolenú sumu z januárovej verzie; overená oprava sumy priamo v RZD sa zachová. Kladná suma na verzii bez príznaku sa odmietne. Výpočet RZD odmietne aj januárový príznak bez kladnej overenej ročnej sumy alebo sumu bez príznaku. Ročné zníženie upravuje [§ 11 ods. 6](law:sk/2003/595#paragraf-11). Mesačný nárok vychádza z [§ 35](law:sk/2003/595#paragraf-35) a [§ 36](law:sk/2003/595#paragraf-36) spolu s [FAQ Finančnej správy, otázky 3, 7, 9](https://podpora.financnasprava.sk/260857-Nezdanite%C4%BEn%C3%A1-%C4%8Das%C5%A5-z%C3%A1kladu-dane-na-da%C5%88ovn%C3%ADka-za-rok-2026). Spätné priznanie potrebuje historický údaj a príslušný opravný postup; zaúčtované pásky sa potichu neprepisujú.

## Hodinová mzda a schválená absencia

Pri hodinovej mzde zahŕňa BASIC odpracované hodiny po odpočítaní schválených
absencií. Za platenú dovolenku patrí samostatná náhrada z priemerného zárobku
podľa [§116](law:sk/2001/311#paragraf-116); tie isté hodiny sa preto nezaplatia
aj ako bežná práca. Obe podporované znamienka absencií dávajú rovnakú sumu.
Napríklad 176 plánovaných hodín pri 20 EUR/h a 8 h dovolenky znamená BASIC 3360
a náhradu 160, ak overený priemer je 20 EUR/h.

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

## Nárok na náhradu príjmu počas PN {#sickness-entitlement}

Dátumy schválenej PN určujú kalendárne dni jednotlivých pásiem; nárok určuje spoločné natívne pravidlo `SICKNESS_COMPENSATION`. Samotná absencia alebo zadaný DVZ nezakladajú nemocenské poistenie. Pri pravidelnom pracovnom pomere zostáva nárok aj starobnému dôchodcovi. Pri nepravidelných dohodách, študentskej dohode a dôchodkových DoVP/DoPČ sa náhrada neposkytuje. Právny základ: [462/2003](law:sk/2003/462) a [461/2003](law:sk/2003/461). Zákonná náhrada je podľa §5 ods.7 písm.f) zákona595/2003 oslobodená od dane, čo potvrdzuje [Finančná správa](https://podpora.financnasprava.sk/589698-N%C3%A1hrada-pr%C3%ADjmu-a-pr%C3%ADplatok-k-n%C3%A1hrade-pr%C3%ADjmu-pri-do%C4%8Dasnej-PN). Jej vylúčenie zo zdaniteľného GROSS zostáva zachované. Určenie DVZ, chýbajúce či prekrývajúce sa lekárske podklady a ručne zadané pokračovanie vyžadujú samostatné overenie.

## Skutočne odpracovaný čas pri priemere {#average-worked-time}

WORK100 obsahuje plánovaný čas. Pred overením hranice21 dní alebo168 hodín a delením mzdy hodinami sa odpočítajú absolútne dni a hodiny samostatne evidovaných absencií. Používa sa rovnaký zoznam kódov ako pri BASIC; obe nastavenia znamienok absencie majú rovnaký výsledok. Znamienko refundu naďalej uplatní volajúci iba raz. Neuložený náhľad pásky z histórie vylučuje svoj uložený originál namiesto dočasného NewId.
