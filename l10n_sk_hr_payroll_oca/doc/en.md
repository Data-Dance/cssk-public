---
title: Slovak Payroll (OCA)
summary: The Slovak monthly payslip for the OCA payroll app on Odoo Community — a complete salary structure for a pracovný pomer and the three dohody.
verified: 19.0.1.26.0
family: l10n_sk_hr_payroll_base#engines
---

A complete Slovak salary structure for the OCA `payroll` app: four structures, one per employment form, sharing one rule set — social and health insurance, the tax base, the non-taxable part per taxpayer, the progressive income tax, the child tax bonus, holiday and obstacle pay at average earnings, employer sick pay, garnishments and the meal allowance. It also ships the dated rule parameters the rules read, Slovak time-off types with a *Slovak Payroll Code* and accrual plans, and the annual tax reconciliation. The Slovak fields appear on the employee form, *Payroll* tab, and on contract templates; the rule parameters are under *Payroll → Configuration → Rule Parameters*.

Install it on purpose; it needs the OCA `payroll` module and works on Odoo Community. For posting to the general ledger add the OCA accounting bridge; for wage surcharges the surcharges family.

## Retained monthly social-insurance bases {#social-bases}

The regular monthly calculation retains the exact base for each social-insurance fund together with the effective employment version, rates, dates, inputs and salary amounts. The same shared base helper is used by the salary rules and the retained evidence: agreement OOP is deducted before the applicable ceiling, accident insurance is uncapped and guarantee insurance does not use OOP. Employee and employer ceilings remain distinct for a partial month. A rounded premium is never divided by its rate to guess its assessment base.

Confirmation validates this source, including when automatic recomputation is disabled. Confirmed salary lines and source identity remain protected after cancellation; use a payroll correction rather than changing the original. Version edits and confirmation coordinate under PostgreSQL repeatable-read, including inserting another version. A native refund payslip remains available for bookkeeping; it is not automatically a complete replacement monthly declaration.

MVP reads the retained fund bases and employment interval. MVP and VPP both use the retained relationship when selecting regular versus irregular income, so editing today's HR card does not reroute historical pay. Missing old evidence requires an explicit reviewed compatibility adapter; existing generated XML is preserved. Allocation and correction adapters can override the source-policy hook and supply their own exact bases. A within-month change of insurance profile requires separate consolidation support; it is not silently combined into one profile. This public implementation verifies OCA payroll, not the proprietary Enterprise engine or authority acceptance.

A tax-relevant pension drawn on 1 January also affects monthly allowance eligibility. Record *Draws a tax-relevant pension* on the native version effective from the pension award date, using the retained taxpayer declaration. Monthly payroll reads the version in force on 1 January of its own year. A January pensioner receives no monthly NČZD even if the declaration is signed and the pension is small. A May 2026 award keeps the 2026 monthly allowance and removes it from January 2027, without editing the May version or preventing a December 2026 recomputation. Disability, widow's and orphan's pensions alone do not set this flag. A relevant insurance pension without the flag on the January version stops a monthly claim with a plain message before salary rules run. For a genuine midyear hire without a January version, or a rehire whose earlier employment ended before 1 January, the first version of the new employment records the January pension status declared at hiring. Do not backdate employment; a later award remains a later fact. A version later than the payslip or belonging to a later year cannot establish that status. Statutory parameters and tax bands remain unchanged.

The annual difference for a small pension is settled in RZD or the personal return. Review the yearly pension, including the 13th pension, for each annual reconciliation. *Pension at 1 January (yearly)* supplies its default from the January version; a reviewed correction on the reconciliation is retained. A positive version amount without the flag is refused, and RZD refuses a January flag without a positive reviewed yearly amount or an amount without that flag. The annual reduction follows [§ 11(6)](law:sk/2003/595#paragraf-11). Monthly eligibility follows [§ 35](law:sk/2003/595#paragraf-35) and [§ 36](law:sk/2003/595#paragraf-36), together with the [Financial Administration FAQ, questions 3, 7, 9](https://podpora.financnasprava.sk/260857-Nezdanite%C4%BEn%C3%A1-%C4%8Das%C5%A5-z%C3%A1kladu-dane-na-da%C5%88ovn%C3%ADka-za-rok-2026). Retroactive awards require the historical fact and the applicable correction procedure; posted payslips are not silently rewritten.

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

## Sickness compensation entitlement {#sickness-entitlement}

Approved PN dates determine calendar-day tiers, while the native shared `SICKNESS_COMPENSATION` applicability policy determines entitlement. A valid absence or entered DVZ alone does not confer insurance. Regular employment remains entitled even for an old-age pensioner; irregular agreements, student agreements and pensioner DoVP/DoPC agreements receive no employer sickness compensation. See [Act462/2003](law:sk/2003/462) and [Act461/2003](law:sk/2003/461). The statutory compensation is income-tax exempt under §5(7)(f) of Act595/2003, as confirmed by the [Financial Administration](https://podpora.financnasprava.sk/589698-N%C3%A1hrada-pr%C3%ADjmu-a-pr%C3%ADplatok-k-n%C3%A1hrade-pr%C3%ADjmu-pri-do%C4%8Dasnej-PN); its exclusion from taxable GROSS is retained. DVZ determination, missing/overlapping medical evidence and manual continuation inputs still require their separate review.

## Actual worked time in the average {#average-worked-time}

WORK100 is the gross scheduled time; separately recorded approved absence rows are deducted by absolute days and hours before applying the 21-day or168-hour threshold and wage/hour division. This follows the same absence-code taxonomy as BASIC, with identical results for either leave-sign setting. Refund direction remains applied once by the caller. An unsaved payslip preview excludes its persistent origin rather than passing a temporary NewId into the history domain.


For a prorated wage, the salary-rule category may still contain a fractional cent while the recorded GROSS and general ledger have the currency-rounded amount. The fund helper first derives that actual monetary income, then applies the statutory base deduction/cap and downward rounding. For example,765.217391 is recorded as765.22; its14% employer pension premium is107.13, not107.12.

Ordinary nonzero remuneration outside the employment period must use a reviewed historical income allocation; it cannot be retained as a regular monthly social-insurance source.
