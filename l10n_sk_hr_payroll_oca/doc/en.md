---
title: Slovak Payroll (OCA)
summary: The Slovak monthly payslip for the OCA payroll app on Odoo Community — a complete salary structure for a pracovný pomer and the three dohody.
verified: 19.0.1.22.1
family: l10n_sk_hr_payroll_base#engines
---

A complete Slovak salary structure for the OCA `payroll` app: four structures, one per employment form, sharing one rule set — social and health insurance, the tax base, the non-taxable part per taxpayer, the progressive income tax, the child tax bonus, holiday and obstacle pay at average earnings, employer sick pay, garnishments and the meal allowance. It also ships the dated rule parameters the rules read, Slovak time-off types with a *Slovak Payroll Code* and accrual plans, and the annual tax reconciliation. The Slovak fields appear on the employee form, *Payroll* tab, and on contract templates; the rule parameters are under *Payroll → Configuration → Rule Parameters*.

Install it on purpose; it needs the OCA `payroll` module and works on Odoo Community. For posting to the general ledger add the OCA accounting bridge; for wage surcharges the surcharges family.

A pension drawn on 1 January counts in the annual tax reconciliation only. Enter its yearly amount, 13th pension included, as *Pension at 1 January (yearly)* on the contract version; the reconciliation takes it from the version in force on 1 January and reduces the non-taxable part per taxpayer by it, to nothing when the pension is higher ([§ 11 ods. 6](law:sk/2003/595#paragraf-11)). The monthly advances keep the full allowance, as [§ 35 ods. 1](law:sk/2003/595#paragraf-35) requires.

## Hourly wage and approved absence

For hourly pay, BASIC covers the worked hours after approved absences have
been removed. Paid leave receives its separate average-earnings compensation
under [§116](law:sk/2001/311#paragraf-116), so those hours are not also paid
as ordinary hourly work. Both supported signs of the absence lines give the
same amount. For example, 176 scheduled hours at EUR 20/h with 8 hours of leave
give BASIC 3360 and leave compensation 160 when the reviewed average is 20/h.

## Annual reconciliation sources

Gathering uses confirmed (`done`) payslips of the reconciliation company and
employee, keyed by period end in the selected year. Draft, waiting and cancelled
calculations and the selected settlement payslip are excluded. This aligns the
source selection with payroll declarations. It does not establish actual
payment, statutory tax-year attribution or eligibility for employer RZD;
those still require the relevant payroll records and legal review. Extensions
retaining explicit financial replacements must also filter superseded sources.
