---
title: GPC Statement Format — Shared Parser
summary: The GPC bank-statement reader shared by the Community and Enterprise GPC imports.
verified: 19.0.1.0.0
family: account_statement_import_gpc#format
---

Reads GPC electronic statements — the `074` header, `075` transactions and `076`/`078`/`079` message lines — into statements with balances, counterparty accounts and VS/KS/SS, so the Community and the Enterprise GPC imports read every file the same way.

It has no screen and no settings. It is installed as a dependency of `account_statement_import_gpc` or `account_statement_import_gpc_ee`.
