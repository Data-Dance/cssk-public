---
title: CZ Employment Start/End Notification (ONZ)
summary: The oznámení o nástupu do zaměstnání / skončení for the ČSSZ in the ONZ 2022 XML structure — superseded by the JMHZ employee register since 1 April 2026.
verified: 19.0.1.0.4
---

## What it is for {#purpose}

The *oznámení o nástupu do zaměstnání* (**ONZ**, the form that also served as
the *odhláška*) told the ČSSZ that an employee had started or ended an
employment that is subject to sickness insurance.

This module builds a batch ONZ for a list of employees — either all starts or
all ends — and exports it as XML, checked against the official
`ONZ2022_20230616.xsd`. The data come from the employee and contract records,
not from payslips. It belongs to the family of payroll filings built on
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
— see [the Czech payroll guide](module:l10n_cz_hr_payroll_base#declarations).

**The form can no longer be filed.** See the next section.

## Legal background {#legal}

- **Since 1 April 2026** the employer meets the duty to notify the ČSSZ of
  the day an employee starts and the day the employment ends by registering
  the employee in, and removing them from, the *evidence zaměstnanců* under
  the [JMHZ Act](law:cz/2025/323) —
  [§ 94 of the Sickness Insurance Act](law:cz/2006/187) as amended by
  [Act No. 360/2025 Sb.](law:cz/2025/360) (Art. XXIV, in force from
  1 April 2026 under Art. XXXIV letter d).
- **No ONZ for older events either.** Where the event happened before
  1 April 2026 and the employer had not yet notified it, the duty is met in
  the new way (Art. XXV point 4 of Act No. 360/2025 Sb.). An employee
  registered on 31 March 2026 counts as registered in the new evidence
  (point 6).

The module therefore **refuses to generate** an ONZ on or after
1 April 2026, and one for an event dated on or after that day; notifications
generated before then stay on their records. It does not produce the JMHZ
registration.

## Setting it up {#setup}

On the company:

| Value | Used as |
|---|---|
| *ČSSZ variable symbol (VS)*, 8 to 10 digits | `<comp vs>` |
| *OSSZ code*, a number from 100 to 999 | `dep`, the competent social security office. Defaults to 100. |
| *Company ID* (IČO) | `<comp id>` |

The *ČSSZ variable symbol (VS)* and *OSSZ code* fields are **not shown on any
form**; fill them in by importing them on the companies list. They are shared
with the PVPOJ and ELDP modules.

Per employee: the birth number in *Identification No*, the date of birth
(*Birthday*), optionally the place of birth, the private address, and the
contract's *Contract Start Date* (for a start) or *Contract End Date* (for an
end).

## Preparing a notification {#usage}

*Payroll Declarations → CZ ONZ (registration)*, then *New*.

1. Choose the **Event Type** — *Start of employment* or *End of employment*.
   It applies to every employee in the notification.
2. Add the **Employees**.
3. Click **Generate**. The XML is built and validated against the schema.
   **Mark Submitted** and **Reset to Draft** work as on the other filings.

Generation stops without employees, without a valid VS or OSSZ code, for an
employee without a date of birth, without the contract date the event needs,
and — with a message pointing to the JMHZ registration — on or after
1 April 2026 or for an event dated from that day.

## What each record contains {#output}

| Item | Taken from |
|---|---|
| action (`act`) | *1* start or *2* end |
| date filled in (`dat`) | the day you click *Generate* |
| birth number | *Identification No*, if it has 9 or 10 digits; otherwise left out |
| surname (`sur`), first name (`fir`) | the employee's name: the last word is the surname, everything before it the first name(s); separate first and last name fields (OCA `hr_employee_firstname`) are used when present |
| birth surname | the current surname |
| address | the private address; a trailing number in the street is the house number |
| start / end of the employment (`fro`, `to`) | the current contract's start and end dates |
| kind of activity (`rel`) | always *1* |
| place of work (`per`) | the company's country |

## Limitations {#limitations}

- **Superseded since 1 April 2026** — see [Legal background](#legal).
- The birth surname is the current surname, and a surname of more than one
  word is recognised only with separate first and last name fields.
- Only the two actions start and end; changes and corrections are not
  modelled. The kind of activity is always *1*, also for agreements and
  small-scale employment.
- The dates come from the contract current today, so a back-dated or
  replaced contract can give a different date than the one really notified.
- Schema validation checks the shape of the file, not the content.
