---
title: CZ/SK Payment Symbols — SEPA Credit Transfer (OCA)
summary: Writes the variable, constant and specific symbol into the SEPA credit transfer file of OCA payment orders, in the form Slovak and Czech banks read.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#iso20022
---

Puts the symbols of each paid bill into the SEPA credit transfer file (pain.001) that an OCA payment order (`account_banking_sepa_credit_transfer`) generates: in the end-to-end identifier as `/VS…/SS…/KS…`, which Slovak banks read, or appended to the message for the payee as `/VS/…/KS/…/SS/…`. Each bank journal has the option **CZ/SK Symbols in SEPA Transfers**; bills with different symbols become separate transfers.

It installs itself when the payment-order symbols and the SEPA credit transfer module are both installed.
