---
title: Formát výpisů MT940 / MultiCash — společný parser
summary: Čtení výpisů SWIFT MT940 s českou strukturou pole :86:, které používá import výpisů MT940.
verified: 19.0.1.0.0
family: account_statement_import_mt940#format
---

Načte výpisy SWIFT MT940 tak, jak je české banky dodávají přes MultiCash, X-business a Business 24, včetně podpolí `?NN` pole `:86:` s VS/KS/SS a protistranou; každý symbol rozpozná podle předpony, ne podle pozice.

Nemá obrazovku ani nastavení. Instaluje se jako závislost modulu `account_statement_import_mt940`.
