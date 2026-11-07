---
title: SK Hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti
summary: Ročné hlásenie zamestnávateľa o príjmoch zo závislej činnosti, zrazených preddavkoch na daň a daňovom bonuse, s údajmi o každom zamestnancovi, zostavené z výplatných pások roka ako XML pre finančnú správu.
verified: 19.0.2.1.1
---

## Na čo slúži {#purpose}

Po skončení roka podáva zamestnávateľ, ktorý zráža preddavky na daň, správcovi
dane **Hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti**.
Zhŕňa mzdy, zrazené preddavky na daň a daňové bonusy za rok a uvádza každého
zamestnanca s jeho údajmi.

Modul hlásenie zostaví z výplatných pások kalendárneho roka a vyexportuje ho
ako XML vo formáte finančnej správy. Podobne ako mesačný
[module:l10n_sk_hr_payroll_monthly_tax_overview](module:l10n_sk_hr_payroll_monthly_tax_overview)
funguje s oboma mzdovými jadrami (pozri
[skupinu modulov slovenských miezd](module:l10n_sk_hr_payroll_base#declarations))
a obrazovky, stavy a kontrolu XML zdieľa s ostatnými mzdovými hláseniami
prostredníctvom
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base).

## Právny rámec {#legal}

Odkazy sú na [zákon o dani z príjmov](law:sk/2003/595).

- **Povinnosť.** Zamestnávateľ, ktorý je platiteľom dane, predkladá správcovi
  dane hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti
  poskytnutých jednotlivým zamestnancom za uplynulé zdaňovacie obdobie, o
  zrazených preddavkoch na daň, o zamestnaneckej prémii, o daňovom bonuse a o
  daňovom bonuse na zaplatené úroky —
  [§ 39 ods. 9 písm. b)](law:sk/2003/595#paragraf-39.odsek-9.pismeno-b).
  Hlásenie podľa toho istého ustanovenia obsahuje aj meno, priezvisko a
  **rodné číslo** zamestnanca — preto ho modul bez rodného čísla nevygeneruje.
- **Lehota.** Hlásenie sa podáva **do konca apríla** po uplynutí zdaňovacieho
  obdobia — [§ 49 ods. 2](law:sk/2003/595#paragraf-49.odsek-2). Hlásenie za
  rok 2026 treba podať do 30. 4. 2027.

## Nastavenie {#setup}

- **DIČ spoločnosti.** Na spoločnosti vyplňte *DIČ* (10-miestne daňové
  identifikačné číslo); bez neho generovanie skončí chybou.
- **Adresa, telefón a e-mail spoločnosti** idú do hlavičky. Číslo domu sa
  berie z konca poľa *Ulica* (*Hlavná 12*, *Hlavná 1141/11*); *Ulica2* sa
  použije, len ak obsahuje iba číslo — budova, poschodie či c/o sa ako číslo
  domu nikdy nepodávajú.
- **Každý zamestnanec potrebuje rodné číslo.** Zadajte ho (9 alebo 10 číslic)
  do poľa *Identifikačné č* na karte *Personal* formulára zamestnanca. Lomka a
  medzery sa ignorujú.
- **Mená a adresy zamestnancov.** Príloha preberá súkromnú ulicu (číslo domu
  oddelené rovnako), PSČ a obec zamestnanca. **Posledné slovo mena je
  priezvisko** a všetko pred ním meno, preto mená zapisujte ako „Ján Peter Novák“, nie „Novák Ján“. Ak je
  nainštalovaný `hr_employee_firstname`, použijú sa jeho samostatné polia pre
  meno a priezvisko.
- Verzia tlačiva **Annual tax reconciliation statement 2023+** (schéma
  `HLASENIEv23`, platná od 1. 1. 2023) sa nainštaluje spolu s modulom a
  vyberie automaticky.

## Podanie za rok {#usage}

*Mzdové hlásenia → SK hlásenie o vyúčtovaní dane*, potom *Nové*.

1. Zvoľte **Rok**. Obdobím je vždy 1. január až 31. december.
2. **Typ opravy** nechajte na *Regular* (riadne hlásenie).
3. Kliknite na **Generovať**. Modul zoberie všetky nezrušené výplatné pásky
   spoločnosti, ktorých obdobie leží v danom roku — **iba potvrdené pásky** —,
   pre každého zamestnanca vytvorí stĺpec prílohy, vykreslí XML a overí ho
   voči oficiálnej schéme `rh2023.xsd`. Ak niektorému zamestnancovi chýba
   rodné číslo, chyba ho menuje a nič sa nevygeneruje.
4. XML si stiahnite z poľa *Príloha XML* a na portál finančnej správy ho
   nahrajte sami.
5. Po podaní kliknite na **Označiť ako odoslané**; podaná kópia sa uchová a
   záznam sa uzamkne. *Vrátiť do konceptu* ho odomkne.

## Prílohy a overený rozsah {#mapping}


Verzia 19.0.2.1.0, 7.11.2026. Používa nezmenenú priloženú XSD rh2023;
nejde o potvrdenie nového ročníka formulára ani prijatia úradom.

Bez vykonaného RZD patrí zamestnanec do časti IV. Časť V obsahuje údaje RZD:
celkový príjem zo všetkých zamestnávateľov a osobitne príjem tohto zamestnávateľa,
sociálne a zdravotné poistné, nezdaniteľné časti a preddavky. Riadky r4a/r4b
nie sú daň; preddavok patrí do r6. Pôvodný export dával všetkých do časti V.

Samotný formulárový modul neimplementuje druhý mzdový výpočet. Most
`_annual_settlement_column(line)` vráti None pre časť IV alebo overené údaje
časti V a `completed_on` vo formáte DD.MM.RRRR. Známe vypočítané/naviazané RZD
bez mosta export zastaví. Vykonanie RZD nie je jeho následná výplata.

Časti IV/V sa počítajú a stránkujú samostatne. Mesiace vychádzajú z vybraných
pások a ich historických verzií. Priradenie podľa skutočnej výplaty a daňového
roka musí zabezpečiť mzdový adaptér; dátum pásky sám nedokazuje výplatu.
Daňový bonus bez identít detí a mesiacov nároku ani zahraničný pobyt sa nesmú
potichu vynechať: vyžadujú doplnený adaptér.

Právny podklad: poučenie FS k HLASENIEv23, časti IV/V:
https://pfseform.financnasprava.sk/Formulare/Poucenia/HLASENIEv23-poucenie.pdf

Testy overujú OCA, XML/XSD, rozdelenie a význam riadkov. Beh OCA sa nevydáva
za otestovanie Enterprise. Zmiešaný komponentový test používa vzor overeného
mosta; reálne ročné údaje musí dodať implementácia konkrétneho mzdového jadra.

## Opravy {#corrections}

Hlásenie pozná druhy *riadne*, *opravné* a *dodatočné*. Nastavte **Typ
opravy** na *Corrective* alebo *Supplementary*. Modul opravné ani dodatočné
hlásenie nevygeneruje, kým nie je riadne hlásenie označené ako odoslané — pozri
však [Obmedzenia](#limitations): pôvodné hlásenie dnes hľadá len v **tom istom
mesiaci**, v ktorom bol nový záznam vytvorený.

## Platnosť ročníka formulára

Verzia 19.0.2.1.1 obmedzuje rh2023 / HLASENIEv23 na daňové roky do 2025
vrátane; existujúce záznamy upraví upgrade migrácia. Export za 2026 a neskôr
sa zastaví. Predpísaný vzor 2026 mení význam riadkov časti V; úspešná kontrola
starou XSD preto nepreukazuje správnosť nového podania. Pred podaním treba
overený adaptér aktuálneho formulára, ktorý tento modul zatiaľ nedodáva.

Zdroj: https://www.mfsr.sk/files/archiv/75/HLASENIEv26-v1.2.pdf

