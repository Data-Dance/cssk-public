---
title: Formát výpisů GPC — společný parser
summary: Čtení bankovních výpisů GPC, které sdílejí importy GPC pro Community i Enterprise.
verified: 19.0.1.0.0
family: account_statement_import_gpc#format
---

Načte elektronické výpisy GPC — záhlaví `074`, transakce `075` a řádky zpráv `076`/`078`/`079` — do výpisů se zůstatky, účty protistrany a symboly VS/KS/SS, aby import GPC v Community i v Enterprise četl každý soubor stejně.

Nemá obrazovku ani nastavení. Instaluje se jako závislost modulu `account_statement_import_gpc` nebo `account_statement_import_gpc_ee`.
