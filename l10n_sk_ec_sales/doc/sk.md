---
title: SK Súhrnný výkaz
summary: Slovenský súhrnný výkaz vypočítaný z daní pre dodania do EÚ v slovenskej účtovej osnove Odoo a exportovaný do XML finančnej správy podľa vzoru platného pre dané obdobie.
verified: 19.0.1.4.0
---

## Na čo slúži {#purpose}

Slovenský platiteľ DPH, ktorý dodáva tovar alebo služby osobám identifikovaným
pre daň v inom členskom štáte EÚ, ich vykazuje v **súhrnnom výkaze** (SV),
ktorý sa podáva elektronicky finančnej správe.

Tento modul je slovenskou vrstvou modulu
[module:l10n_cssk_ec_summary_base](module:l10n_cssk_ec_summary_base), ktorý
obsahuje obrazovky a postup — príprava výkazu, kontrola riadkov, export a
podanie sú opísané [tam](module:l10n_cssk_ec_summary_base#usage). Tento modul
pridáva slovenské kódy plnenia, XML šablóny a oficiálne schémy oboch vzorov,
kontrolu kódov a predpôn IČ DPH a označí štandardné dane slovenskej účtovej
osnovy Odoo.

## Právny rámec {#legal}

Odkazy sú na [§ 80 zákona o DPH](law:sk/2004/222#paragraf-80).

- **Kto podáva.** Platiteľ, ktorý dodal tovar oslobodený od dane podľa § 43
  ods. 1 osobe identifikovanej pre daň v inom členskom štáte, premiestnil
  tovar oslobodený podľa § 43 ods. 4, zúčastnil sa na trojstrannom obchode ako
  prvý odberateľ (§ 45), dodal službu s miestom dodania v inom členskom štáte
  podľa § 15 ods. 1, pri ktorej je daň povinný platiť príjemca, alebo odoslal
  tovar v režime call-off stock
  ([§ 80 ods. 1](law:sk/2004/222#paragraf-80.odsek-1)). Zdaniteľná osoba
  registrovaná podľa § 7 alebo § 7a podáva súhrnný výkaz za každý kalendárny
  štvrťrok, v ktorom takú službu dodala
  ([ods. 3](law:sk/2004/222#paragraf-80.odsek-3)).
- **Mesačne alebo štvrťročne.** Základom je kalendárny mesiac. Za štvrťrok
  možno súhrnný výkaz podať, ak hodnota tovarov (ods. 1 písm. a) až c))
  nepresiahne **50 000 eur** v príslušnom štvrťroku a súčasne v predchádzajúcich
  štyroch štvrťrokoch; po jej prekročení podáva platiteľ súhrnný výkaz osobitne
  za každý mesiac štvrťroka ([ods. 2](law:sk/2004/222#paragraf-80.odsek-2)).
- **Obdobie a suma.** Dodania sa uvádzajú za obdobie, v ktorom vznikla daňová
  povinnosť, v eurách, zaokrúhlené na celé eurá do 0,5 eura nadol a od 0,5 eura
  vrátane nahor ([ods. 6](law:sk/2004/222#paragraf-80.odsek-6)). Oprava základu
  dane podľa § 25 sa uvádza sumou opravy za obdobie, v ktorom bola oprava
  oznámená odberateľovi ([ods. 7](law:sk/2004/222#paragraf-80.odsek-7)).
- **Opravy.** Chybu zistenú pred uplynutím lehoty opraví **opravný súhrnný
  výkaz**; po jej uplynutí **dodatočný súhrnný výkaz**, *„v ktorom uvedie len
  doplnené alebo opravené údaje“*
  ([ods. 8](law:sk/2004/222#paragraf-80.odsek-8)).
- **Lehota.** Elektronicky, **najneskôr do 25 dní** po skončení obdobia
  ([ods. 9](law:sk/2004/222#paragraf-80.odsek-9)).

V tlačive sa dodanie tovaru uvádza **bez kódu**, trojstranný obchod s kódom
**1** a dodanie služby s kódom **2**. Interne modul tovar označuje kódom **0** a
do XML ho zapíše ako prázdny kód.

## Vzory tlačiva {#version}

Finančná správa vydáva pre každý vzor samostatnú schému a staré ponecháva,
takže každé obdobie sa podáva vo vzore platnom v tom čase. Modul inštaluje
oba a výkaz ponúkne len ten, ktorý platí pre jeho obdobie:

| Verzia | Platnosť | Schéma | Tvar |
|---|---|---|---|
| Súhrnný výkaz 2010 (do 31. 12. 2019) | 1. 1. 2010 – 31. 12. 2019 | `svdph2010.xsd` | 27 záznamov na strane |
| Súhrnný výkaz 2020 (od 1. 1. 2020) | od 1. 1. 2020 | `svdph20.xsd` | 12 záznamov + 12 záznamov call-off stock na strane |

Vzor 2020 prišiel s pravidlami režimu call-off stock účinnými od 1. 1. 2020.
Obe schémy sú zhodné s kópiami zverejnenými finančnou správou (overené
9. 9. 2026); ani jedna neuvádza revíziu, takže neskoršiu zmenu z Odoo nevidno.

Obe verzie ponúkajú typy *Riadny*, *Opravný* a *Dodatočný*, ktoré v XML
označia príslušné políčko druhu súhrnného výkazu.

## Nastavenie {#setup}

Pri inštalácii modul nastaví kód plnenia na daniach pre dodania do EÚ pri
každej spoločnosti, ktorá v tej chvíli používa slovenskú účtovú osnovu, ak
tam kód ešte nie je:

| Daň slovenskej osnovy Odoo | Kód |
|---|---|
| *0% EÚ T* — dodanie tovaru do EÚ | 0 (v tlačive bez kódu) |
| *0% EÚ TRI* — trojstranný obchod | 1 |
| *0% EÚ S* — dodanie služby do EÚ | 2 |

Pozor na názvy: v anglickom rozhraní je tá istá daň pre tovar *0% EU M* a
*0% EU T* znamená trojstranný obchod.

Export potrebuje aj IČ DPH spoločnosti a daňový úrad v nastavení
**Predvolený správca dane** — pozri
[nastavenie spoločného modulu](module:l10n_cssk_ec_summary_base#setup).
Hlavička tlačiva sa vyplní zo spoločnosti: názov, ulica a číslo, PSČ, obec,
telefón a e-mail. *Číslo* je číslo na konci poľa **Ulica** („Hlavná 12“ dá
*ulica* „Hlavná“ a *číslo* „12“), prípadne polia čísla domu, ak sa adresa
vedie rozdelená; *Ulica 2* sa ako číslo podá, len ak obsahuje iba číslo.

## Príprava a podanie {#usage}

Postupujte podľa [spoločného postupu](module:l10n_cssk_ec_summary_base#usage)
v ponuke *Účtovníctvo → Výkazy → Zákonné výkazy → Súhrnný výkaz*. Okrem
spoločných kontrol export slovenského výkazu odmietne:

- riadok s iným kódom ako 0, 1 alebo 2;
- riadok, v ktorom IČ DPH odberateľa nezačína prijateľnou predponou krajiny
  (ISO kód krajiny alebo EL či XI);
- službu (kód 2) pre IČ DPH Severného Írska (XI) — XI platí len pre tovar.

Kód štátu je predpona IČ DPH odberateľa, ako ju uvádza poučenie: **EL** pre
Grécko, **XI** pre Severné Írsko.

Sumy sa zaokrúhľujú na celé eurá, polovica smerom od nuly (−9,50 je −10), po
riadkoch; celková hodnota v hlavičke je súčtom zaokrúhlených riadkov.

Elektronický kanál na slovenské podania tento modul nemá: exportované XML
nahrajte na portál finančnej správy a potom kliknite na **Označiť ako
podané** — alebo na **Podať**, ktoré zaznamená ručné podanie a uchová
potvrdenie. Osobu, ktorá výkaz podáva, a dátum vyplňte na záložke
**Hlavička**: *Meno a priezvisko*, *Telefón* a *E-mail* konateľa alebo
oprávnenej osoby (vzor 2010 e-mail nemá) a *Dátum vyhlásenia*; ak dátum
chýba, použije sa dátum exportu.

**Dodatočný súhrnný výkaz obsahuje len zmeny**, ako požaduje
[§ 80 ods. 8](law:sk/2004/222#paragraf-80.odsek-8). Pri **Vypočítať** modul
porovná prepočítané obdobie s tým, čo sa zaň podalo — s výkazmi toho istého
obdobia označenými ako podané alebo zaznamenanými ako historické podania,
v poradí, v akom boli podané — a ponechá:

- **nový** záznam tak, ako je;
- záznam, ktorého hodnota (v celých eurách, ako sa exportuje) sa
  **zmenila**, so správnou hodnotou;
- skôr podaný záznam, ktorý **zmizol**, s hodnotou 0.

Nezmenené záznamy sa vynechajú. Dodatočný výkaz bez zaznamenaného podaného
výkazu za to isté obdobie sa odmietne: pôvodný výkaz najprv označte ako
podaný alebo ho importujte ako historické podanie. *Opravný* výkaz, ktorý
pred uplynutím lehoty nahrádza pôvodný, naďalej obsahuje celé obdobie.

## Obmedzenia {#limitations}

- **Dodatočný výkaz sa porovnáva s tým, čo je zaznamenané tu.** Podanie
  urobené mimo Odoo a nezaznamenané ako historické podanie porovnanie nevidí.
- **Režim call-off stock** (ods. 1 písm. e) až g)) nie je podporovaný;
  záznamy call-off stock vo vzore 2020 sú vždy prázdne.
- **Opravy základu dane** sa vykážu za obdobie podľa dátumu zdaniteľného
  plnenia dobropisu alebo jeho *Deklarovaného obdobia DPH* — nastavte ho na
  obdobie, v ktorom bola oprava oznámená odberateľovi (ods. 7).
- Hranica 50 000 eur pre štvrťročné podávanie sa nekontroluje.
- Dodanie služby príjemcovi, ktorý o IČ DPH požiadal, ale ešte ho nemá
  pridelené (posledná veta ods. 6), sa nerieši; riadok bez IČ DPH export
  zablokuje.
- Ulica, ktorá nekončí číslom, sa zapíše celá a číslo zostane prázdne.
