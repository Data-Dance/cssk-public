---
title: payme (Slovensko)
summary: Tlačí na faktúry odberateľom slovenský platobný odkaz payme ako QR kód; po naskenovaní sa otvorí banková aplikácia odberateľa s vyplnenou platbou.
verified: 19.0.1.2.1
---

## Na čo slúži {#purpose}

**payme** je štandard platobného odkazu Slovenskej bankovej asociácie:
webová adresa `payme.sk`, ktorá nesie účet, sumu a identifikáciu platby. Modul
tlačí tento odkaz na faktúry ako QR kód. Odberateľ ho naskenuje fotoaparátom
telefónu alebo bankovou aplikáciou a otvorí sa mu banková aplikácia s
vyplnenou platbou.

To, čo majú národné formáty spoločné — zapnutie QR kódov, potrebný bankový
účet a spôsob, akým Odoo pre každú faktúru vyberá formát — opisuje modul
[module:account_qr_code_frame_provider](module:account_qr_code_frame_provider),
ktorý sa nainštaluje spolu s týmto modulom.

## Nastavenie {#setup}

1. Zapnite *QR kódy* v *Účtovníctvo → Konfigurácia → Nastavenia* — pozri
   [spoločné nastavenie](module:account_qr_code_frame_provider#setup).
2. Použite bankový účet v tvare **IBAN** z krajiny SEPA s vyplneným *Názvom
   držiteľa účtu*.
3. Fakturujte v **EUR**. Pre iné meny sa payme neponúka.

Odoo vyberie payme **automaticky** pre faktúru v eurách, keď je vaša
spoločnosť aj odberateľ zo Slovenska (alebo odberateľ nemá vyplnenú krajinu)
a nie je nainštalovaný PAY by square. Inak vyberte *payme (Slovensko)* v poli
*Platba QR kód* na faktúre — pozri
[Ktorý formát faktúra dostane](module:account_qr_code_frame_provider#method-choice).

## Čo odkaz obsahuje {#content}

| Údaj | Odkiaľ sa berie |
|---|---|
| IBAN | účet v poli *Banka príjemcu* na faktúre |
| Suma, mena | suma, ktorá na faktúre zostáva uhradiť, EUR |
| Identifikácia platby | ak je nainštalovaný modul [module:l10n_cssk_payment_symbols](module:l10n_cssk_payment_symbols#qr) a faktúra má symboly: `/VS…/SS…/KS…`; inak *Referencia platby* alebo číslo faktúry. Najviac 35 znakov. |
| Meno príjemcu | *Názov držiteľa účtu*, alebo meno vlastníka účtu; najviac 70 znakov |
| Správa | *Referencia platby*, a ak nie je, číslo faktúry |

Kód sa kreslí v rámčeku payme.

## Obmedzenia {#limitations}

- Dátum splatnosti sa neodovzdáva; banková aplikácia navrhne vlastný dátum
  platby.
- Len eurá.
- Ak je nainštalovaný aj PAY by square, Odoo automaticky vyberá ten; pozri
  [spoločné obmedzenia](module:account_qr_code_frame_provider#limitations).
