---
title: Slovak Payroll (OCA)
summary: The Slovak monthly payslip for the OCA payroll app on Odoo Community — a complete salary structure for a pracovný pomer and the three dohody.
verified: 19.0.1.24.0
family: l10n_sk_hr_payroll_base#engines
---

A complete Slovak salary structure for the OCA `payroll` app: four structures, one per employment form, sharing one rule set — social and health insurance, the tax base, the non-taxable part per taxpayer, the progressive income tax, the child tax bonus, holiday and obstacle pay at average earnings, employer sick pay, garnishments and the meal allowance. It also ships the dated rule parameters the rules read, Slovak time-off types with a *Slovak Payroll Code* and accrual plans, and the annual tax reconciliation. The Slovak fields appear on the employee form, *Payroll* tab, and on contract templates; the rule parameters are under *Payroll → Configuration → Rule Parameters*.

Install it on purpose; it needs the OCA `payroll` module and works on Odoo Community. For posting to the general ledger add the OCA accounting bridge; for wage surcharges the surcharges family.

A pension drawn on 1 January counts in the annual tax reconciliation only. Enter its yearly amount, 13th pension included, as *Pension at 1 January (yearly)* on the contract version; the reconciliation takes it from the version in force on 1 January and reduces the non-taxable part per taxpayer by it, to nothing when the pension is higher ([§ 11 ods. 6](law:sk/2003/595#paragraf-11)). The monthly advances keep the full allowance, as [§ 35 ods. 1](law:sk/2003/595#paragraf-35) requires.

## Annual reconciliation sources

Gathering uses confirmed (`done`) payslips of the reconciliation company and
employee, keyed by period end in the selected year. Draft, waiting and cancelled
calculations and the selected settlement payslip are excluded. This aligns the
source selection with payroll declarations. It does not establish actual
payment, statutory tax-year attribution or eligibility for employer RZD;
those still require the relevant payroll records and legal review. Extensions
retaining explicit financial replacements must also filter superseded sources.
## Average earnings sources {#average-sources}

For the determining quarter, actual average hourly earnings are used when the
employee worked at least **21 days or 168 hours**. Short part-time days count
as days; the test is not hours alone. Below both thresholds, the existing
probable-earnings fallback applies. Only confirmed payslips of the same company
and employment start supply wage and worked time. A wage-version change within
that employment keeps its history; a genuine rehire does not inherit the old
employment's average. Simultaneous employments use separate employee records,
as required by the native HR contract model.

Native credit notes subtract both their counted wage and worked time. A
refund/replacement pair therefore supplies the replacement's actual amounts
rather than two copies of the original time. Confirmed wages are distinct
from evidence of bank payment.

The default counted wage remains GROSS less the existing wage-replacement
codes. Extensions can refine `_l10n_sk_average_counted_wage`, select effective
sources through `_l10n_sk_average_payslips`, and extend worked time through
`_l10n_sk_average_worked_time`. Tax/insurance GROSS alone does not establish the
Labour Code classification of a noncash benefit. This fix does not implement
allocation of remuneration for periods longer than a quarter (§ 134 ods. 6),
all minimum-wage grades or an independently reviewed probable-wage input.

Source: [Labour Code § 134](https://static.slov-lex.sk/static/SK/ZZ/2001/311/20261202.html),
including paragraphs 1–7, verified against the published version applying from
2 December 2026. Review future amendments for each actual payroll period.
