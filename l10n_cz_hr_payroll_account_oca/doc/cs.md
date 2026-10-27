---
title: Česká mzdová agenda — účetnictví (OCA)
summary: Zaúčtuje české výplatní pásky z aplikace OCA payroll podle české účtové osnovy.
verified: 19.0.1.1.1
family: l10n_cz_hr_payroll_base#accounting
---

Nastaví českým mzdovým pravidlům účty české účtové osnovy — 521 hrubá mzda a náhrada mzdy při nemoci, 524 pojistné zaměstnavatele snížené o slevu na pojistném, 527 stravenkový paušál, 331 čistá mzda, 336 sociální a zdravotní pojištění, 342 daň z příjmů snížená o vyplacený daňový bonus a přeplatek z ročního zúčtování, 379 exekuční a ostatní srážky, 333 proplacení výdajů — každému pravidlu účet na stranu Má dáti i Dal, takže potvrzená výplatní páska zaúčtuje vyrovnaný doklad. Založí také všeobecný deník *Salaries* (kód `SLR`); vyberte ho na smlouvě jako **Deník platů**.

Instaluje se ručně a vyžaduje modul OCA `payroll_account` a českou mzdovou agendu. Účty nastaví při instalaci u společností, které již mají českou účtovou osnovu, a u každé společnosti, která českou osnovu načte později.
