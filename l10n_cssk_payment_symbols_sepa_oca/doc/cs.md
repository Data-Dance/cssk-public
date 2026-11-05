---
title: Platební symboly CZ/SK — SEPA převody (OCA)
summary: Zapíše variabilní, konstantní a specifický symbol do souboru SEPA převodů, který vytváří platební příkaz OCA, v podobě, kterou čtou slovenské a české banky.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#iso20022
---

Zapíše symboly každé hrazené faktury do souboru SEPA převodů (pain.001), který vytváří platební příkaz OCA (`account_banking_sepa_credit_transfer`): do identifikátoru end-to-end ve tvaru `/VS…/SS…/KS…`, který čtou slovenské banky, nebo na konec zprávy pro příjemce jako `/VS/…/KS/…/SS/…`. Každý bankovní deník má volbu **Platební symboly CZ/SK v SEPA převodech**; faktury s různými symboly se uhradí samostatnými převody.

Nainstaluje se sám, když jsou nainstalované symboly v platebních příkazech i modul SEPA převodů.
