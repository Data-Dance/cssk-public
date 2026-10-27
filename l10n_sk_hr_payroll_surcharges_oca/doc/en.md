---
title: SK Wage Surcharges (OCA)
summary: The Slovak wage surcharges and the minimum wage top-up as salary rules of the OCA payroll app.
verified: 19.0.1.0.3
family: l10n_sk_hr_payroll_surcharges#engines
---

Adds the night, Saturday, Sunday, public-holiday, overtime, difficult-conditions and standby surcharges, the overtime pay and the minimum wage top-up as salary rules of the Slovak OCA structures. Each rule declares its own payslip input (*Night hours*, *Saturday hours*, …) for the hours. It also accounts for the OCA engine reporting absences as separate negative worked-days lines, so the top-up compares the wage with the hours actually worked. All rates and the arithmetic come from the surcharges base module.

It installs itself when the Slovak OCA payroll and the surcharges base module are both installed, and has no settings of its own. If the accounting bridge is already installed, it gives its rules the wage account 521000.
