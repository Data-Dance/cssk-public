---
title: Slovak Payroll (OCA)
summary: The Slovak monthly payslip for the OCA payroll app on Odoo Community — a complete salary structure for a pracovný pomer and the three dohody.
verified: 19.0.1.23.0
family: l10n_sk_hr_payroll_base#engines
---

A complete Slovak salary structure for the OCA `payroll` app: four structures, one per employment form, sharing one rule set — social and health insurance, the tax base, the non-taxable part per taxpayer, the progressive income tax, the child tax bonus, holiday and obstacle pay at average earnings, employer sick pay, garnishments and the meal allowance. It also ships the dated rule parameters the rules read, Slovak time-off types with a *Slovak Payroll Code* and accrual plans, and the annual tax reconciliation. The Slovak fields appear on the employee form, *Payroll* tab, and on contract templates; the rule parameters are under *Payroll → Configuration → Rule Parameters*.

Install it on purpose; it needs the OCA `payroll` module and works on Odoo Community. For posting to the general ledger add the OCA accounting bridge; for wage surcharges the surcharges family.

A tax-relevant pension drawn on 1 January also affects monthly allowance eligibility. Record *Draws a tax-relevant pension* on the native version effective from the pension award date, using the retained taxpayer declaration. Monthly payroll reads the version in force on 1 January of its own year. A January pensioner receives no monthly NČZD even if the declaration is signed and the pension is small. A May 2026 award keeps the 2026 monthly allowance and removes it from January 2027, without editing the May version or preventing a December 2026 recomputation. Disability, widow's and orphan's pensions alone do not set this flag. A relevant insurance pension without the flag on the January version stops a monthly claim with a plain message before salary rules run. For a genuine midyear hire without a January version, the first version records the January pension status declared at hiring. Do not backdate employment; a later award remains a later fact. A version later than the payslip or belonging to a later year cannot establish that status. Statutory parameters and tax bands remain unchanged.

The annual difference for a small pension is settled in RZD or the personal return. Review the yearly pension, including the 13th pension, for each annual reconciliation. *Pension at 1 January (yearly)* supplies its default from the January version; a reviewed correction on the reconciliation is retained. A positive version amount without the flag is refused, and RZD refuses a January flag without a positive reviewed yearly amount or an amount without that flag. The annual reduction follows [§ 11(6)](law:sk/2003/595#paragraf-11). Monthly eligibility follows [§ 35](law:sk/2003/595#paragraf-35) and [§ 36](law:sk/2003/595#paragraf-36), together with the [Financial Administration FAQ, questions 3, 7, 9](https://podpora.financnasprava.sk/260857-Nezdanite%C4%BEn%C3%A1-%C4%8Das%C5%A5-z%C3%A1kladu-dane-na-da%C5%88ovn%C3%ADka-za-rok-2026). Retroactive awards require the historical fact and the applicable correction procedure; posted payslips are not silently rewritten.

## Annual reconciliation sources

Gathering uses confirmed (`done`) payslips of the reconciliation company and
employee, keyed by period end in the selected year. Draft, waiting and cancelled
calculations and the selected settlement payslip are excluded. This aligns the
source selection with payroll declarations. It does not establish actual
payment, statutory tax-year attribution or eligibility for employer RZD;
those still require the relevant payroll records and legal review. Extensions
retaining explicit financial replacements must also filter superseded sources.
