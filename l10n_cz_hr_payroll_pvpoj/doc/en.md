---
title: CZ Social Insurance Overview (PVPOJ)
summary: The monthly přehled o výši pojistného for the ČSSZ — the employer's total social insurance premium for a month, summed from the payslips and exported as XML in the PVPOJ 2025 structure.
verified: 19.0.1.1.3
---

## What it is for {#purpose}

The *přehled o výši pojistného* (**PVPOJ**) is the employer's monthly report
to the Czech social security administration (ČSSZ) of the social insurance
premium it owes for a month: the total assessment base, the employer's and
the employees' premium, and the *sleva na pojistném* claimed for part-time
employees.

This module builds that overview for one month from the month's payslips and
exports it as XML in the ČSSZ structure `PVPOJ2025`, checked against the
official `PVPOJ25.xsd`. Payslips are read through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
so it works with either Czech payroll engine — see
[the Czech payroll guide](module:l10n_cz_hr_payroll_base#declarations).

**Since 2026 the overview is filed only for older periods.** Read the next
section before you use it.

## Legal background {#legal}

- **The form was replaced in 2026.** From 1 January 2026 the employer reports
  the assessment base and the premium through the
  *jednotné měsíční hlášení zaměstnavatele* (JMHZ) under
  [§ 9 odst. 2 of the Social Insurance Premium Act](law:cz/1992/589), which
  now refers to the [JMHZ Act](law:cz/2025/323). The JMHZ is due from the
  1st to the 20th of the following month (§ 7 odst. 1 of that act). This
  module does not produce a JMHZ.
- **What is still filed as a PVPOJ.** Under the transitional provisions of
  [Act No. 360/2025 Sb.](law:cz/2025/360) (Art. IX), a PVPOJ is still filed
  - for every month **before January 2026**, in the way the act prescribed
    before 2026 — also when it is filed or corrected now; and
  - for **January to March 2026** by an employer that was an employer during
    those months but no longer is on 1 April 2026: by the 20th of the month
    after the month in which it stopped being one.
- **The figures.** The premium is due from the 1st to the 20th of the
  following month ([§ 9 odst. 1](law:cz/1992/589)). The employer's rate is
  24.8 % of the assessment base of ordinary employees
  (*§ 7 odst. 1 písm. a)*, band A); the employee's rate is 7.1 %
  (*písm. d)*); each premium is rounded up to whole koruny (*§ 7 odst. 3*).
  Higher employer rates apply to rescuers and firefighters (band B) and to
  risky occupations (band C) under *§ 5a odst. 1 písm. b) and c)*; the module
  does not support them.
- **Sleva na pojistném.** The employer may claim a discount for a part-time
  employee (8 to 30 hours a week) in one of the groups of
  [§ 7a odst. 1](law:cz/1992/589) — over 55, a parent of a child under 10, a
  carer, a student under 26, a retraining participant, a person with a
  disability, or anyone under 21 (for whom the hours condition does not
  apply), provided the monthly assessment base does not exceed 1.5 times the
  average wage (*§ 7a odst. 3*). The overview then lists those employees.

## Setting it up {#setup}

On the company:

| Value | Used as |
|---|---|
| *ČSSZ variable symbol (VS)*, **exactly 10 digits** | `<vs>`, the employer's variable symbol at the ČSSZ |
| *OSSZ code*, a number from 100 to 999 | `<kodOSSZ>`, the competent social security office. Defaults to 100. |
| *Company ID* (IČO) or, failing that, the *Tax ID* | `<IC>` |
| city and ZIP (street optional) | the employer's address |

The *ČSSZ variable symbol (VS)* and *OSSZ code* fields are on the **Payroll
Reporting** tab of the company form (see
[the declaration base](module:l10n_cssk_payroll_declaration_base#company)).
They are shared with the ELDP and ONZ modules. Because the OSSZ code has a default,
a forgotten code is not reported: check it.

For the discount annex, set the employee's *Social insurance discount
category* in the payroll module and give the employee a working schedule
with the shorter weekly hours, and a date of birth.

## Preparing the overview {#usage}

*Payroll Declarations → CZ PVPOJ (social)*, then *New*. The *Payroll
Declarations* menu is a top-level application.

1. Choose the **Year** and **Month**. The period is always the whole
   calendar month.
2. Click **Generate**. The module collects every confirmed payslip of the
   company whose period ends in the month (drafts and cancelled ones are not
   counted; see [the declaration base](module:l10n_cssk_payroll_declaration_base#payslips)),
   adds one row per employee, renders the XML, validates it against `PVPOJ25.xsd` and attaches
   it.
3. Submit the XML through the ČSSZ e-portal and click **Mark Submitted**.
   The filed copy is kept. **Reset to Draft** reopens the overview for
   regeneration; a submitted overview cannot be deleted.

Generation stops if the VS is not 10 digits, the OSSZ code is not between 100
and 999, the company has no city or ZIP, or the month has no payslips. It
also stops, pointing to the JMHZ, for **April 2026 and later**, and for
**January to March 2026** when the company still has an employee whose
contract runs on 1 April 2026 — only an employer that had ceased to be one
by then files those months. A month before 2025 is refused too: only the
2025 structure is shipped.

## What the overview contains {#output}

| Item | Taken from |
|---|---|
| employer assessment base, band A (`zakladZamestnavateleA`) | the sum of the employees' monthly assessment bases, each rounded **up** to whole koruny (*§ 5d*). An employee's base is taken from his *Social Insurance (Employer)* line (`SOCIALER`) — the gross capped at the annual maximum assessment base; an employee with no such line (a month he is not insured) adds nothing |
| employer premium, band A (`pojistneZamestnavateleA`) and in total | 24.8 % of that total base, rounded **up** once, on the company total (*§ 7 odst. 1 písm. a) a odst. 3*) |
| employee premium (`pojistneZamestnance`) | the sum of each employee's *Social Insurance Total (Employee)* (`SOCIALEETOT`), rounded **up** per employee |
| total premium (`pojistneCelkem`) | employer + employee premium |
| discount block (`slevaZamestnavatele`) | count and sum of the assessment bases of the employees who have a discount; the discount itself is 5 % of that sum, rounded **up** (*§ 7b odst. 1*) |
| amount to pay (`pojistneUhrada`) | total premium less the discount |
| discount annex (`slevaZamestnanci`) | per discounted employee: name, date of birth, assessment base (not the gross), the reason letter (a–g) from the discount category, and the weekly hours of the working schedule |
| type of overview | always *N* (regular) |
| date filled in | the day you click *Generate* |

When no payslip of the month carries a discount, the discount block and annex
are left out.

## Limitations {#limitations}

- **Not for periods from January 2026** except the case described under
  [Legal background](#legal); for those, the data go into the JMHZ. Whether
  the company "is no longer an employer" on 1 April 2026 is judged from the
  contract dates of its employees.
- **Computed from the bases, not the payslip premiums.** The employer
  premium and the discount are worked out from the employees' assessment
  bases, so they can differ by a koruna from the sum of the payslips' own
  premium lines. Compare the totals with the payroll recapitulation before
  filing.
- **Only band A.** Employees in risky occupations or in rescue and fire
  services (bands B and C) are reported in band A at 24.8 %.
- **Only a regular overview.** The type is always *N*; a corrective overview
  (*opravný přehled*) has to be filed through the portal.
- **Discount reason.** An employee whose discount category cannot be read is
  reported with reason *g* (under 21). Check the annex.
- **Name split.** In the annex the last word of the employee's name is the
  surname and everything before it the first name(s), unless separate first
  and last name fields (OCA `hr_employee_firstname`) are present.
- Schema validation checks the shape of the file, not the figures. No
  overview from this module has been confirmed by a live ČSSZ submission;
  check the first one by hand.
