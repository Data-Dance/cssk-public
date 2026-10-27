---
title: KB BEST Format — Shared Builders and Parser
summary: Komerční banka's BEST format — domestic and foreign payment records and the electronic statement — shared by the KB BEST payment export and statement import.
verified: 19.0.1.0.0
family: account_payment_kb_best#format
---

Writes BEST payment files (domestic `01` records, foreign/SEPA `02` records with the `03` address) and reads BEST statements (`51` turnover, `52` transactions), applying KB's own rules before the bank does: KB debit account only, unique daily sequence numbers, refused constant symbols, SEPA and EEA charge rules.

It has no screen and no settings. It is installed as a dependency of `account_payment_kb_best` and `account_statement_import_kb_best`.
