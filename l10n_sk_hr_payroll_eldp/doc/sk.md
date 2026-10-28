---
title: SK ELDP — evidenčný list dôchodkového poistenia
summary: Evidenčný list dôchodkového poistenia za kalendárny rok — vymeriavací základ a obdobie poistenia každého zamestnanca zostavené z výplatných pások roka a vyexportované ako hromadné XML pre Sociálnu poisťovňu.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

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
- **Predloženie.** Platné znenie zákona ročné predkladanie ELDP výslovne
  neupravuje; zamestnávateľ predkladá podklady na výzvu organizačnej zložky
  Sociálnej poisťovne
  ([§ 231 ods. 1 písm. g)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-g),
  záver), na tlačive, ktoré určí Sociálna poisťovňa
  ([§ 231 ods. 2](law:sk/2003/461#paragraf-231.odsek-2)). ELDP podajte vtedy
  a za tých zamestnancov, za ktorých ho Sociálna poisťovňa vyžaduje.

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
