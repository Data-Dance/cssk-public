---
title: SK Monthly Health Insurance Statement (dávka 514)
summary: The monthly výkaz preddavkov na poistné for a Slovak health insurer (VšZP, Dôvera, Union) in the common dávka 514 format, built from the month's payslips and exported as XML.
verified: 19.0.1.2.6
---

## What it is for {#purpose}

Every month the employer reports to each **health insurer** the health
insurance advances (*preddavky na poistné*) it pays for its employees and for
itself: the *mesačný výkaz preddavkov na poistné*. All three Slovak insurers —
**VšZP** (25), **Dôvera** (24) and **Union** (27) — accept it in the same
electronic format, **dávka 514**.

This module builds the dávka 514 from the payslips of the month and exports
it as an XML file to upload through the insurer's electronic branch. Payslips
are read through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
so it works with either Slovak payroll engine — see
[the Slovak payroll guide](module:l10n_sk_hr_payroll_base#declarations).

## Legal background {#legal}

References are to the [Health Insurance Act](law:sk/2004/580) (*zákon
o zdravotnom poistení*).

- **The statement.** The employer reports to the competent health insurer
  the advances for the calendar month, broken down by the employees for whom
  it pays them and for the employer itself (the *mesačný výkaz*). It states
  the total income, the income for and the amount of the deductible item, tax-
  exempt payments, the assessment base and the advance, and must be sent
  **electronically** — [§ 20 ods. 1](law:sk/2004/580#paragraf-20.odsek-1).
- **The due date of the advances.** The employee's and employer's advances
  are due on the day fixed for paying out the employees' income for the month;
  if no such day is fixed, on the last day of the following month —
  [§ 17 ods. 1](law:sk/2004/580#paragraf-17.odsek-1).
- **Corrections.** Data the insurer rejects in its error report (*chybový
  protokol*) must be corrected electronically within 30 days of receiving it —
  [§ 24 ods. 1 písm. m)](law:sk/2004/580#paragraf-24.odsek-1.pismeno-m).

## Setting it up {#setup}

On the company:

| Value | Where | Used as |
|---|---|---|
| *Company ID* (IČO), 8 to 12 digits | company form | `IDCode`, `CompanyIDCode` |
| *DIČ*, 10 digits | company form (from the Slovak base module) | `CompanyIDTaxCode` |
| *Health payer number* | company form, or the dávka 514 form | `CodeOfPayer` — the number the insurer assigned to the employer |
| *Health insurer (dávka 514)* | company form | the default insurer of a new statement (VšZP if not set) |
| a bank account | the company's contact | `IBAN` — the first account is used |

Both health fields sit on the company form, tab *Payroll Reporting*, group
*Health insurance (dávka 514)*. The *Health payer number* can also be filled
in on the dávka 514 form itself; it is stored on the company either way, so it
is entered once (changing it needs the right to edit companies).

Every employee on the statement needs the **birth number** in *Identification
No*, and should carry their **Health insurer (SK)**, next to it on the
*Personal* tab. Each dávka 514 takes only the employees insured with the
insurer it is addressed to; an employee whose insurer is left empty counts as
insured with the company's default insurer (VšZP unless changed). Set the
insurer on every employee rather than relying on the default.

## Preparing the statement {#usage}

*Payroll Declarations → SK dávka 514 (health)*, then *New*.

1. Choose the **Health insurer**, the **Year** and the **Month**. *Payment
   Date* gives the day of payment reported in `DateOfPayment`; left empty, the
   last day of the month is used.
2. Click **Generate**. The module takes the company's confirmed payslips
   whose period ends in the month, builds one row per employee and renders the XML.
3. Upload the file through the insurer's electronic branch and click **Mark
   Submitted**. **Reset to Draft** reopens it.

Generation stops if the IČO, the DIČ, the payer number or the insurer is
missing, if an employee has no valid birth number, or if there are no payslips
for the month.

**Who is left out.** A DoVP or DoPČ worker is not reported, and does not
count as an employee of the insurer, when the contract the payslip was
computed on has either
- a **Pension granted (SK)**: the statute excludes agreement income of every
  pensioner group the field offers, with no income limit or claim
  ([§ 10b ods. 1 písm. a)](law:sk/2004/580#paragraf-10b.odsek-1.pismeno-a)); or
- **Health-insurance exempt** ticked without a pension, for example a worker
  covered by another state's legislation (an A1 form). Keeping that evidence
  is up to you.

An ordinary employment contract stays on the statement even with a pension.
A DoVP or DoPČ with a pension but *Health-insurance exempt* not ticked stops
generation: its payslip carries health advances for income the statute
excludes. Tick the box on that contract and recalculate the payslip. The check
covers only the insurer the statement is addressed to.

## What the statement contains {#output}

| Part | Content |
|---|---|
| `Identification` | type 514, character *N*, IČO, payer number, the insurer's four-digit code (2500, 2400, 2700), date of sending, serial number 1, number of rows |
| `CorporateBody` | period, day of payment, company name, IČO, payer number, DIČ, IBAN |
| `InsuranceBody` | employer totals in two groups, employees without and with a health disability: the number of employees an advance is paid for, days, income, the employees' assessment base and the employer's and the employees' advances of each group; then the grand total |
| `PersonData` | per employee: birth number, days, the employer's and employee's rate, income, the employee's assessment base, advances, the income for the deductible item, other income, the deductible item, whether no minimum advance applies, and the minimum top-up |

The amounts come from the payslip lines: *HEALTHEMPLOYER* (employer's
advance), *HEALTH* (employee's advance) and the health minimum top-up
(*HEALTHDOPLATOK* or *HEALTH_DOPLATOK*, depending on the engine). What each
figure contains follows § 1 ods. 3 of vyhláška č. 159/2018 Z. z. and the item
descriptions in the schema:

- **Groups.** An employee whose contract has *ZŤP / Disabled* ticked is
  reported in the second group, the one with the reduced rates of
  [§ 12](law:sk/2004/580#paragraf-12.odsek-1); everyone else in the first.
  The employees' advance of a group includes the minimum top-up, which raises
  the employee's advance
  ([§ 16a ods. 4](law:sk/2004/580#paragraf-16a.odsek-4)).
- **Days.** The calendar days of employment in the month without the days of
  sick leave, nursing, maternity and paternity leave, for which the State
  pays ([§ 11 ods. 7 písm. m)](law:sk/2004/580#paragraf-11.odsek-7.pismeno-m)),
  and without the days of parental and unpaid leave, on which a person
  without income is not an employee
  ([§ 11 ods. 3](law:sk/2004/580#paragraf-11.odsek-3)). They are read from
  the approved time off of the Slovak leave types; a day of leave taken in
  part (half a day, some hours) is not removed. When the payslip carries the *PN_DAYS* input, the sick days
  are taken from it, as the payslip takes them. An employee with no such day
  and no advance is listed, and is not counted among those an advance is paid
  for.
- **Income and base.** The income is the payslip's *GROSS*; it is also the
  employer's base ([§ 13 ods. 4](law:sk/2004/580#paragraf-13.odsek-4)). The
  employee's base is the income less the deductible item
  ([§ 16 ods. 16 to 18](law:sk/2004/580#paragraf-16.odsek-16)). The base, the
  item and the two rates are the ones the payslip recorded when it was
  computed. The income of an employment relationship is the income for the
  deductible item; the income of an agreement (DoVP, DoPČ, DoBPŠ) is other
  income.
- **No minimum advance.** `NotAppliedMinimum` is set where the payslip
  computes no minimum for the whole month — a disabled employee, a
  health-exempt contract, a DoBPŠ — or where the month has no day an advance
  is paid for, and no top-up was charged.

**Checking the file.** The official schema `514-2023.xsd` contradicts itself
(patterns that admit only one digit in fields that must be 8 to 12 characters
long, impossible numeric limits), so no real file can pass it. The module
therefore runs it without stopping and checks the structure instead: the root
element, the three header blocks and that the number of rows matches.

## Limitations {#limitations}

- **The insurer is a property of the employee, not of the month.** A change
  of insurer during the year (allowed once a year, from 1 January) has to be
  recorded on the employee before generating; past statements are not
  recomputed.
- **The deductible item needs the fund bases the payslip recorded.** A
  payslip computed before the Slovak payroll recorded them (OCA engine
  19.0.1.25.0, Enterprise engine 19.0.1.26.0), or whose lines were changed
  afterwards, is reported on its gross: no item, and rates worked back as
  advance ÷ gross. The statement names the payslips reported this way;
  correct the row of an employee who claims the item by hand.
- **The minimum top-up is the one the payslip charged.** The payslip reduces
  the minimum advance for sick days and days outside the contract only, so
  in a month with nursing, maternity, parental or unpaid leave the top-up is
  higher than the days on the statement give.
- **One row per employee record.** A person kept as two employees (two
  concurrent contracts) gets two rows with the same birth number. Income paid
  after the employment ended is not separated as other income.
- Disability is the tick on the contract the payslip was computed on; there
  is no date of the decision.
- Only a regular statement (*N*) with serial number 1. Corrections after an
  error report must be made through the insurer's electronic branch.
- Because the official schema cannot be applied, the module cannot guarantee
  that the insurer will accept the file. Reconcile the first statement with
  the insurer.
