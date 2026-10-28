---
title: SK Pension Insurance Record Sheet (ELDP)
summary: The evidenčný list dôchodkového poistenia for a calendar year — each employee's pension assessment base and insured period, built from the year's payslips and exported as a batch XML for the Sociálna poisťovňa.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

The *Evidenčný list dôchodkového poistenia* (**ELDP**) records, per employee
and calendar year, the period of pension insurance and the assessment base on
which pension premiums were paid. The Sociálna poisťovňa uses it to establish
pension rights.

This module builds the electronic batch ELDP (one `eldpZec` record per
employee) for a whole year from that year's payslips and exports it as XML.
Payslips are read through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
so it works with either Slovak payroll engine — see
[the Slovak payroll guide](module:l10n_sk_hr_payroll_base#declarations).

## Legal background {#legal}

References are to the [Social Insurance Act](law:sk/2003/461).

- **The employer's records.** The employer keeps a record of each employee for
  social-insurance purposes for as long as the insurance lasts
  ([§ 232 ods. 1](law:sk/2003/461#paragraf-232.odsek-1)); among other things it
  contains the start and end of the employment and the employee's
  **unlimited assessment base** (*neobmedzený vymeriavací základ*,
  [§ 232 ods. 2 písm. e)](law:sk/2003/461#paragraf-232.odsek-2.pismeno-e)).
- **Submitting it.** The current text of the act does not name an annual ELDP
  filing; the employer submits documents to the Sociálna poisťovňa when asked
  to ([§ 231 ods. 1 písm. g)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-g),
  last part), in the form the Sociálna poisťovňa determines
  ([§ 231 ods. 2](law:sk/2003/461#paragraf-231.odsek-2)). File an ELDP when
  and for whom the Sociálna poisťovňa requires it.

## Setting it up {#setup}

On the company:

| Value | Used as |
|---|---|
| *Company ID* (IČO), **exactly 8 digits** | `<ico>` |
| *Sociálna poisťovňa variable symbol*, exactly 10 digits | `<icz>`, the employer's identification number at the Sociálna poisťovňa |
| city and a 5-digit ZIP (street optional) | the employer's address |

Fill in the *Sociálna poisťovňa variable symbol* on the ELDP form itself. It
is stored on the company and shared with the MVP, VPP and RLFO modules, so it
is entered once; changing it needs the right to edit companies.

Per employee: the **birth number** in *Identification No*, the date of birth
(*Birthday*), and the *Departure Date* of anyone who left. The **last word of
the name is the surname** and everything before it the first name; with
`hr_employee_firstname` installed, its separate name fields are used.

## Preparing the ELDP {#usage}

*Payroll Declarations → SK ELDP (pension)*, then *New*.

1. Choose the **Year**. The period is always 1 January to 31 December.
2. Click **Generate**. Every payslip of the company whose period lies within
   the year is collected (cancelled ones excepted), one row is built per
   employee, and the XML is validated against `ELDP-v2015_1.3.xsd` and
   attached.
3. Upload the XML to the Sociálna poisťovňa portal and click
   **Mark Submitted**. **Reset to Draft** reopens it.

Generation stops if the company data above are incomplete, if an employee has
no valid birth number or date of birth, or if the year has no payslips.

## What each record contains {#output}

| Item | Taken from |
|---|---|
| birth number, surname, first name, date of birth | the employee |
| start of the insurance relationship (`datVzniku`) | the start of the employee's current uninterrupted run of contracts (*Contract Start Date*) |
| end (`datZaniku`) or *still lasting* (`trva`) | the employee's departure date, if it falls within the year |
| period in the year (`datOd`–`datDo`) | the relationship clamped to the year |
| pension assessment base (`vzDP`) | the sum of the employee's *GROSS* for the year |
| type of insurance (`znakPoist`) | always *A* (employee) |
| excluded days (`dniVyluc`) | always 0 |

## Limitations {#limitations}

- **The assessment base is the summed GROSS.** It is not reduced by
  excluded periods and no maximum is applied. Check it for employees with
  unpaid leave, sick leave, maternity or parental leave, and for high earners.
- **One continuous period per employee per year.** Several spells in one year
  (leaving and returning, an interrupted insurance) are not split into
  separate rows.
- Excluded days are always reported as 0, and every employee is reported as
  *A* (employee), including agreement workers.
- Draft payslips count; a payslip whose period crosses the year boundary is
  ignored.
- Only a regular filing; corrections go through the portal. Only the 2015
  schema (version 1.3) is shipped.
- Schema validation checks the shape of the file, not the figures.
