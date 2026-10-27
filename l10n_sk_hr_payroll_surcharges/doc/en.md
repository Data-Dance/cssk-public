---
title: SK Wage Surcharges and Minimum Wage Claims
summary: Statutory Slovak wage surcharges for night, Saturday, Sunday, public-holiday, overtime, difficult-conditions and standby work, and the top-up to the minimum wage claim of the job's stupeň náročnosti, on either payroll engine.
verified: 19.0.1.2.5
---

## What it is for {#purpose}

The Zákonník práce entitles an employee to a *mzdové zvýhodnenie* for work at
certain times or in certain conditions, and guarantees a *minimálny mzdový
nárok* that depends on how demanding the job is. This module computes both:

- the surcharges for **night**, **Saturday**, **Sunday** and
  **public-holiday** work, **overtime**, **difficult working conditions** and
  **inactive standby away from the workplace**;
- the six **stupne náročnosti** and the **top-up** (*doplatok*) of a wage that
  falls short of the claim for the job's level.

Every percentage and every amount is a dated record, so a change in the law is
a data change. The module itself holds the rates, the fields and the
arithmetic, and works without a payroll engine; the salary rules come with its
engine bridge (see [Payroll engines](#engines)). It is part of the
[Slovak payroll family](module:l10n_sk_hr_payroll_base#purpose).

## Legal background {#legal}

All references are to the [Zákonník práce](law:sk/2001/311) unless stated
otherwise.

| Surcharge | Paragraph | Minimum | Of |
|---|---|---|---|
| Overtime | [§ 121 ods. 1](law:sk/2001/311#paragraf-121.odsek-1) | wage for the hour + 25 % (35 % for risky work) | average earnings |
| Public holiday | [§ 122 ods. 1](law:sk/2001/311#paragraf-122.odsek-1) | 100 % | average earnings |
| Saturday | [§ 122a](law:sk/2001/311#paragraf-122a) | 50 % (45 % by agreement where Saturday work is regular) | minimum hourly wage |
| Sunday | [§ 122b](law:sk/2001/311#paragraf-122b) | 100 % (90 % by agreement where Sunday work is regular) | minimum hourly wage |
| Night | [§ 123](law:sk/2001/311#paragraf-123) | 40 % (50 % for risky work; 35 % by agreement where most work is at night, not for risky work) | minimum hourly wage |
| Difficult conditions | [§ 124 ods. 3](law:sk/2001/311#paragraf-124.odsek-3) | 20 % | minimum hourly wage |
| Inactive standby off site | [§ 96 ods. 5](law:sk/2001/311#paragraf-96.odsek-5) | 20 % | minimum hourly wage |

The lower Saturday, Sunday and night rates may be agreed in a collective
agreement or, at an employer with no trade union and fewer than 20 employees
at the end of the previous year, in the employment contract.

**Minimum wage claims.** An employer whose pay is not set by a collective
agreement must pay at least the claim for the level of the job, and tops up
any shortfall in a month ([§ 120 ods. 1](law:sk/2001/311#paragraf-120.odsek-1)).
Overtime pay, the surcharges and the difficult-conditions compensation are
left out of the comparison ([§ 120 ods. 2](law:sk/2001/311#paragraf-120.odsek-2)).
Each job is assigned a level by its most demanding activity
([§ 120 ods. 3](law:sk/2001/311#paragraf-120.odsek-3)). The monthly claim is
the year's monthly minimum wage plus (coefficient − 1) × the 2020 minimum
wage of 580 €, with coefficients 1.0 to 2.0; the hourly claim is 1/174 of it
([§ 120 ods. 4](law:sk/2001/311#paragraf-120.odsek-4)). Hourly claims rise
for an established week shorter than 40 hours
([§ 120 ods. 5](law:sk/2001/311#paragraf-120.odsek-5)); the monthly claim is
reduced in proportion to the time worked
([§ 120 ods. 6](law:sk/2001/311#paragraf-120.odsek-6)). The minimum hourly
wage itself is 1/174 of the monthly minimum wage
([§ 2 ods. 2 zákona o minimálnej mzde](law:sk/2007/663#paragraf-2.odsek-2)).

## Setting it up {#setup}

1. Install the bridge for your engine — it installs itself together with the
   Slovak payroll module of that engine.
2. **Classify the jobs.** On each job position set **Stupeň náročnosti**.
   A contract created on the job takes the level over when the job is chosen;
   it never overwrites a level already set on the contract.
3. **On the contract**, group **Slovak Wage Surcharges**:

   | Field | What it does |
   |---|---|
   | Stupeň náročnosti | The level of this contract (§ 120). Left empty, level 1 — the plain minimum wage — is used. |
   | Riziková práca | Raises the night surcharge to 50 % and overtime to 35 %, and rules out the reduced night rate. |
   | Reduced night rate agreed, Reduced Saturday rate agreed, Reduced Sunday rate agreed | Tick where the lower rate has been agreed as described above. The night flag is hidden for risky work. |

   When the agreed wage is below the claim for the contract's level, reduced in
   proportion for a shorter week, a **Minimum Wage Warning** appears above the
   group. Agreements (dohody) and contracts with an hourly wage are not
   checked.
4. **Rates.** *Employees → Configuration → Slovak Wage Surcharges* (HR
   managers):
   - **Minimum Wage Claims** — one record per level and start date, with the
     monthly and hourly claim;
   - **Surcharge Rates** — one record per start date with every percentage
     and the **Standard weekly hours**.

   To pay more than the statutory minimum, or to roll the figures into a new
   year, add a new dated record rather than changing an old one.

## Entering the hours {#usage}

The module does not detect night or weekend hours from attendance. Each
surcharge is fed by a number of hours under its code:

| Code | Hours of | Payslip line |
|---|---|---|
| NOC | night work | *Night Work Surcharge* |
| SOBOTA | Saturday work | *Saturday Work Surcharge* |
| NEDELA | Sunday work | *Sunday Work Surcharge* |
| SVIATOK | work on a public holiday | *Public Holiday Work Surcharge* |
| NADCAS | overtime | *Overtime Pay* and *Overtime Surcharge* |
| STAZENY | work in difficult conditions | *Difficult Conditions Compensation* |
| POHOTOVOST | inactive standby away from the workplace | *Standby Compensation* |

Enter the hours as a payslip input with that code (*Other Inputs* on the
payslip; the input types are called *Night hours*, *Saturday hours*, and so
on). If the payslip has a worked-days line with the same code, it takes
precedence over the input.

Night, Saturday, Sunday and difficult-conditions hours are hours the employee
also worked normally. A work entry type with one of these codes that moves the
hours out of ordinary work would reduce the basic wage; record such hours
alongside ordinary work, or use the inputs.

## What the payslip shows {#payslip}

- **Surcharges.** Hours × hourly base × percentage, rounded **up** to the
  cent, because every figure is a statutory minimum. The hourly base is the
  level-1 **minimum hourly wage** for night, Saturday, Sunday, difficult
  conditions and standby — whatever the employee's own level — and the
  employee's **average hourly earnings** for public holidays and overtime.
- **Overtime pay.** Overtime hours fall outside the time a monthly wage pays
  for, so *Overtime Pay* adds the wage for those hours at average earnings
  next to the surcharge. Public-holiday hours get only the surcharge; their
  basic pay is assumed to be in the basic wage.
- **Minimum Wage Top-up.** Compares the **basic wage** — without surcharges,
  overtime and wage replacements — with the claim for the contract's level:
  - for a monthly wage, against the monthly claim reduced by the ordinary
    hours worked (absences excluded) over the hours a full-time contract on
    the company's working calendar would work in the period;
  - for an hourly wage (on the OCA engine only), against the hourly claim,
    raised for a working calendar shorter than the standard week.

  It applies only to a pracovný pomer. All surcharge lines count towards gross
  pay, so they are insured and taxed.

## Statutory figures {#rates}

Percentages, effective from 1 June 2023 (the only record shipped):

| Night | Night, risky | Night, reduced | Saturday | Saturday, reduced | Sunday | Sunday, reduced | Difficult | Standby | Public holiday | Overtime | Overtime, risky |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 40 % | 50 % | 35 % | 50 % | 45 % | 100 % | 90 % | 20 % | 20 % | 100 % | 25 % | 35 % |

Minimum wage claims (monthly / hourly):

| Level | 2024 | 2025 | 2026 |
|---|---|---|---|
| 1 — pomocné práce | 750 € / 4.310 € | 816 € / 4.690 € | 915 € / 5.259 € |
| 2 — jednoduché odborné práce | 866 € / 4.977 € | 932 € / 5.356 € | 1 031 € / 5.925 € |
| 3 — odborné práce | 982 € / 5.644 € | 1 048 € / 6.023 € | 1 147 € / 6.592 € |
| 4 — zložité odborné práce | 1 098 € / 6.310 € | 1 164 € / 6.690 € | 1 263 € / 7.259 € |
| 5 — veľmi zložité odborné práce | 1 214 € / 6.977 € | 1 280 € / 7.356 € | 1 379 € / 7.925 € |
| 6 — vysoko špecializované práce | 1 330 € / 7.644 € | 1 396 € / 8.023 € | 1 495 € / 8.592 € |

So a night hour in 2026 earns at least 40 % × 5.259 € = 2.11 € on top of the
wage.

## Payroll engines {#engines}

The salary rules are added by a bridge for each engine; both use the same
arithmetic and the same data from this module.

- [module:l10n_sk_hr_payroll_surcharges_ee](module:l10n_sk_hr_payroll_surcharges_ee)
  adds the rules to the Slovak structure of Odoo Enterprise Payroll, together
  with the seven payslip input types. Its contract templates carry the
  surcharge fields over to new contracts. It installs itself when
  [module:l10n_sk_hr_payroll_ee](module:l10n_sk_hr_payroll_ee) and this module
  are installed.
- [module:l10n_sk_hr_payroll_surcharges_oca](module:l10n_sk_hr_payroll_surcharges_oca)
  adds the rules to the Slovak structures of the OCA payroll app, each rule
  declaring its own input. It installs itself when
  [module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca) and this
  module are installed.

## Limitations {#limitations}

- **No check of the conditions for the reduced rates.** The module does not
  check that a collective agreement (or an eligible employment contract)
  exists.
- **Collective agreements on pay.** § 120 ods. 1 applies only where pay is
  not set by a collective agreement; the module always tops up.
- **Dohody** get no minimum wage check at all, neither the § 120 claim (which
  does not apply to them) nor the minimum hourly wage.
- **Hours are entered, not derived.** No work entry types are shipped, and
  hours are not taken from attendance or the calendar.
- **Overtime** is valued at average earnings; an employer whose contracts
  state an hourly rate has to adjust the *Overtime Pay* rule.
- **Standby** covers only the inactive part away from the workplace; inactive
  standby at the workplace is working time and is not detected.
- **Difficult conditions** use one rate; the hazard-specific rates of some
  collective agreements are not modelled.
- **Periods before 1 June 2023** are not covered by the shipped rate record,
  and its percentage fields cannot express a surcharge set as a fixed amount.
