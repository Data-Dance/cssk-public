---
title: Czech Payroll
summary: The Czech payroll family in one place — the monthly payslip for a pracovní poměr, DPP and DPČ on either the OCA payroll app or Odoo Enterprise Payroll, with dated statutory rates, time off, the annual tax reconciliation and posting to the general ledger.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Czech payroll is delivered as a family of modules. This page describes the
family as a whole; the individual modules have short pages that point back
here.

| Module | What it does |
|---|---|
| [module:l10n_cz_hr_payroll_base](module:l10n_cz_hr_payroll_base) (this module) | The Czech employee data (agreement type, taxpayer declaration, children, insurance flags) and the statutory annual leave accrual plans. Engine-neutral, no screens of its own. |
| [module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca) | The Czech payslip on the **OCA payroll app** (`payroll`), for Odoo Community. |
| [module:l10n_cz_hr_payroll_ee](module:l10n_cz_hr_payroll_ee) | The same payslip on **Odoo Enterprise Payroll** (`hr_payroll`). Odoo has no Czech payroll of its own, so this is a complete localization, not an overlay. |
| [module:l10n_cz_hr_payroll_account_oca](module:l10n_cz_hr_payroll_account_oca), [module:l10n_cz_hr_payroll_account_ee](module:l10n_cz_hr_payroll_account_ee) | Posting payslips to the Czech chart of accounts, one per engine. |
| [module:l10n_cz_hr_payroll_surcharges](module:l10n_cz_hr_payroll_surcharges) | Wage surcharges (*příplatky*) for overtime, public holidays, night, weekend and difficult-environment work. |
| [module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base) | The register of wage garnishment orders (*srážky ze mzdy*), shared with Slovakia. |
| The statutory reports | See [Reports to the authorities](#declarations). |

The base module holds what does not depend on the payroll engine: the Czech
fields of the employee's contract and the annual leave accrual plans. It
installs automatically as a dependency of the engine modules, and you meet it
only through them. Each engine module carries its own salary structure, rules,
statutory figures, time-off types and screens.

## Choosing an engine {#engines}

Both engines run the same salary rules on the same dated figures. The choice
is about which payroll application you run, not about the Czech rules.

| | OCA (`_oca`) | Enterprise (`_ee`) |
|---|---|---|
| Payroll app | OCA `payroll`, works on Community | Odoo Enterprise *Payroll* (`hr_payroll`) |
| Installs | on purpose | automatically, once Enterprise *Payroll* and its time-off integration are installed |
| Salary structure | *Czech Republic: Regular Pay* (`CZMONTHLY`) | the same, under the structure type *Czech Republic: Employee* |
| Czech fields shown on | the employee form, *Payroll* tab, group **Czech Payroll**, and the contract template form | the employee form, *Payroll* tab, group **Czech Payroll**, and the contract template form |
| Absences reach the payslip through | the **Czech Payroll Code** on the time-off type | work entry types (*CZHOLIDAY*, *CZSICK*, …) |
| Basic wage for a partial month | the contract wage × worked hours ÷ scheduled hours | Odoo's own prorating by work entries |
| Hours and amounts entered by hand | an *Other Inputs* line with the input **code** typed in | an *Other Input* of the matching input type, or a salary adjustment |
| Statutory rates visible at | *Payroll → Configuration → Rule Parameters* | *Payroll → Configuration → Salary → Rule Parameters* |
| Payslip PDF | the OCA standard | *CZ: Payslip*, printed in the employee's language |

The employment form is not a separate structure on either engine. It is the
**Agreement Type** field on the contract: *Standard employment*, *DPP
(agreement to perform work)* or *DPČ (agreement to perform working
activity)*.

## Legal background {#legal}

The figures the payslip uses come from these acts. Paragraph references were
checked against the consolidated texts in force in October 2026.

- **Social insurance.** The employee pays 7.1 % (6.5 % pension, 0.6 %
  sickness) and the employer 24.8 % (21.5 % pension, 2.1 % sickness, 1.2 %
  employment policy) under
  [§ 7 of Act 589/1992 Sb.](law:cz/1992/589). The annual assessment base is
  capped at 48 times the average wage
  ([§ 15a](law:cz/1992/589)). The employer's discount of 5 % of the
  assessment base for eligible part-time employees is
  [§ 7a and § 7b](law:cz/1992/589).
- **Health insurance** is 13.5 % of the assessment base
  ([§ 2 of Act 592/1992 Sb.](law:cz/1992/592)), rounded up to whole crowns
  per employee, one third paid by the employee
  ([§ 9 odst. 2 of Act 48/1997 Sb.](law:cz/1997/48)). The minimum assessment
  base is the minimum wage, reduced by calendar days for a partial month of
  employment and for days of important personal obstacles such as sickness
  ([§ 3 odst. 6 and 9](law:cz/1992/592)). An employee below it pays 13.5 %
  of the difference, unless the shortfall comes from an obstacle on the
  employer's side, which the employer pays ([§ 3 odst. 10](law:cz/1992/592));
  the minimum base does not apply to the persons listed in § 3 odst. 8, among
  them ZTP and ZTP/P card holders and those for whom the state pays.
- **Agreements.** A DPP is sickness-insured in a month in which its income
  reaches 25 % of the average wage rounded down to 500 Kč
  ([§ 7a of Act 187/2006 Sb.](law:cz/2006/187)); a DPČ, like any other
  employment, once the income reaches the *rozhodný příjem*
  ([§ 6 odst. 2](law:cz/2006/187)). Below those amounts, and without a
  signed declaration, the income is taxed by a final withholding tax
  ([§ 6 odst. 4 of the Income Tax Act](law:cz/1992/586)).
- **Income tax.** The monthly advance is 15 % of the base and 23 % of the
  part above three times the average wage; the base is rounded up to whole
  hundreds of crowns ([§ 38h odst. 1 and 2](law:cz/1992/586)). The tax
  credits are [§ 35ba](law:cz/1992/586), the child tax benefit and bonus
  [§ 35c and § 35d](law:cz/1992/586); a monthly bonus is paid only when that
  month's income reaches half the minimum wage. The declaration
  (*prohlášení poplatníka*) is made within 30 days of joining and by
  15 February each year ([§ 38k odst. 4](law:cz/1992/586)). The annual
  reconciliation is [§ 38ch](law:cz/1992/586).
- **Meal allowance.** A *stravenkový paušál* is tax-exempt up to 70 % of the
  upper limit of the meal allowance for a 5–12 hour business trip
  ([§ 6 odst. 9 písm. b)](law:cz/1992/586)).
- **Minimum wage and wage replacements.** The minimum wage is set under
  [§ 111 of the Labour Code](law:cz/2006/262) and announced by an MPSV
  communication (for 2026, No. 356/2025 Sb.). A wage below it is topped up
  with a *doplatek*, compared per hour unless the monthly minimum wage was
  agreed in advance; overtime pay and surcharges do not count towards it
  ([§ 111 odst. 1 and 2](law:cz/2006/262)). An overtime hour is paid its
  wage plus a surcharge ([§ 114 odst. 1](law:cz/2006/262)). Holiday is paid at average
  earnings ([§ 222](law:cz/2006/262)); employer-side obstacles at at least
  80 % (downtime) or 60 % (weather) ([§ 207](law:cz/2006/262)), 100 % for
  other reasons ([§ 208](law:cz/2006/262)) and at least 60 % for short-time
  working only where a union agreement or internal rule says so
  ([§ 209](law:cz/2006/262)). Sick pay for the first 14 calendar days of
  incapacity is 60 % of reduced average earnings, the reduction thresholds
  being the sickness-insurance ones multiplied by 0.175 and rounded up to the
  haléř ([§ 192](law:cz/2006/262)); it is taxed as employment income but
  carries no insurance. Average earnings are §§ 351–362.
- **Annual leave** is at least four weeks a year
  ([§ 212](law:cz/2006/262)), accrued in hours by worked weeks
  ([§ 213](law:cz/2006/262)); untaken leave must be scheduled by the end of
  the following year ([§ 218](law:cz/2006/262)).

## Setting it up {#setup}

1. Install the engine module: on Community,
   [module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca); on
   Enterprise, [module:l10n_cz_hr_payroll_ee](module:l10n_cz_hr_payroll_ee)
   installs itself with *Payroll*. Add the accounting bridge if payslips
   should be posted (see [Posting to the general ledger](#accounting)).
2. The company must be in the Czech Republic. The Czech salary structure,
   time-off types and (on Enterprise) the Czech employee fields are visible
   only to Czech companies.
3. Give each employee's contract the Czech salary structure (OCA) or the
   structure type *Czech Republic: Employee* (Enterprise), and fill in the
   Czech data described below.
4. On Enterprise, check the figures under *Payroll → Configuration → Salary →
   Rule Parameters* before the first payslip of a new year.

## Employee and contract data {#employees}

| Field | What it does |
|---|---|
| Agreement Type | *Standard employment*, *DPP* or *DPČ*. Decides the insurance thresholds and when the withholding tax applies. |
| Taxpayer declaration signed | The employee signed the *prohlášení poplatníka* with this employer: the monthly tax credits and the child tax benefit are applied, and an agreement below the threshold is taxed by advance instead of by withholding. |
| Employee Holds ZTP/P, Invalidity Degree | Add the ZTP/P credit, or the basic (I/II) or extended (III) disability credit. |
| State-insured person | The health insurance minimum base is not applied. Tick it only when one of the § 3 odst. 8 exemptions lasts the whole month. |
| Meal allowance / shift | The *stravenkový paušál* per shift, capped at the tax-exempt limit and paid for each worked day. |
| Average hourly earnings | Overrides the computed average hourly earnings (never below the hourly minimum wage). Leave empty to let the payslip compute it. |
| Garnishment dependents | Dependants raising the non-seizable amount when a garnishment is entered as a payslip input. |
| Social insurance discount category | One of the § 7a categories for the employer's 5 % discount. |
| Children (1st tier), (2nd tier), (3rd+ tier), of which ZTP/P Children | Number of children for the child tax benefit, by order. |

## How the payslip is computed {#payslip}

In the order the rules run:

1. **Basic Salary.** The contract wage, reduced for every absence in the
   period.
2. **Wage surcharges** and the **Overtime Wage** for overtime hours, when the
   surcharges family is installed.
3. **Wage replacements** at average hourly earnings: *Holiday Pay*, *Paid
   Obstacle* (doctor, escort, blood donation, public office and the other
   § 199–206 reasons) and *Employer Work Obstacle (§§ 207–209)* at 80, 60,
   100 % (short-time working: the company's agreed rate, 100 % by default).
   Average hourly earnings are the basic wage of the validated
   payslips of the previous calendar quarter divided by their worked hours;
   without such a quarter, the contract wage over the period's scheduled
   hours; never less than the hourly minimum wage.
4. **Sickness Compensation**: 60 % of average hourly earnings reduced by the
   three reduction thresholds (90 / 60 / 30 %), for the hours of sick leave
   that fall in the first 14 calendar days of the incapacity (or the *Sick
   Hours* input), rounded up to whole crowns. Consecutive sick-leave requests
   count as one incapacity. It is kept out of gross pay, so it carries no
   insurance, but it is part of the tax base and of net pay.
5. **Minimum Wage Top-up**, when the surcharges family is installed (see its
   page), then **Gross Salary.**
6. **Social Insurance** employee and employer, on gross pay up to what
   remains of the annual cap after the year's earlier validated payslips.
   **Social Insurance Discount (Employer)** for an eligible employee in
   standard employment: gross pay at most 1.5 times the average wage and at
   most 1.15 % of it per hour (hours worked and hours paid as a wage
   replacement); except under 21, also an agreed 8–30 hours a week and at
   most 138 hours in the month. It lowers the employer cost but not the
   premium.
7. **Health Insurance**: 13.5 % of gross pay rounded up to whole crowns; the
   employee pays one third, rounded up, and the employer the rest. When gross
   pay of a standard employee is below the minimum base — the minimum wage,
   reduced by calendar days outside the employment and of sickness, family
   care, paid personal obstacles and maternity or parental leave — the
   employee also pays 13.5 % of the difference. The employer pays it instead
   when an employer-side obstacle is on the payslip; nobody pays it for a
   state-insured person or a ZTP/P card holder.
8. Agreements below their threshold pay neither insurance.
9. **Tax Base** = gross pay plus sickness compensation. **Income Tax Advance**: the base rounded up to
   whole hundreds of crowns, 15 % up to the monthly threshold and 23 % above.
   **Withholding Tax** instead for an agreement below its threshold without a
   declaration: 15 % of the whole-crown gross, no credits.
10. **Tax Credits** with a signed declaration, at most the advance.
11. **Child Tax Benefit** up to the remaining tax, and **Child Tax Bonus**
    for the rest if the tax base reaches half the minimum wage.
12. **Wage Garnishment** and the other deductions (see
    [Garnishments](#garnishment)), **Reimbursement**, and the **Annual Tax
    Settlement** when present.
13. **Meal Allowance**, outside gross pay.
14. **Net Salary**, and the employer totals.

## Statutory figures {#rates}

Every rate and amount is a dated value, so a payslip uses the figure in force
on its date. The values shipped:

| Figure | 2025 | 2026 |
|---|---|---|
| Average wage (for insurance and tax) | 46 557 Kč | 48 967 Kč |
| Social insurance, employee / employer | 7.1 % / 24.8 % | same |
| Maximum annual assessment base (48×) | 2 234 736 Kč | 2 350 416 Kč |
| Health insurance, employee / employer | 4.5 % / 9 % | same |
| Minimum wage, monthly / hourly (= health minimum base) | 20 800 Kč / 124.40 Kč | 22 400 Kč / 134.40 Kč |
| DPP threshold (25 % of the average wage) | 11 500 Kč | 12 000 Kč |
| DPČ threshold (*rozhodný příjem*) | 4 500 Kč | 4 500 Kč |
| Income tax | 15 %, 23 % above 139 671 Kč a month | 15 %, 23 % above 146 901 Kč a month |
| Taxpayer credit, monthly / annual | 2 570 / 30 840 Kč | same |
| ZTP/P credit, monthly / annual | 1 345 / 16 140 Kč | same |
| Disability credit I/II, III (monthly) | 210 / 420 Kč | same |
| Child tax benefit per month, 1st / 2nd / 3rd+ child | 1 267 / 1 860 / 2 320 Kč | same |
| Monthly bonus income test (½ minimum wage) | 10 400 Kč | 11 200 Kč |
| Tax-exempt meal allowance per shift | 123.90 Kč | 129.50 Kč |
| Sick pay reduction thresholds (hourly) | 271.60 / 407.40 / 814.80 Kč | 285.78 / 428.58 / 856.98 Kč |
| Social insurance discount | 5 %, base capped at 1.5× the average wage and 1.15 % of it per hour, 138 hours | same |

Employer obstacle rates (80 / 60 / 100 %, and 60 % as the floor for
short-time working) and the annual deduction caps
(48 000 Kč for pension and life insurance products, 150 000 Kč for mortgage
interest, 30 % of the base for gifts) are dated from 2024. On Enterprise you
add a new dated value under *Rule Parameters* to roll a figure forward.

## Time off {#leave}

The engine modules ship Czech time-off types. On Enterprise each is tied to a
work entry type; on the OCA engine to a Czech payroll code:

| Code | Time-off types | On the payslip |
|---|---|---|
| CZHOLIDAY | Holiday | paid at average earnings |
| CZSICK | Sickness, Quarantine / Isolation (karanténa) | drives the sickness compensation |
| CZOCR | Family Care (OČR), Short-term family care — limit 9 days (16 for a lone parent), Long-term family care — limit 90 days | unpaid by the employer (benefit from ČSSZ) |
| CZUNPAID | Unpaid Leave, Study Leave, unpaid | unpaid |
| CZOBSTACLE | Paid Obstacle - Doctor Visit / Escort, Blood Donation (§ 203), Public Office (§ 201), Other Acts in the Public Interest (§ 202), Study Leave, paid (§ 232), Transport of a Disabled Child to a Facility — 6 days/year, Escort to a doctor — max 1 day | paid at average earnings |
| CZPROSTOJ, CZPOVETRNOST, CZJINEPREKAZKY, CZCASTECNA | the four employer obstacles (§ 207 a, § 207 b, § 208, § 209) | paid at their percentage |
| CZMATERSKA, CZRODICOVSKA, CZOTCOVSKA | Maternity (§ 195), Parental (§ 196), Paternity Leave | unpaid by the employer |

The family-care and escort types with a limit require an allocation; the
transport of a disabled child accrues 6 days a year through its own plan.

**Annual leave accrual plans** are shipped by the base module, so they are
the same on both engines. *Statutory annual leave — 4 weeks (160 h/year)*
and *Annual leave — 5 weeks (200 h/year)* accrue leave in hours each week
worked, 1/52 of the annual entitlement, so a part year gives the
proportional part. They assume a 40-hour week. Unused leave carries over to
the next year and never expires: [§ 218](law:cz/2006/262) has no forfeiture.
The employer must schedule carried-over leave by the end of the following
year, the employee may schedule it himself after 30 June of that year, and
leave still unused when the employment ends is paid out
([§ 222 odst. 2](law:cz/2006/262)). Two alternative plans granting
the whole year on 1 January ship archived. The plans are not linked to the
*Holiday* type; assign one per employee through an allocation
(*Time Off → Allocations*).

## Annual tax reconciliation {#tax-reconciliation}

*Payroll → Payslips → Annual Tax Reconciliation* (on the OCA engine
*Payroll → CZ Annual Tax Reconciliation*) holds one record per employee and
tax year for the *roční zúčtování záloh a daňového zvýhodnění*.

1. Create the record for the employee and **Year** (the previous year by
   default).
2. Enter what only the employee's documents show under **Non-taxable Parts
   (§15)**: pension and life insurance contributions (48 000 Kč together),
   mortgage interest (150 000 Kč), gifts (up to 30 % of the base) and the
   **Spouse credit** as the eligible amount. *Union dues* and
   *Further-education exams* are recorded but no longer deducted from 2024.
3. Click **Compute**. The year's validated payslips give the gross tax base,
   the advances withheld after monthly credits and the bonus already paid;
   the record computes the annual tax, credits, child benefit and bonus, the
   **Overpayment** and the **Bonus top-up**. An underpayment is not collected,
   as § 38ch odst. 5 prescribes.
4. Add the **Settlement Total** to the payslip of the month of settlement as
   the *Annual Tax Settlement* input (on the OCA engine, an input line with
   the code `ANNUAL_TAX_SETTLEMENT`); it raises net pay. There is no button
   for this step — see [Limitations](#limitations).

The employee must ask by 15 February and bring the certificates of any
earlier employer of the year; the employer computes it by 31 March and refunds
an overpayment above 50 Kč no later than with the March wage
([§ 38ch odst. 1, 3 to 5](law:cz/1992/586)). The module does not track these
dates. The employer's annual statement to the tax office is a separate
module, listed below.

## Posting to the general ledger {#accounting}

[module:l10n_cz_hr_payroll_account_oca](module:l10n_cz_hr_payroll_account_oca)
(OCA) and
[module:l10n_cz_hr_payroll_account_ee](module:l10n_cz_hr_payroll_account_ee)
(Enterprise) put accounts of the Czech chart on the salary rules, each rule
with a debit and a credit account, so that a validated payslip posts a
balanced entry:

| Account | Lines |
|---|---|
| 521 Mzdové náklady | gross pay and sickness compensation (debit) |
| 331 Zaměstnanci | net pay (credit), and the other side of every withholding |
| 336 Zúčtování s institucemi sociálního a zdravotního pojištění | employee insurance; the credit side of the employer's insurance |
| 524 Zákonné sociální pojištění | employer insurance (debit), less the employer's social insurance discount |
| 342 Ostatní přímé daně | income tax advance and withholding tax, less the tax credits, child benefit, child tax bonus and annual tax settlement paid out |
| 527 Zákonné sociální náklady | meal allowance (debit) |
| 379 Jiné závazky | garnishments, child support, assignments, other deductions |
| 333 Ostatní závazky vůči zaměstnancům | reimbursements (debit) |

Accounts are found by the first account whose code starts with the three
digits above.

- **OCA.** Install it on purpose; it needs the OCA `payroll_account` module.
  It sets the accounts on the rules for every company on the Czech chart —
  those already on it at installation, and any company that loads the chart
  later — and creates a general journal *Salaries* (code `SLR`) for it. Choose that journal as the **Salary Journal** on the contract.
- **Enterprise.** It installs itself when Enterprise *Payroll with
  Accounting*, the Czech chart and the Czech payroll are installed. Odoo
  assigns the accounts per company and creates the salary journal through
  its own payroll accounting setup.

## Garnishments {#garnishment}

With
[module:l10n_cssk_hr_payroll_garnishment_base](module:l10n_cssk_hr_payroll_garnishment_base)
installed and an order on file for the employee, the *Wage Garnishment* rule
takes the amount from the order register, which applies the statutory order
of claims across all of the employee's orders.

Without an order in the register, enter the claim as a payslip input — *Wage
Garnishment - Priority* (`GARNISHMENT_PREF`) or *Wage Garnishment -
Non-priority* (`GARNISHMENT_NONPREF`), the amount being the outstanding
claim. On Enterprise these are also available as salary adjustments. The
rule then takes, from the net wage less the non-seizable amount, two thirds
(priority) or one third (non-priority) of the remainder up to the limit, plus
everything above the limit; one claim per payslip. Only the 2026 figures of
the non-seizable amount are shipped for this route.

*Attachment of Salary*, *Assignment of Salary* and *Child Support* are plain
deductions of the amount entered.

## Reports to the authorities {#declarations}

The filings are separate modules built on
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
and work with either engine:

| Module | Report | Filed to |
|---|---|---|
| [module:l10n_cz_hr_payroll_pvpoj](module:l10n_cz_hr_payroll_pvpoj) | Přehled o výši pojistného (PVPOJ) | ČSSZ |
| [module:l10n_cz_hr_payroll_onz](module:l10n_cz_hr_payroll_onz) | Oznámení o nástupu do zaměstnání / skončení zaměstnání (ONZ) | ČSSZ |
| [module:l10n_cz_hr_payroll_eldp](module:l10n_cz_hr_payroll_eldp) | Evidenční list důchodového pojištění (ELDP) | ČSSZ |
| [module:l10n_cz_hr_payroll_health](module:l10n_cz_hr_payroll_health) | Přehled o platbě pojistného zaměstnavatele and the employee notifications | health insurers |
| [module:l10n_cz_hr_payroll_annual_tax_settlement](module:l10n_cz_hr_payroll_annual_tax_settlement) | Vyúčtování daně z příjmů ze závislé činnosti | Finanční správa |

Since 1 January 2026 the social-security data go through the *jednotné
měsíční hlášení zaměstnavatele* (JMHZ, Act 323/2025 Sb.), which no module of
this family produces. ONZ is superseded from 1 April 2026; PVPOJ and ELDP are
still filed only for the periods the transitional provisions leave to them.
Each report's page says which.

## Limitations {#limitations}

- **Several DPPs or DPČs.** The law adds up the income from several
  agreements of one person with the same employer (§ 7 odst. 4 and § 7a
  odst. 3 of Act 187/2006 Sb.). The module does not: each payslip is tested
  against the threshold on its own.
- **Rounding.** The social premium is not rounded up to whole crowns per
  employee; the health premium is. The social insurance discount is not
  rounded either: the law rounds the total over all employees.
- **Health minimum base.** Only whole-day time off reduces it. When an
  employer-side obstacle is on the payslip the employer pays the whole
  top-up, even if part of the shortfall has another cause. ZTP card holders
  (as opposed to ZTP/P) and the other § 3 odst. 8 persons are exempt only if
  *State-insured person* is ticked.
- **Social insurance discount.** Several employments with the same employer
  are not added up, and the notification to ČSSZ (§ 7a odst. 5) and the
  eligibility reason itself are up to you.
- **Sickness compensation.** The 14 days are counted from the first day of
  the sick leave; an incapacity that began after a shift already worked
  (when the 14 days start the next day) and a reduced or forfeited
  compensation (§ 192 odst. 4 and 5) need a manual correction. Hours entered
  through the *Sick Hours* input are paid as entered.
- **Average earnings** count only the basic wage of the previous quarter, not
  surcharges or bonuses, and test "any hours worked" instead of 21 days.
- **Child tax benefit.** A ZTP/P child adds one first-tier amount instead of
  doubling that child's own tier, which is too little for a second or third
  child. The 50 Kč monthly and 100 Kč annual bonus minimums are not applied.
- **Annual tax reconciliation.** There is no button to post the result to a
  payslip, so the record never reaches *Settled*; enter the input by hand.
  Only this employer's validated payslips are read — figures from an earlier
  employer's certificate are not added. The 50 Kč refund minimum, the gift
  minimum and the 300 000 Kč mortgage cap for older loans are not applied.
  The rule that one record exists per employee and year is not enforced in
  Odoo 19.
- **Annual leave plans.** The plans assume a 40-hour week; for other hours
  scale the accrual, and the four-week minimum of § 213 odst. 3 is not
  enforced. Nothing reminds the employer of the § 218 odst. 3 deadline to
  schedule carried-over leave.
- **Short-time working (§ 209)** is paid at the rate under *Settings →
  Employees → Short-time work compensation (§ 209)*, 100 % by default. Lower
  it only when a union agreement or an internal regulation sets a lower rate;
  payslips never go below the statutory 60 %.
- **Meal allowance** is paid for every worked day; the module does not check
  the three-hour shift or a business trip on the same day, and an amount above
  the exempt limit is cut to it rather than paid as taxable income.
- **OCA engine.** The **Czech Payroll Code** of your own time-off types is
  set on the time-off type form, next to *Count as*; a type without a code
  is treated as an ordinary absence.
- The figures are shipped for 2025 and 2026. Check them against the law
  before using a later period.
