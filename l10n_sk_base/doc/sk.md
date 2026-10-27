---
title: Slovenská základná lokalizácia (DIČ)
summary: Dáva slovenskému DIČ — daňovému identifikačnému číslu — vlastné pole na kontaktoch a spoločnostiach, oddelené od IČ DPH aj od IČO.
verified: 19.0.2.0.0
---

## Na čo slúži {#purpose}

Slovenský podnikateľ má až tri identifikátory a každý je iné číslo:

| Identifikátor | Význam | Pole v Odoo |
|---|---|---|
| **IČO** | identifikačné číslo organizácie | *IČO* (`company_registry`) |
| **DIČ** | daňové identifikačné číslo pridelené pri registrácii na daň z príjmov, desať číslic | **DIČ**, pridáva ho tento modul |
| **IČ DPH** | identifikačné číslo pre daň, spravidla `SK` a DIČ | pole DPH (`vat`) |

Kto je registrovaný na daň z príjmov, ale nie je platiteľom DPH, má DIČ a
**nemá IČ DPH**. Pole DPH v Odoo to vyjadriť nevie a slovenská lokalizácia Odoo
má DIČ len na spoločnosti (*Income Tax ID*), nie pri odberateľoch a
dodávateľoch. Modul pridá DIČ ku každému kontaktu a DIČ spoločnosti z neho
urobí tú istú hodnotu.

Odtiaľto ho čítajú iné moduly: slovenská faktúra ho tlačí vedľa IČ DPH, daňové
priznania k dani z príjmov, účtovná závierka a mzdové výkazy ho uvádzajú v XML.
S modulom [module:partner_autocomplete_orsf_sk](module:partner_autocomplete_orsf_sk)
sa vyplní z verejných registrov.

V Česku takéto pole netreba: tam je *DIČ* priamo číslo pre DPH, ktoré už drží
pole DPH v Odoo.

## Právny rámec {#legal}

DIČ prideľuje správca dane pri registrácii daňového subjektu a daňový subjekt
je povinný ho uvádzať pri styku so správcom dane —
[§ 67 ods. 7 daňového poriadku](law:sk/2009/563#paragraf-67.odsek-7).

## Kam ho zadať {#usage}

- **Kontakty.** Pri kontakte s krajinou Slovensko sa pole **DIČ** zobrazí
  tesne pred poľom DPH. Patrí spoločnosti, nie jej jednotlivým kontaktným
  osobám: osoba pod spoločnosťou zobrazuje a používa DIČ spoločnosti, rovnako
  ako Odoo zaobchádza s IČ DPH.
- **Vaša spoločnosť.** *Nastavenia → Spoločnosti → vaša spoločnosť*: pole
  **DIČ** je za poľom DPH, ak je krajinou spoločnosti Slovensko. Je to DIČ
  kontaktu spoločnosti, takže zmena na jednom mieste sa prejaví na oboch.

Pôvodné pole *Income Tax ID* zo slovenskej lokalizácie Odoo má teraz rovnakú
hodnotu a vo formulári spoločnosti je skryté, aby sa číslo nezobrazovalo dvakrát.

Pole sa nekontroluje; zadajte desať číslic tak, ako boli pridelené.

## Prechod zo starších verzií {#upgrade}

Pri inštalácii modul zozbiera DIČ zadané inde — v poli *Income Tax ID*
spoločnosti, v staršom spoločnom poli modulu jadra CZ/SK alebo v poli
spoločnosti, ktoré si viedli niektoré slovenské mzdové moduly — a presunie ho
do nového poľa. Hodnotu, ktorá už v novom poli je, nikdy neprepíše. Ručne netreba
robiť nič.

## Obmedzenia {#limitations}

- Formát sa nekontroluje: neoveruje sa dĺžka, číslice ani zhoda s IČ DPH.
- Pole sa zobrazuje len pri kontaktoch a spoločnostiach s krajinou Slovensko.
- Vlastný slovenský preklad Odoo na niektorých obrazovkách označuje ako *DIČ*
  aj pole DPH. Nezameňte ich: pole DPH obsahuje IČ DPH s predponou `SK`.
- Ak jeden import alebo volanie API nastaví *DIČ* a *Income Tax ID*
  spoločnosti na rôzne hodnoty, odmietne sa, lebo ide o jedno číslo.
