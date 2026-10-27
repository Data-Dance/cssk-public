---
title: SK Monthly Social Insurance Statement (MVP)
summary: The monthly výkaz poistného a príspevkov for the Sociálna poisťovňa, built from the month's payslips — fund totals and a per-employee annex, exported as XML checked against the official schema.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Every month a Slovak employer reports to the **Sociálna poisťovňa** what it
owes in social-insurance premiums and old-age pension savings contributions:
the *Mesačný výkaz poistného a príspevkov* (**MVP**, filed electronically as
*MVPP*). The statement gives one employer/employee pair of amounts per fund and
an annex with one row per employee.

This module builds that statement from the payslips of the month and exports
it as an XML file you upload to the Sociálna poisťovňa portal. It reads the
payslips through the shared
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
so it works with either Slovak payroll engine — see
[the Slovak payroll guide](module:l10n_sk_hr_payroll_base#declarations).

Work agreements with an irregular income are reported on a different
statement, the VPP — see [module:l10n_sk_hr_payroll_vpp](module:l10n_sk_hr_payroll_vpp).

## Legal background {#legal}

References are to the [Social Insurance Act](law:sk/2003/461) (*zákon
o sociálnom poistení*).

- **The duty to file.** Under
  [§ 231 ods. 1 písm. g)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-g) the
  employer must submit the *výkaz poistného a príspevkov na starobné
  dôchodkové sporenie* for each calendar month, **within the due date of the
  premiums it pays**, stating the day fixed for paying out the income that
  forms the employees' assessment base, broken down by employee and by fund
  (sickness, old-age and pension savings, disability, accident, guarantee,
  unemployment, short-time work support, solidarity reserve fund), and naming
  the natural person who deals with the Sociálna poisťovňa. A wrong statement
  is corrected with an *opravný výkaz* (point 2 of the same letter).
- **The due date.** Premiums the employer pays are due on the day fixed for
  paying out the employees' income; if no such day is fixed, on the last day
  of the following month —
  [§ 143 ods. 2](law:sk/2003/461#paragraf-143.odsek-2).
- [§ 231 ods. 2](law:sk/2003/461#paragraf-231.odsek-2) leaves the form and the
  way of sending it to the Sociálna poisťovňa, which publishes the XML schema
  this module validates against.

## Setting it up {#setup}

Two company values must be filled in before the first statement:

| Value | Where | Used as |
|---|---|---|
| *Company ID* (IČO), 8 to 12 digits | company form | `<identifikator>` |
| *Sociálna poisťovňa variable symbol*, exactly 10 digits | see below | `<variabilnySymbol>` — the number the Sociálna poisťovňa assigned to the employer |

Fill in the *Sociálna poisťovňa variable symbol* on the MVP form itself. It is
stored on the company and shared with the VPP, ELDP and RLFO modules, so it is
entered once; changing it needs the right to edit companies.

For every employee on the statement, the **birth number** (*rodné číslo*, 9 or
10 digits; slashes and spaces are ignored) must be in the employee's
*Identification No* field.

The phone number and e-mail of the contact person are taken from the company;
the contact person's name is the name of the user who generates the
statement.

## Preparing the statement {#usage}

*Payroll Declarations → SK MVP (social)*, then *New*.

1. Choose the **Year** and **Month**. *Payment Date* is the payday reported in
   `<denVyplaty>`; left empty, the last day of the month is used.
2. Click **Generate**. The module collects the company's payslips whose period
   lies within the month, builds one row per employee, renders the XML and
   validates it against the shipped schema `MVPP-v2026.xsd`. The XML is
   attached to the record (*Xml Attachment*) and the record moves to
   *Generated*.
3. Download the XML, upload it to the Sociálna poisťovňa portal, then click
   **Mark Submitted**. The filed copy is kept, and a submitted statement can
   be neither regenerated nor deleted until it is reset.

**Reset to Draft** reopens the statement — for instance after correcting a
payslip — and *Generate* then rebuilds it from scratch.

Generation stops with a message if the company has no IČO or no valid variable
symbol, if an employee has no valid birth number, or if there are no payslips
for the month.

## What the statement contains {#output}

Each fund is taken from the payslip lines with a fixed salary-rule code:

| Fund (element) | Employer | Employee |
|---|---|---|
| nemocenské poistenie (`np`) | SICKEMPLOYER | SICK |
| starobné poistenie (`sp`) | PENSIONEMPLOYER | PENSION |
| invalidné poistenie (`ip`) | DISABILITYEMPLOYER | DISABILITY |
| poistenie v nezamestnanosti (`pvn`) | UNEMPLOYMENTEMPLOYER | UNEMPLOYMENT |
| úrazové poistenie (`up`) | ACCIDENT | — |
| garančné poistenie (`gp`) | GUARANTEEEMPLOYER | — |
| rezervný fond solidarity (`rfs`) | RESERVEFUNDEMPLOYER | — |
| podpora v čase skrátenej práce (`pfp`) | SHORTTIMEEMPLOYER | — |

The total (`spoluPoistne`) is the sum of these rows. Health insurance is not
part of it — it goes to the health insurer on the dávka 514
([module:l10n_sk_hr_payroll_health](module:l10n_sk_hr_payroll_health)).

Each annex row carries the birth number, the assessment base (the employee's
*GROSS* for the month), the number of days, the hours from the payslips' worked
days, and the employee's amounts per fund.

## Limitations {#limitations}

- **Only a regular statement** (`typVykazu` R). An *opravný výkaz* cannot be
  produced; file corrections through the portal.
- **Every payslip of the month counts**, including drafts — only cancelled
  payslips are left out. Generate the statement once payroll is final. A
  payslip whose period crosses the month boundary is not picked up at all.
- **Work agreements are not left out.** The MVP takes every employee with a
  payslip, while the VPP takes every DoVP and DoPČ. An agreement worker paid in
  the month therefore appears on both statements; remove the duplicate before
  filing.
- Every annex row uses the relationship type *ZEC* (employee with a regular
  income), the assessment-base exception flag `vynimkaVZ` set to 0, and the full number of
  calendar days in the month, even for someone who joined or left during it.
- The assessment base is the payslip's *GROSS*, not a figure computed under
  the Social Insurance Act; the maximum assessment base is not applied here.
- The only form vintage shipped is MVPP 2026 (valid from 1 January 2026); an
  earlier period is also exported in that layout.
- Schema validation checks the shape of the file, not the figures. Reconcile
  the first statement you file with the payslips by hand.
