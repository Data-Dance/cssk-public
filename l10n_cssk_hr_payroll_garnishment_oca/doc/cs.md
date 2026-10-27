---
title: Srážky ze mzdy CZ/SK (mzdy OCA)
summary: Napojí evidenci srážek ze mzdy na mzdovou aplikaci OCA, aby potvrzené výplatní pásky zaznamenaly srážky ke každému nařízení.
verified: 19.0.1.0.2
family: l10n_cssk_hr_payroll_garnishment_base#engines
---

Napojí evidenci srážek ze mzdy na mzdovou aplikaci OCA. Při potvrzení výplatní pásky zaznamená jednu srážku za každé probíhající nařízení, spočítanou ze stejné čisté mzdy, jakou páska ukázala; zrušení pásky nebo její vrácení do konceptu smaže srážky, které ještě nebyly poukázány, a pásku, jejíž srážka už byla poukázána, do konceptu vrátit ani zrušit nelze. Páska dostane kartu *Garnishments* se svými srážkami.

Nainstaluje se sám, je-li nainstalována mzdová aplikace OCA (`payroll`) i evidence srážek, a nemá žádná nastavení. Samotnou srážku počítá pravidlo *Wage Garnishment* českých nebo slovenských mezd.
