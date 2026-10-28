---
title: CZ Wage Surcharges (příplatky)
summary: Statutory Czech wage surcharges for overtime, public-holiday, night, weekend and difficult-environment work, the wage for overtime hours and the minimum wage top-up, from dated rates, on either payroll engine.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

The Czech Labour Code entitles an employee to a *příplatek* on top of the
wage for work at certain times or in certain conditions. This module
computes five of them:

- **overtime** (*práce přesčas*),
- **public holiday** (*práce ve svátek*),
- **night work** (*noční práce*),
- **Saturday and Sunday** (*práce v sobotu a v neděli*),
- **difficult working environment** (*ztížené pracovní prostředí*).

It also pays the **wage for overtime hours** (*dosažená mzda*) next to the
overtime surcharge, and the **minimum wage top-up** (*doplatek do minimální
mzdy*) when the wage falls below the minimum wage.

The module holds the dated percentages, the dated minimum wage, two contract
fields and the arithmetic, and installs without a payroll engine. The salary
rules come with its engine bridge (see [Payroll engines](#engines)). It is
part of the [Czech payroll family](module:l10n_cz_hr_payroll_base#purpose).

There is no Czech counterpart to the Slovak *stupne náročnosti*: since
1 January 2025 the private sector has one minimum wage for every job.

## Legal background {#legal}

All references are to the [Labour Code](law:cz/2006/262), private-sector
*mzda*. Every figure is a minimum (*nejméně*).

| Surcharge | Paragraph | Minimum | Of |
|---|---|---|---|
| Overtime | § 114 odst. 1 | 25 %, unless compensatory time off is agreed instead | average earnings |
| Public holiday | § 115 odst. 2 | 100 %, where agreed instead of compensatory time off | average earnings |
| Night work | § 116 | 10 %; another minimum may be agreed | average earnings |
| Difficult environment | § 117 | 10 % for each aggravating influence | minimum wage |
| Saturday and Sunday | § 118 odst. 1 | 10 %; another minimum may be agreed | average earnings |

An overtime hour is paid its wage *and* the surcharge
([§ 114 odst. 1](law:cz/2006/262)); neither is owed where the wage was agreed
with overtime already in it, for at most 150 hours a year
([§ 114 odst. 3](law:cz/2006/262)). A wage below the minimum wage is topped
up; overtime pay and the surcharges do not count towards the minimum wage
([§ 111 odst. 1](law:cz/2006/262)). The top-up is the difference per hour
worked against the hourly minimum wage, or against the monthly minimum wage
where that was agreed, set or determined in advance; an agreement (DPP, DPČ)
is always compared per hour ([§ 111 odst. 2](law:cz/2006/262)). The monthly
minimum is reduced in proportion for a shorter working time or a month not
worked in full ([§ 111 odst. 6](law:cz/2006/262)).

The aggravating influences (dust, chemicals, noise, vibration, split shifts
and others) are defined by
[government regulation No. 443/2024 Sb.](law:cz/2024/443), in force since
1 January 2025. The surcharges add up: an overtime hour on a Saturday night
earns § 114, § 116 and § 118 together.

## Setting it up {#setup}

1. Install the bridge for your engine (see [Payroll engines](#engines)).
2. Check the rates under *Employees → Configuration → Czech Wage Surcharges*:
   - **Czech Minimum Wage** — one record per start date with the monthly and
     hourly amount. 2025 (20 800 Kč / 124.40 Kč) and 2026 (22 400 Kč /
     134.40 Kč) are shipped; add the next year's record when MPSV announces
     it.
   - **Czech Wage Surcharges** — one record per start date with the
     percentages: *Overtime %* 25, *Public holiday %* 100, *Night work %* 10,
     *Saturday/Sunday %* 10, *Difficult environment %* 10, and *Standard
     weekly hours* 40. One record dated 1 January 2024 is shipped. If you pay
     more than the minimum, raise the figure or add a record dated from the
     agreement. *Night work % (agreed)* and *Saturday/Sunday % (agreed)* are
     empty; fill them in only if a collective or individual agreement sets
     another minimum.
   Only HR managers can change these records, and none of the five
   percentages can be zero.
3. On the contract template (*Employees → Configuration → Contract
   Templates*), group **Czech Wage Surcharges**:

   | Field | What it does |
   |---|---|
   | Ztížené prostředí — počet vlivů | The number of aggravating influences. Each earns a further 10 %. Zero means no difficult-environment surcharge, whatever hours are entered. |
   | Sjednaná jiná výše příplatků | An agreement sets another minimum for night and weekend work: the *(agreed)* percentages are used instead. |
   | Minimum wage top-up compared with | *Hourly minimum wage* (the default, as in the law) or *Monthly minimum wage*. Choose monthly only where it was agreed, set or determined in advance. Agreements and hourly-paid employees are always compared per hour. |

## Entering the hours {#usage}

The hours of each kind are entered on the payslip — as an input on the OCA
engine, as an *Other Input* on Enterprise:

| Input | Code | Surcharge line on the payslip |
|---|---|---|
| Overtime hours | `PRESCAS` | Overtime Wage (§ 114) and Overtime Surcharge (§ 114) |
| Public holiday hours | `SVATEK` | Public Holiday Surcharge (§ 115) |
| Night hours | `NOCNI` | Night Work Surcharge (§ 116) |
| Weekend hours | `VIKEND` | Saturday/Sunday Surcharge (§ 118) |
| Difficult-environment hours | `ZTIZENE` | Difficult Environment Surcharge (§ 117) |

The amount of the input is the number of hours. Night, weekend and
difficult-environment hours are the same hours as ordinary work seen a second
time, so enter them on top of the working time, not instead of it. If a
worked-days line carries the same code (for example from your own work entry
type with code `NOCNI`), that line wins over the input.

## How the amount is computed {#computation}

For each code: hours × hourly base × percentage, rounded **up** to the
haléř, so that rounding never takes the payment below the minimum.

- **Overtime Wage** is the overtime hours × the employee's own hourly wage:
  the hourly wage of an hourly-paid employee, otherwise the monthly wage
  divided by the hours the contract schedules in the month. Record no
  overtime hours for an employee whose wage already includes overtime
  (§ 114 odst. 3).
- **Minimum Wage Top-up** runs after the wage replacements and before gross
  pay, so it is insured and taxed. The wage compared is the basic wage plus
  the allowances computed before it, less the overtime wage, the surcharges
  and the wage replacements (holiday, obstacles); the hours are the ordinary
  hours worked, without absences and overtime. On the hourly basis the top-up
  is (hourly minimum wage − wage per hour) × hours; on the monthly basis it is
  the monthly minimum wage, reduced by the hours worked against a full-time
  month of the company's calendar, less the wage.

- **Hourly base for overtime, holiday, night and weekend** is the employee's
  average hourly earnings as the Czech payroll module computes them (the
  previous quarter, or the override on the contract).
- **Hourly base for the difficult environment** is the hourly minimum wage
  ([§ 117 odst. 2](law:cz/2006/262); § 3 of government regulation
  No. 443/2024 Sb., until 2024 No. 567/2006 Sb.), raised in proportion when
  the weekly hours of the **company's** working calendar are below *Standard
  weekly hours* ([§ 111 odst. 5](law:cz/2006/262)). An employee's own shorter
  hours (part-time, § 80) do not raise it. The surcharge is then multiplied by
  the number of aggravating influences.
- The surcharges enter gross pay, and so insurance and tax.

## Payroll engines {#engines}

Install the bridge that matches your Czech payroll engine. Neither installs
itself.

- [module:l10n_cz_hr_payroll_surcharges_ee](module:l10n_cz_hr_payroll_surcharges_ee)
  — Odoo Enterprise Payroll: the five rules in the Czech structure and the
  five payslip input types.
- [module:l10n_cz_hr_payroll_surcharges_oca](module:l10n_cz_hr_payroll_surcharges_oca)
  — OCA payroll: the five rules in the Czech structure, each declaring its
  input.

## Limitations {#limitations}

- **Minimum wage top-up.** Bonuses and other wage components count only if
  their salary rule runs before the top-up (sequence below 95); later ones
  are not counted, so the top-up can be too high. The Czech payroll module
  keeps its own copy of the minimum wage as a rule parameter; keep both in
  step. Choosing the monthly basis is your statement that it was agreed in
  advance.
- **Compensatory time off for overtime** (§ 114 odst. 1 and 2) is not
  tracked: enter overtime hours on the payslip only when they are paid.
- **Public holiday** hours are paid at 100 % whenever entered. Enter them only
  where the surcharge was agreed instead of compensatory time off.
- **The company's working calendar stands for the standard week.** The
  hourly minimum wage is raised only when the company's calendar has fewer
  weekly hours than *Standard weekly hours*. Keep the company calendar at the
  employer's stanovená týdenní pracovní doba.
- **Average earnings** come from the Czech payroll module, which counts only
  the basic wage of the previous quarter.
- The contract fields are on the contract template form only; a value reaches
  an employee when the template is applied to the contract.
- No Czech translation ships with this module, so its screens are in English.
