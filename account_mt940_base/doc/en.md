---
title: MT940 / MultiCash Statement Format — Shared Parser
summary: The SWIFT MT940 statement reader with the Czech layout of field :86:, used by the MT940 statement import.
verified: 19.0.1.0.0
family: account_statement_import_mt940#format
---

Reads SWIFT MT940 statements as Czech banks deliver them through MultiCash, X-business and Business 24, including the `?NN` subfields of field `:86:` that carry VS/KS/SS and the counterparty, recognising each symbol by its prefix rather than its position.

It has no screen and no settings. It is installed as a dependency of `account_statement_import_mt940`.
