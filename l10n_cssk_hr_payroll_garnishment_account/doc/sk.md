---
title: Zrážky zo mzdy CZ/SK — poukázanie
summary: Zo zrážok každého exekučného príkazu vytvorí zaúčtovaný záväzok voči exekútorovi alebo oprávnenému so spisovou značkou ako variabilným symbolom, pripravený na platobný príkaz a bankový súbor.
verified: 19.0.1.1.2
family: l10n_cssk_hr_payroll_garnishment_base#accounting
---

Presunie zrážky zo súhrnného záväzku, ktorý účtuje mzdový doklad, na príjemcu: jeden zaúčtovaný doklad za každý príkaz, na ťarchu účtu *Garnishment Liability Account* a v prospech záväzku voči exekútorovi alebo oprávnenému, so symbolmi a bankovým účtom príjemcu z príkazu. Otvorený záväzok sa potom uhradí ako ktorýkoľvek dodávateľ. Poukazuje sa v *Zamestnanci → Garnishments → Remit to Payees* alebo tlačidlom *Remit to Payee* na označených zrážkach; poukázané zrážky sa už nedajú vymazať a ich výplatnú pásku nemožno vrátiť do konceptu.

Nainštaluje sa sám, keď sú nainštalované `account`, evidencia zrážok a modul platobných symbolov. *Garnishment Remittance Journal* a *Garnishment Liability Account* nastavte v *Účtovníctvo → Konfigurácia → Nastavenia*, blok *Wage Garnishments*. Poukázanie môže vykonávať *Administrátor* účtovníctva a používatelia so skupinou *Show Full Accounting Features*.
