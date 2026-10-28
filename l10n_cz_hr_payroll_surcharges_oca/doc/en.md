---
title: CZ Wage Surcharges (OCA)
summary: The Czech wage surcharges as salary rules of the OCA payroll app.
verified: 19.0.1.1.1
family: l10n_cz_hr_payroll_surcharges#engines
---

Creates the overtime, public-holiday, night, Saturday/Sunday and difficult-environment surcharges as salary rules of the OCA payroll app, each declaring its own input (`PRESCAS`, `SVATEK`, `NOCNI`, `VIKEND`, `ZTIZENE`) for the hours, and subtracts absences from the OCA engine's worked-days line where the minimum wage comparison needs it. Two more rules pay the wage for the overtime hours (*Overtime Wage (§ 114)*, from the `PRESCAS` input) and the minimum wage top-up (*Minimum Wage Top-up (§ 111)*). The rules are added to the Czech structure *Czech Republic: Regular Pay*. All rates and the arithmetic come from the surcharges base module.

Install it on purpose, together with the Czech OCA payroll; it does not install itself and has no settings of its own.
