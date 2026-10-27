---
title: Platobné symboly CZ/SK — párovanie výpisov (OCA)
summary: Páruje prijaté platby s faktúrami podľa presného variabilného symbolu v párovaní výpisov OCA.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#bank-matching
---

Pridá presné porovnanie variabilného symbolu do automatického párovania v párovacom nástroji OCA (`account_reconcile_oca`), ktorý sa bežne používa v Odoo Community. Beží pred vlastným párovaním faktúr v OCA, ktoré porovnáva popis platby s číslom faktúry, a preto slovenskú či českú platbu, pri ktorej platiteľ uvádza len variabilný symbol, nájde zriedka.

Nainštaluje sa sám, keď je nainštalovaný modul platobných symbolov aj `account_reconcile_oca`, a nemá žiadne nastavenia.
