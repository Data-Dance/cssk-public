---
title: Formát výpisov GPC — spoločný parser
summary: Čítanie bankových výpisov GPC, ktoré zdieľajú importy GPC pre Community aj Enterprise.
verified: 19.0.1.0.0
family: account_statement_import_gpc#format
---

Načíta elektronické výpisy GPC — hlavičku `074`, transakcie `075` a riadky správ `076`/`078`/`079` — do výpisov so zostatkami, účtami protistrany a symbolmi VS/KS/SS, aby import GPC v Community aj v Enterprise čítal každý súbor rovnako.

Nemá obrazovku ani nastavenia. Inštaluje sa ako závislosť modulu `account_statement_import_gpc` alebo `account_statement_import_gpc_ee`.
