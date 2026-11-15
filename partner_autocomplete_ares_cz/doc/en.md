---
title: Partner Autocomplete from ARES (Czech Republic)
summary: Fills Czech contacts from ARES, the Czech register of economic subjects, by company name, IČO or DIČ.
verified: 19.0.1.4.0
family: partner_autocomplete_dispatcher#ares
---

Adds ARES as a provider of partner autocomplete. A Czech contact is looked up in ARES by company name, by IČO, or by a legal person's DIČ, and filled with its name, address, DIČ and, if you choose a field for them, its IČO, its prevailing activity in CZ-NACE 2025 and its entry in the veřejný rejstřík: the register, the rejstříkový soud, the spisová značka, the status and the dates of establishment and dissolution. With [module:l10n_cz_trade_registry](module:l10n_cz_trade_registry) installed those go to its fields without any setting. Czech contacts are looked up in ARES from every company, whichever provider the company itself has chosen.

It needs the partner-autocomplete dispatcher, which it installs, and no account or key. Its settings appear under *Settings → General Settings → Contacts* when ARES is selected as the company's provider.
