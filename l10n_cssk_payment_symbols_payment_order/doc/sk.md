---
title: Platobné symboly CZ/SK — platobné príkazy
summary: Prenáša variabilný, konštantný a špecifický symbol dokladu na riadky platobných príkazov OCA.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#payment-orders
---

Keď vznikne riadok platobného príkazu OCA (`account_payment_order`) z faktúry, tento modul naň prenesie variabilný, konštantný a špecifický symbol dokladu, aby ich exportéry tuzemských bankových súborov (ABO, Multicash) zapísali do súboru ako štruktúrované symboly.

Nainštaluje sa sám, keď je nainštalovaný modul platobných symbolov aj `account_payment_order`. Vlastnú obrazovku nemá.
