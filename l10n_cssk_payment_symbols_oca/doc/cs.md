---
title: Platební symboly CZ/SK — párování výpisů (OCA)
summary: Páruje přijaté platby s fakturami podle přesného variabilního symbolu v párování výpisů OCA.
verified: 19.0.1.0.0
family: l10n_cssk_payment_symbols#bank-matching
---

Přidá přesné porovnání variabilního symbolu do automatického párování v párovacím nástroji OCA (`account_reconcile_oca`), který se běžně používá v Odoo Community. Běží před vlastním párováním faktur v OCA, které porovnává popis platby s číslem faktury, a proto českou či slovenskou platbu, u níž plátce uvádí jen variabilní symbol, najde zřídka.

Nainstaluje se sám, je-li nainstalován modul platebních symbolů i `account_reconcile_oca`, a nemá žádná nastavení.
