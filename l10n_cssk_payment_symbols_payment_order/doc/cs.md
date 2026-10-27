---
title: Platební symboly CZ/SK — platební příkazy
summary: Přenáší variabilní, konstantní a specifický symbol dokladu na řádky platebních příkazů OCA.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#payment-orders
---

Když vznikne řádek platebního příkazu OCA (`account_payment_order`) z faktury, tento modul na něj přenese variabilní, konstantní a specifický symbol dokladu, aby je exportéry tuzemských bankovních souborů (ABO, Multicash) zapsaly do souboru jako strukturované symboly.

Nainstaluje se sám, je-li nainstalován modul platebních symbolů i `account_payment_order`. Vlastní obrazovku nemá.
