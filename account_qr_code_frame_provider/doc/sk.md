---
title: Platobné QR kódy CZ/SK — spoločný základ
summary: Čo majú české a slovenské platobné QR kódy na faktúrach spoločné — zapnutie, výber formátu pre každú faktúru a rámček s logom schémy.
verified: 19.0.1.1.1
---

## Na čo slúži {#purpose}

Odoo vie na faktúru odberateľovi vytlačiť platobný QR kód. Odberateľ ho
naskenuje v aplikácii svojej banky a dostane platobný príkaz s vyplneným
účtom, sumou a údajmi platby. Každá krajina má vlastný formát:

| Formát | Krajina | Modul |
|---|---|---|
| QR Platba (*Short Payment Descriptor*) | Česko | [module:account_qr_code_qr_platba_cz](module:account_qr_code_qr_platba_cz) |
| PAY by square | Slovensko | [module:account_qr_code_pay_by_square_sk](module:account_qr_code_pay_by_square_sk) |
| payme | Slovensko | [module:account_qr_code_payme_sk](module:account_qr_code_payme_sk) |
| SEPA Credit Transfer QR (EPC) | eurozóna | vlastný formát Odoo, inštaluje sa s Účtovníctvom |

Tento modul je to, čo majú tri národné formáty spoločné. Nainštaluje sa s
ktorýmkoľvek z nich a nemá nastavenia. Modul:

- **vyberie správny formát** pre každú faktúru, ak výber necháte na Odoo
  (pozri [nižšie](#method-choice));
- nakreslí národný kód **v rámčeku jeho schémy** — s logom, ktoré odberateľ
  pozná zo svojej bankovej aplikácie;
- odstráni logo Odoo, ktoré štandardné rozloženie faktúry kladie doprostred
  platobného QR kódu.

## Zapnutie QR kódov {#setup}

1. *Účtovníctvo → Konfigurácia → Nastavenia*, blok *Zákaznícke platby*:
   zaškrtnite **QR kódy**.
2. Nainštalujte modul(y) formátov, ktoré potrebujete.
3. Bankový účet, na ktorý má odberateľ platiť, musí byť zadaný v tvare
   **IBAN** a mať vyplnený *Názov držiteľa účtu* (alebo patriť kontaktu s
   menom). Je to účet, ktorý faktúra zobrazuje ako *Banka príjemcu*.

Kód sa tlačí na PDF faktúru, kým má faktúra neuhradenú sumu, a znie na **sumu,
ktorá ešte zostáva uhradiť** — čiastočne uhradená faktúra teda žiada len
zvyšok. Uhradená faktúra kód netlačí.

Ak je nainštalovaný modul
[module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr),
odovzdajú sa kódu variabilný, konštantný a špecifický symbol faktúry ako
samostatné údaje; kam presne sa dostanú, opisuje stránka každého formátu.

## Ktorý formát faktúra dostane {#method-choice}

Rozhoduje pole *Platba QR kód* na karte *Ďalšie info* faktúry.

- **Ak v ňom formát vyberiete**, použije sa — a ak sa pre danú faktúru použiť
  nedá (iná mena, účet nie je IBAN), tlač sa zastaví so správou, prečo.
- **Ak ho necháte prázdne**, Odoo vezme prvý formát, ktorý faktúre vyhovuje,
  v tomto poradí, a uloží ho do poľa:

| Poradie | Formát | Použije sa automaticky, keď |
|---|---|---|
| 1 | QR Platba | faktúra je v CZK **alebo** odberateľ je z Česka |
| 2 | PAY by square | faktúra je v EUR **a** vaša spoločnosť (držiteľ účtu) aj odberateľ sú zo Slovenska |
| 3 | payme | ako pri PAY by square |
| 4 | SEPA Credit Transfer QR | faktúra je v EUR |

Všetky formáty navyše vyžadujú IBAN z krajiny SEPA. Ak strana nemá vyplnenú
krajinu, formátu to neuškodí: slovenská spoločnosť, ktorá fakturuje
odberateľovi bez krajiny, dostane PAY by square.

Česká spoločnosť teda pri faktúre v eurách nemeckému odberateľovi dostane
kód SEPA, slovenská spoločnosť pri faktúre českému odberateľovi QR Platbu a
faktúra medzi dvoma slovenskými firmami slovenský formát.

Formát uložený na faktúre už zostane. Ak má Odoo vyberať znova, pole
vymažte.

## Obmedzenia {#limitations}

- **PAY by square má prednosť pred payme**, a to pevným poradím, nie poradím
  načítania modulov: ak sú nainštalované oba, medzi slovenskými stranami sa
  automaticky vyberie PAY by square. Ak chcete na faktúre payme, vyberte ho
  v poli *Platba QR kód*.
- QR Platba sa vyberie pre každú faktúru českému odberateľovi, aj v eurách a
  aj vtedy, keď vaša spoločnosť nie je česká.
- Logo Odoo zmizne len z platobného QR kódu. Samostatný QR kód s odkazom na
  platbu (*Pridať odkaz do QR kódu na PDF*) sa nemení.
- Národné formáty sa vyberajú automaticky len na faktúrach. Inde (napríklad
  pri platobnej požiadavke vytvorenej priamo z bankového účtu) platí
  štandardné poradie Odoo.
