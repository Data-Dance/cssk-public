---
title: Srážky ze mzdy CZ/SK — poukázání
summary: Ze srážek každého nařízení vytvoří zaúčtovaný závazek vůči exekutorovi nebo oprávněnému se spisovou značkou jako variabilním symbolem, připravený pro platební příkaz a bankovní soubor.
verified: 19.0.1.1.2
family: l10n_cssk_hr_payroll_garnishment_base#accounting
---

Přesune srážky ze souhrnného závazku, který účtuje mzdový doklad, na příjemce: jeden zaúčtovaný doklad za každé nařízení, na vrub účtu *Garnishment Liability Account* a ve prospěch závazku vůči exekutorovi nebo oprávněnému, se symboly a bankovním účtem příjemce z nařízení. Otevřený závazek se pak uhradí jako kterýkoli dodavatel. Poukazuje se v *Zaměstnanci → Garnishments → Remit to Payees* nebo tlačítkem *Remit to Payee* na označených srážkách; poukázané srážky už nelze smazat a jejich výplatní pásku nelze vrátit do konceptu.

Nainstaluje se sám, jsou-li nainstalovány `account`, evidence srážek a modul platebních symbolů. *Garnishment Remittance Journal* a *Garnishment Liability Account* nastavte v *Účetnictví → Konfigurace → Nastavení*, blok *Wage Garnishments*. Poukázání může provádět *Administrátor* účetnictví a uživatelé se skupinou *Show Full Accounting Features*.
