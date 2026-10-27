---
title: CZ/SK Bank File Formats — Shared Builders
summary: The ABO and MultiCash file writers and the Czech account-number parser shared by the bank-file modules.
verified: 19.0.1.3.2
family: account_abo#format
---

Holds the ABO and MultiCash payment-file writers, so the Community (payment order) and Enterprise (batch payment) variants produce identical files, together with the reading of Czech account numbers in both spellings (IBAN and `prefix-number/bank code`) and of `VS:`/`KS:`/`SS:` tokens in a payment's text. The KB BEST and Fio modules and the MT940 and KB statement imports use the same account parser.

It has no screen and no settings. It is installed as a dependency of the modules that need it.
