---
title: SK ELDP — evidenčný list dôchodkového poistenia
summary: Evidenčný list dôchodkového poistenia za kalendárny rok — vymeriavací základ a obdobie poistenia každého zamestnanca zostavené z výplatných pások roka a vyexportované ako hromadné XML pre Sociálnu poisťovňu.
verified: 19.0.1.1.3
---

## Na čo slúži {#purpose}

**Iba obdobia pred 1. januárom 2026.** Povinnosť predkladať ELDP za nové
obdobia bola od roku 2026 zrušená. Údaje za tieto obdobia sa poskytujú
prostredníctvom príslušných mesačných výkazov. Modul ponecháva historické
podania a opravy za staršie obdobia; nový záznam predvolí rok 2025.

*Evidenčný list dôchodkového poistenia* (**ELDP**) zaznamenáva za každého
zamestnanca a kalendárny rok obdobie dôchodkového poistenia a vymeriavací
základ, z ktorého sa platilo poistné na dôchodkové poistenie. Sociálna
poisťovňa z neho určuje nárok na dôchodok.

Modul zostaví elektronické hromadné ELDP (záznam `eldpZec` za každého
zamestnanca) za celý rok z výplatných pások toho roka a vyexportuje ho do XML.
Výplatné pásky číta cez
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
takže funguje s oboma mzdovými jadrami — pozri
[príručku slovenských miezd](module:l10n_sk_hr_payroll_base#declarations).

## Právny rámec {#legal}

Odkazy sú na [zákon o sociálnom poistení](law:sk/2003/461).

- **Evidencia zamestnávateľa.** Zamestnávateľ vedie evidenciu zamestnanca na
  účely sociálneho poistenia počas celého trvania poistenia
  ([§ 232 ods. 1](law:sk/2003/461#paragraf-232.odsek-1)); obsahuje okrem iného
  deň vzniku a skončenia pracovného pomeru a **neobmedzený vymeriavací základ
  zamestnanca**
  ([§ 232 ods. 2 písm. e)](law:sk/2003/461#paragraf-232.odsek-2.pismeno-e)).
- **Podávanie je od roku 2026 zrušené.** Zákon č. 310/2024 Z. z. vypustil
  povinnosť zamestnávateľa predkladať túto evidenciu (§ 231 ods. 1 písm. j)
  v znení účinnom do 31. decembra 2025) s účinnosťou od 1. januára 2026.
  Sociálna poisťovňa údaje získava zo svojich systémov; jediný údaj, ktorý
  niesol iba ELDP, náhrada mzdy z vážnych prevádzkových dôvodov (§ 142 ods. 4
  a § 250b ods. 6 Zákonníka práce), sa presúva do mesačného výkazu
  ([oznam Sociálnej poisťovne](https://www.socpoist.sk/news/povinnost-zamestnavatelov-predkladat-evidencne-listy-dochodkoveho-poistenia-sa-od-roku-2026)).
- **Jednorazové podanie za obdobie pred rokom 2026.**
  [§ 293gl](law:sk/2003/461#paragraf-293gl) ešte vyžaduje evidenciu za obdobie
  pred 1. januárom 2026 za všetkých zamestnancov, a to do:

  | Zamestnanci | Lehota |
  |---|---|
  | skončili pred rokom 2026 a evidencia nebola predložená (alebo bola vrátená na opravu) | 31. januára 2026 |
  | právny vzťah trvá, zamestnávateľ mal k 31. decembru 2025 menej ako 51 zamestnancov | 30. júna 2026 |
  | právny vzťah trvá, 51 až 500 zamestnancov | 30. septembra 2026 |
  | právny vzťah trvá, viac ako 500 zamestnancov | 31. decembra 2026 |

  Evidencia pokrýva každý doteraz nevykázaný rok pred rokom 2026, nielen rok
  2025. Modul zostavuje vždy jeden kalendárny rok z výplatných pások toho roka,
  od roku 2020; roky pred zavedením miezd v Odoo treba podať z pôvodného
  systému. Súbor za rok 2026 a neskôr modul odmietne vygenerovať aj označiť
  za podaný; uložené prílohy ponechá.

## Nastavenie {#setup}

Na spoločnosti:

| Údaj | Použije sa ako |
|---|---|
| *IČO*, **presne 8 číslic** | `<ico>` |
| *Variabilný symbol Sociálnej poisťovne*, presne 10 číslic | `<icz>`, identifikačné číslo zamestnávateľa v Sociálnej poisťovni |
| obec a 5-miestne PSČ (ulica nepovinná) | adresa zamestnávateľa |

*Variabilný symbol Sociálnej poisťovne* vyplňte priamo vo formulári ELDP.
Ukladá sa na spoločnosti a je spoločný s modulmi MVP, VPP a RLFO, takže sa
zadáva raz; na jeho zmenu treba právo upravovať spoločnosti.

Pri zamestnancovi: **rodné číslo** v poli *Identifikačné č*, dátum narodenia
(*Birthday*) a pri tých, čo odišli, *Dátum odchodu*. **Posledné slovo mena je
priezvisko**, všetko pred ním meno; ak je nainštalovaný
`hr_employee_firstname`, použijú sa jeho samostatné polia pre meno.

## Zostavenie ELDP {#usage}

*Mzdové hlásenia → SK ELDP (dôchodkové)*, potom *Nové*.

1. Zvoľte **Rok**. Obdobie je vždy 1. januára až 31. decembra.
2. Kliknite na **Generovať**. Zoberú sa všetky výplatné pásky spoločnosti,
   ktorých obdobie leží v danom roku (okrem zrušených), vytvorí sa riadok za
   každého zamestnanca a XML sa overí voči `ELDP-v2015_1.3.xsd` a priloží.
3. XML nahrajte na portál Sociálnej poisťovne a kliknite na **Označiť ako
   odoslané**. **Vrátiť do konceptu** ELDP znova otvorí.

Generovanie sa zastaví, ak údaje spoločnosti nie sú úplné, ak zamestnanec
nemá platné rodné číslo alebo dátum narodenia, alebo ak za rok neexistuje
žiadna výplatná páska.

## Obsah záznamu {#output}

| Údaj | Zdroj |
|---|---|
| rodné číslo, priezvisko, meno, dátum narodenia | zamestnanec |
| vznik poistného vzťahu (`datVzniku`) | začiatok súčasného neprerušeného radu zmlúv zamestnanca (*Dátum začiatku zmluvy*) |
| zánik (`datZaniku`) alebo *trvá* (`trva`) | dátum odchodu zamestnanca, ak pripadne do roka |
| obdobie v roku (`datOd` – `datDo`) | poistný vzťah ohraničený rokom |
| vymeriavací základ na dôchodkové poistenie (`vzDP`) | súčet *GROSS* zamestnanca za rok |
| znak poistenia (`znakPoist`) | vždy *A* (zamestnanec) |
| vylúčené dni (`dniVyluc`) | vždy 0 |

## Obmedzenia {#limitations}

- **Vymeriavací základ je súčet GROSS.** Neznižuje sa o vylúčené obdobia
  a neuplatňuje sa žiadne maximum. Skontrolujte ho pri zamestnancoch
  s neplateným voľnom, PN, materskou alebo rodičovskou dovolenkou a pri
  vysokých príjmoch.
- **Jedno súvislé obdobie na zamestnanca a rok.** Viac období v jednom roku
  (odchod a návrat, prerušenie poistenia) sa na samostatné riadky nerozdelí.
- Vylúčené dni sú vždy 0 a každý zamestnanec má znak *A* (zamestnanec), aj
  dohodári.
- Započítajú sa aj koncepty výplatných pások; výplatná páska presahujúca
  hranicu roka sa ignoruje.
- Len riadne podanie; opravy cez portál. Dodáva sa len schéma z roku 2015
  (verzia 1.3).
- Overenie voči schéme kontroluje tvar súboru, nie sumy.
