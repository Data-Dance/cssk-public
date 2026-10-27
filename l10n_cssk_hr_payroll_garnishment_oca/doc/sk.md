---
title: Zrážky zo mzdy CZ/SK (mzdy OCA)
summary: Napojí evidenciu exekučných zrážok na mzdovú aplikáciu OCA, aby potvrdené výplatné pásky zaznamenali zrážky ku každému príkazu.
verified: 19.0.1.0.2
family: l10n_cssk_hr_payroll_garnishment_base#engines
---

Napojí evidenciu zrážok zo mzdy na mzdovú aplikáciu OCA. Pri potvrdení výplatnej pásky zaznamená jednu zrážku za každý prebiehajúci príkaz, vypočítanú z tej istej čistej mzdy, akú páska ukázala; zrušenie pásky alebo jej vrátenie do konceptu vymaže zrážky, ktoré ešte neboli poukázané, a pásku, ktorej zrážka už bola poukázaná, do konceptu vrátiť ani zrušiť nemožno. Páska dostane kartu *Garnishments* so svojimi zrážkami.

Nainštaluje sa sám, keď je nainštalovaná mzdová aplikácia OCA (`payroll`) aj evidencia zrážok, a nemá žiadne nastavenia. Samotnú zrážku počíta pravidlo *Wage Garnishment* slovenských alebo českých miezd.
