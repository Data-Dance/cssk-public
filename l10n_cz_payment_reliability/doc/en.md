---
title: CZ Supplier Reliability — ADIS
summary: The Czech register behind the supplier reliability check — nespolehlivý plátce and published bank accounts from the Ministry of Finance ADIS service.
verified: 19.0.1.2.0
family: l10n_cssk_payment_reliability#cz-provider
---

Answers the supplier reliability check for Czech suppliers: it asks the Ministry of Finance ADIS web service whether the supplier is a nespolehlivý plátce and which bank accounts it has published, converts the published domestic account numbers — and an account you are paying that was typed in the domestic form — to IBAN and compares them. A subject ADIS does not hold as a plátce is reported as not checked rather than as paying an unpublished account. One request per check, no key needed.

Install it together with the reliability check and the Czech chart of accounts (`l10n_cz`). It has no screen or settings of its own; it applies to suppliers whose country is the Czech Republic and who have a *Tax ID*.
