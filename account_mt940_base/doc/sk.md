---
title: Formát výpisov MT940 / MultiCash — spoločný parser
summary: Čítanie výpisov SWIFT MT940 s českou štruktúrou poľa :86:, ktoré používa import výpisov MT940.
verified: 19.0.1.0.0
family: account_statement_import_mt940#format
---

Načíta výpisy SWIFT MT940 tak, ako ich české banky dodávajú cez MultiCash, X-business a Business 24, vrátane podpolí `?NN` poľa `:86:` s VS/KS/SS a protistranou; každý symbol rozpozná podľa predpony, nie podľa pozície.

Nemá obrazovku ani nastavenia. Inštaluje sa ako závislosť modulu `account_statement_import_mt940`.
