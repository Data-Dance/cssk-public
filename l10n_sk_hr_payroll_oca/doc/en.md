---
title: Slovak Payroll (OCA)
summary: The Slovak monthly payslip for the OCA payroll app on Odoo Community — a complete salary structure for a pracovný pomer and the three dohody.
verified: 19.0.1.24.6
family: l10n_sk_hr_payroll_base#engines
---

A complete Slovak salary structure for the OCA `payroll` app: four structures, one per employment form, sharing one rule set — social and health insurance, the tax base, the non-taxable part per taxpayer, the progressive income tax, the child tax bonus, holiday and obstacle pay at average earnings, employer sick pay, garnishments and the meal allowance. It also ships the dated rule parameters the rules read, Slovak time-off types with a *Slovak Payroll Code* and accrual plans, and the annual tax reconciliation. The Slovak fields appear on the employee form, *Payroll* tab, and on contract templates; the rule parameters are under *Payroll → Configuration → Rule Parameters*.

Install it on purpose; it needs the OCA `payroll` module and works on Odoo Community. For posting to the general ledger add the OCA accounting bridge; for wage surcharges the surcharges family.

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

## Dated sickness compensation {#sickness-dates}

Employer compensation stops at the end of the insured relationship, even if the
validated PN continues. Preserve the actual illness onset when clipping that
payment window: the first-rate days do not restart with a new month. Each native
PN episode uses the statutory employer-day limit, rates and maximum daily base
at its onset. A PN beginning in 2025 retains the ten-day regime in 2026.

The employer daily base is truncated to four decimals. The resulting monthly
compensation is rounded upward to eurocents under section 10(2) of Act 462/2003;
Decimal arithmetic avoids an extra cent from binary-float accumulation. The
existing manual fallback uses the same monetary rounding. Its continuation
facts and the determination of the supplied DVZ still require review; a manual
day count alone does not reconstruct a medical episode.

References: [SP transition guidance](https://www.socpoist.sk/node/6844),
[MPSVR daily base](https://www.employment.gov.sk/sk/socialne-poistenie-dochodkovy-system/nahrada-prijmu-pri-pracovnej-neschopnosti/denny-vymeriavaci-zaklad.html)
and [Act 462/2003](law:sk/2003/462).

## Starter absence settings on upgrade {#leave-upgrade}

The supplied Slovak absence types are installation defaults. A module upgrade preserves the company's reviewed settings and approved absence dates. Rewriting even the same request unit can recompute dates and invoke the native protection of approved leave. The starter XML therefore uses Odoo's noupdate policy. A future change to an existing default needs an explicit migration that reviews its effect on existing absences; ordinary updates do not silently reset company configuration. The regression reloads the actual data file with approved PN and ordinary holiday records and verifies their dates, state, duration and the company's type name.

## Meal allowance from December 2026

[Notice 255/2026 Z. z.](https://employment.gov.sk/showdoc.do?docid=60223) raises the 5–12 hour domestic meal allowance to EUR 9.80 from 1 December 2026. The dated payroll parameter also applies in January 2027 until a later rate takes effect. With 20 meal days and the default 55% contribution, payroll records EUR 107.80 employer contribution; a minimum 75% voucher leaves EUR 39.20 employee share. November 2026 still uses EUR 9.30 and EUR 102.40 employer contribution. Explicit contractual contributions retain their existing priority. Travel rates are supplied by the travel module separately.
