---
title: Czech Payroll (OCA)
summary: The Czech monthly payslip for the OCA payroll app on Odoo Community — pracovní poměr, DPP and DPČ, with dated statutory rates, time off and the annual tax reconciliation.
verified: 19.0.1.13.0
family: l10n_cz_hr_payroll_base#engines
---

A complete Czech salary structure for the OCA `payroll` app, *Czech Republic: Regular Pay* (`CZMONTHLY`): social and health insurance with the annual cap and the health minimum base, the income tax advance or the withholding tax on an agreement, the tax credits, the child tax benefit and bonus, holiday and obstacle pay at average earnings, sickness compensation, the employer's social insurance discount, garnishments and the meal allowance. It also ships the dated statutory figures the rules read, under *Payroll → Configuration → Rule Parameters*, Czech time-off types mapped to the payslip by a *Czech Payroll Code* (set on the time-off type form), and the annual tax reconciliation under *Payroll → CZ Annual Tax Reconciliation*. The Czech fields appear on the employee form, *Payroll* tab, and on the contract template form.

Install it on purpose; it brings in the engine-neutral base with the Czech employee fields and the annual leave accrual plans. For posting to the general ledger add the OCA accounting bridge; for wage surcharges the surcharges family.
