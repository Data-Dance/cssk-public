---
title: CZ/SK Wage Garnishments (OCA Payroll)
summary: Connects the wage-garnishment register to the OCA payroll app, so confirmed payslips record their deductions per order.
verified: 19.0.1.0.2
family: l10n_cssk_hr_payroll_garnishment_base#engines
---

Connects the garnishment register to the OCA payroll app. When a payslip is confirmed it records one deduction per running order, computed from the same net wage the payslip showed; cancelling the payslip or setting it back to draft deletes the deductions not yet remitted, and a payslip whose deduction has been remitted cannot be set back to draft or cancelled. The payslip gets a *Garnishments* tab listing its deductions.

It installs itself when both the OCA payroll app (`payroll`) and the garnishment register are installed, and has no settings. The deduction itself comes from the *Wage Garnishment* rule of the Czech or Slovak payroll.
