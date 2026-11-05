---
title: Platobné symboly CZ/SK — SEPA úhrady (OCA)
summary: Zapíše variabilný, konštantný a špecifický symbol do súboru SEPA úhrad, ktorý vytvára platobný príkaz OCA, v tvare, ktorý čítajú slovenské a české banky.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#iso20022
---

Zapíše symboly každej uhrádzanej faktúry do súboru SEPA úhrad (pain.001), ktorý vytvára platobný príkaz OCA (`account_banking_sepa_credit_transfer`): do identifikátora end-to-end v tvare `/VS…/SS…/KS…`, ktorý čítajú slovenské banky, alebo na koniec správy pre príjemcu ako `/VS/…/KS/…/SS/…`. Každý bankový denník má voľbu **Platobné symboly CZ/SK v SEPA úhradách**; faktúry s rôznymi symbolmi sa uhradia samostatnými prevodmi.

Nainštaluje sa sám, keď sú nainštalované symboly v platobných príkazoch aj modul SEPA úhrad.
