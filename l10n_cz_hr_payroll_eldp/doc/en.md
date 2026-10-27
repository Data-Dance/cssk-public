---
title: CZ Pension Insurance Record Sheet (ELDP)
summary: The evidenční list důchodového pojištění for a calendar year — each employee's pension assessment base and insured days, built from the year's payslips and exported as a batch XML in the ČSSZ ELDP09 structure.
verified: 19.0.1.0.4
---

## What it is for {#purpose}

The *evidenční list důchodového pojištění* (**ELDP**) records, per employee
and calendar year, the period of pension insurance and the assessment base on
which the premium was paid. The ČSSZ uses it to establish pension rights.

This module builds the batch ELDP (one `eldp09` record per employee inside a
`RELDP` envelope) for a whole year from that year's payslips and exports it as
XML, checked against the official `ELDP09.xsd`. Payslips are read through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
so it works with either Czech payroll engine — see
[the Czech payroll guide](module:l10n_cz_hr_payroll_base#declarations).

**From 2026 the employer no longer files an ELDP for ordinary cases.** Read
the next section before you use it.

## Legal background {#legal}

References are to the
[Act on the Organisation and Implementation of Social Security](law:cz/1991/582).

- **From 2026 the ČSSZ compiles the ELDP itself.** Under § 38 odst. 1 and 2
  as worded from 1 January 2026, the employer reports the data needed for
  pension insurance every month through the
  *jednotné měsíční hlášení zaměstnavatele* (JMHZ,
  [Act No. 323/2025 Sb.](law:cz/2025/323)), and the ČSSZ draws up the ELDP
  from them. The sheet runs from 1 January, or from the day the insurance
  began, to 31 December or the day it ended (§ 38 odst. 3).
- **When an employer still files one.** Under the transitional provisions of
  [Act No. 360/2025 Sb.](law:cz/2025/360) (Art. V), the employer still keeps
  and files ELDPs in the way and within the time limits of §§ 38 and 39 as
  worded before 2026
  - for **calendar years before 2026** (so the ELDPs for 2025);
  - for an employee whose participation in pension insurance **ended before
    1 April 2026**, with the data for 2026; and
  - when the ČSSZ asks for one, within 8 days of the request.

  This module produces the ELDP in the ELDP09 electronic structure for the
  first two cases; it refuses 2026 for anyone else and every year from 2027.
  An ELDP the ČSSZ asks for has to be prepared outside the module.
- **What the sheet records** (§ 38 odst. 4): the employer, the employee's
  name, surname and birth surname, date and place of birth, permanent address
  and birth number, the kind of activity, the period of insurance, the
  assessment base, and the periods that are excluded.

## Setting it up {#setup}

On the company:

| Value | Used as |
|---|---|
| *ČSSZ variable symbol (VS)*, 8 to 10 digits | `<comp vs>` |
| *OSSZ code*, a number from 100 to 999 | `tco` and `dep`, the competent social security office. Defaults to 100. |
| *Company ID* (IČO) | `<comp id>` |

The *ČSSZ variable symbol (VS)* and *OSSZ code* fields are on the **Payroll
Reporting** tab of the company form (see
[the declaration base](module:l10n_cssk_payroll_declaration_base#company)).
They are shared with the PVPOJ and ONZ modules.

Per employee: the **birth number** in *Identification No* (9 or 10 digits),
the date of birth (*Birthday*), the place of birth, the private address
(street with house number, city, ZIP), and the start and end dates of every contract version
(*Contract Start Date*, *Contract End Date*) — earlier contracts in the year
count too, not only the current one.

## Preparing the ELDP {#usage}

*Payroll Declarations → CZ ELDP (pension)*, then *New*.

1. Choose the **Year**. The period is always 1 January to 31 December.
2. Click **Generate**. Every confirmed payslip of the company whose period
   ends within the year is collected (drafts and cancelled ones are not
   counted; see [the declaration base](module:l10n_cssk_payroll_declaration_base#payslips)),
   one record is built per employee, and the XML is validated against `ELDP09.xsd` and attached.
3. Submit the XML through the ČSSZ e-portal and click **Mark Submitted**.
   **Reset to Draft** reopens it.

For a year **before 2026** the ELDP covers every employee with a payslip in
the year. For **2026** it covers only the employees with a payslip in 2026
whose last employment period ended before 1 April 2026; the others are reported through
JMHZ. **2027 and later** are refused.

Generation stops if the VS or OSSZ code is missing or invalid, if an employee
has no valid birth number or date of birth, if the year has no payslips, or —
for 2026 — if no employee with payslips left before 1 April 2026. It also
stops if an employee has more than three separate employment periods in the
year: one ELDP holds at most three (a limit of the ELDP09 schema), so prepare
that employee's ELDP by hand.

## What each record contains {#output}

| Item | Taken from |
|---|---|
| birth number, date and place of birth | the employee |
| surname (`sur`) and first name (`fir`) | the employee's name: the last word is the surname, everything before it the first name(s). With separate first and last name fields (OCA `hr_employee_firstname`) those are used. |
| birth surname | the current surname — see the limitations |
| address | the private address; a trailing number in the street is taken as the house number, the post office (`pos`) is the first five letters of the city |
| type (`typ`) | *1* if the employment continues past 31 December, *2* if the last employment period ended during the year |
| periods (`t1` rows, `fro`–`to`) | one row per employment period in the year (up to three), built from the start and end dates of all the employee's contract versions, clamped to the year |
| days of insurance (`din`) | the calendar days of each period within the year |
| assessment base (`inc`) | per period, the sum of the employee's monthly assessment bases taken from his *Social Insurance (Employer)* line (`SOCIALER`) — the gross capped at the maximum assessment base (*§ 15a zák. 589/1992 Sb.*), nothing for a month that was not insured — rounded **up** to whole koruny. A payslip goes to the period its end date falls in |
| kind of activity (`cod`) | always *1* |
| excluded and deducted days (`dex`, `dar`), month markers | always 0 / empty |

## Limitations {#limitations}

- **The birth surname is the current surname**, and a surname of more than
  one word is only recognised with separate first and last name fields.
- **Excluded periods are not deducted.** The assessment base comes from the
  payslips as they are; check it for employees with unpaid leave, sick leave,
  maternity or parental leave.
- **At most three employment periods per employee.** An employee with more
  is refused; prepare that ELDP by hand.
- Excluded days are always 0 and every record is reported as kind of activity
  *1*, also for agreement workers.
- Only a regular filing; corrections go through the portal. Only the
  ELDP09 structure is shipped.
- Schema validation checks the shape of the file, not the figures. No ELDP
  from this module has been confirmed by a live ČSSZ submission.
