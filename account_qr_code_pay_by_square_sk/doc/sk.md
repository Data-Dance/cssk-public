---
title: PAY by square (Slovensko)
summary: Tlačí na faktúry odberateľom slovenský platobný QR kód PAY by square s variabilným, konštantným a špecifickým symbolom ako samostatnými údajmi.
verified: 19.0.1.2.2
---

## Na čo slúži {#purpose}

**PAY by square** je štandard platobného QR kódu Slovenskej bankovej
asociácie. Číta ho každá slovenská banková aplikácia: odberateľ naskenuje kód
na vašej faktúre a dostane platobný príkaz s vyplneným vaším účtom, sumou a
platobnými symbolmi.

Modul pridáva PAY by square ako formát QR kódu na faktúrach Odoo. To, čo majú
národné formáty spoločné — zapnutie QR kódov, potrebný bankový účet a spôsob,
akým Odoo pre každú faktúru vyberá formát — opisuje modul
[module:account_qr_code_frame_provider](module:account_qr_code_frame_provider),
ktorý sa nainštaluje spolu s týmto modulom.

## Nastavenie {#setup}

1. Zapnite *QR kódy* v *Účtovníctvo → Konfigurácia → Nastavenia* — pozri
   [spoločné nastavenie](module:account_qr_code_frame_provider#setup).
2. Použite bankový účet v tvare **IBAN** z krajiny SEPA s vyplneným *Názvom
   držiteľa účtu*. Ak chcete mať v kóde aj BIC, vyplňte ho pri banke
   (*Identifikačné číslo banky*); nie je povinný.
3. Fakturujte v **EUR**. Pre iné meny sa PAY by square neponúka.

Odoo vyberie PAY by square **automaticky** pre faktúru v eurách, keď je vaša
spoločnosť aj odberateľ zo Slovenska (alebo odberateľ nemá vyplnenú krajinu).
Pri ktorejkoľvek inej faktúre môžete *PAY by square (Slovensko)* vybrať ručne
v poli *Platba QR kód* — pozri
[Ktorý formát faktúra dostane](module:account_qr_code_frame_provider#method-choice).

## Čo kód obsahuje {#content}

| Údaj v kóde | Odkiaľ sa berie |
|---|---|
| IBAN, BIC | účet v poli *Banka príjemcu* na faktúre |
| Meno príjemcu | *Názov držiteľa účtu* tohto účtu, alebo meno jeho vlastníka |
| Suma, mena | suma, ktorá na faktúre zostáva uhradiť, EUR |
| Variabilný, konštantný, špecifický symbol | symboly faktúry, ak je nainštalovaný modul [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr) |
| Referencia platiteľa | *Referencia platby* (alebo číslo faktúry) — len ak faktúra nemá symboly, ako to predpisuje štandard |
| Správa pre príjemcu | *Referencia platby*, a ak nie je, číslo faktúry |
| Dátum splatnosti | dátum splatnosti faktúry; dnešný deň, ak už uplynul |

Kód je jednorazová platba: nie trvalý príkaz ani inkaso. Kreslí sa v rámčeku
PAY by square, aby ho odberateľ spoznal.

## Obmedzenia {#limitations}

- Adresa príjemcu sa do kódu nedáva.
- Len eurá a len jeden bankový účet v kóde.
- Ak je nainštalovaný aj payme, Odoo automaticky vyberá PAY by square; pozri
  [spoločné obmedzenia](module:account_qr_code_frame_provider#limitations).
