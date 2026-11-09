---
title: Slovak Payroll (OCA)
summary: The Slovak monthly payslip for the OCA payroll app on Odoo Community — a complete salary structure for a pracovný pomer and the three dohody.
verified: 19.0.1.24.3
family: l10n_sk_hr_payroll_base#engines
---

A complete Slovak salary structure for the OCA `payroll` app: four structures, one per employment form, sharing one rule set — social and health insurance, the tax base, the non-taxable part per taxpayer, the progressive income tax, the child tax bonus, holiday and obstacle pay at average earnings, employer sick pay, garnishments and the meal allowance. It also ships the dated rule parameters the rules read, Slovak time-off types with a *Slovak Payroll Code* and accrual plans, and the annual tax reconciliation. The Slovak fields appear on the employee form, *Payroll* tab, and on contract templates; the rule parameters are under *Payroll → Configuration → Rule Parameters*.

Install it on purpose; it needs the OCA `payroll` module and works on Odoo Community. For posting to the general ledger add the OCA accounting bridge; for wage surcharges the surcharges family.

A tax-relevant pension drawn on 1 January also affects monthly allowance eligibility. Record *Draws a tax-relevant pension* on the native version effective from the pension award date, using the retained taxpayer declaration. Monthly payroll reads the version in force on 1 January of its own year. A January pensioner receives no monthly NČZD even if the declaration is signed and the pension is small. A May 2026 award keeps the 2026 monthly allowance and removes it from January 2027, without editing the May version or preventing a December 2026 recomputation. Disability, widow's and orphan's pensions alone do not set this flag. A relevant insurance pension without the flag on the January version stops a monthly claim with a plain message before salary rules run. For a genuine midyear hire without a January version, or a rehire whose earlier employment ended before 1 January, the first version of the new employment records the January pension status declared at hiring. Do not backdate employment; a later award remains a later fact. A version later than the payslip or belonging to a later year cannot establish that status. Statutory parameters and tax bands remain unchanged.

The annual difference for a small pension is settled in RZD or the personal return. Review the yearly pension, including the 13th pension, for each annual reconciliation. *Pension at 1 January (yearly)* supplies its default from the January version; a reviewed correction on the reconciliation is retained. A positive version amount without the flag is refused, and RZD refuses a January flag without a positive reviewed yearly amount or an amount without that flag. The annual reduction follows [§ 11(6)](law:sk/2003/595#paragraf-11). Monthly eligibility follows [§ 35](law:sk/2003/595#paragraf-35) and [§ 36](law:sk/2003/595#paragraf-36), together with the [Financial Administration FAQ, questions 3, 7, 9](https://podpora.financnasprava.sk/260857-Nezdanite%C4%BEn%C3%A1-%C4%8Das%C5%A5-z%C3%A1kladu-dane-na-da%C5%88ovn%C3%ADka-za-rok-2026). Retroactive awards require the historical fact and the applicable correction procedure; posted payslips are not silently rewritten.

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

## Actual worked time in the average {#average-worked-time}

WORK100 is the gross scheduled time; separately recorded approved absence rows are deducted by absolute days and hours before applying the 21-day or168-hour threshold and wage/hour division. This follows the same absence-code taxonomy as BASIC, with identical results for either leave-sign setting. Refund direction remains applied once by the caller. An unsaved payslip preview excludes its persistent origin rather than passing a temporary NewId into the history domain.