---
title: Formát KB BEST — společné sestavovače a parser
summary: Formát BEST Komerční banky — tuzemské a zahraniční platební záznamy i elektronický výpis — sdílený exportem plateb a importem výpisů KB BEST.
verified: 19.0.1.0.0
family: account_payment_kb_best#format
---

Zapisuje platební soubory BEST (tuzemské záznamy `01`, zahraniční a SEPA záznamy `02` s adresou `03`) a čte výpisy BEST (obraty `51`, transakce `52`), přičemž uplatňuje pravidla KB dřív než banka: jen účet plátce u KB, jedinečná denní pořadová čísla, odmítané konstantní symboly, pravidla pro SEPA a poplatky do EHP.

Nemá obrazovku ani nastavení. Instaluje se jako závislost modulů `account_payment_kb_best` a `account_statement_import_kb_best`.
