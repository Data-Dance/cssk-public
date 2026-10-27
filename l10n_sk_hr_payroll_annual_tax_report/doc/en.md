---
title: SK Annual Tax Report (Hlásenie)
summary: The employer's annual report on employment income, withheld tax advances and the child tax bonus, with one annex column per employee, generated from the year's payslips as XML for the Slovak financial administration.
verified: 19.0.2.0.2
---

## What it is for {#purpose}

After the end of each year a Slovak employer that withholds income tax files
the **Hlásenie o vyúčtovaní dane a o úhrne príjmov zo závislej činnosti**
(report on the tax settlement and total employment income) with its tax
office. It sums up the year's wages, withheld tax advances and child tax
bonuses, and lists every employee with their own figures.

This module builds the report from the payslips of the calendar year and
exports it as XML in the Finančná správa's format. Like its monthly
counterpart,
[module:l10n_sk_hr_payroll_monthly_tax_overview](module:l10n_sk_hr_payroll_monthly_tax_overview),
it works with either payroll engine (see the
[Slovak payroll family](module:l10n_sk_hr_payroll_base#declarations)), and it
shares its screens, states and XML checks with the other payroll returns
through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base).

## Legal background {#legal}

References are to the [Income Tax Act](law:sk/2003/595) (*zákon o dani z
príjmov*). Statutory terms are given in Slovak.

- **The obligation.** An employer that is a *platiteľ dane* submits a
  *hlásenie* on the tax settlement and the total employment income provided to
  individual employees in the past tax period, on the withheld advances, the
  *zamestnanecká prémia*, the *daňový bonus* and the *daňový bonus na
  zaplatené úroky* —
  [§ 39 ods. 9 písm. b)](law:sk/2003/595#paragraf-39.odsek-9.pismeno-b).
  The same provision requires each employee's name, surname and **birth
  number** (*rodné číslo*) — which is why the module refuses to generate the
  report for an employee without one.
- **The deadline.** The *hlásenie* is filed by the **end of April** after the
  end of the tax period — [§ 49 ods. 2](law:sk/2003/595#paragraf-49.odsek-2).
  The report for 2026 is due by 30 April 2027.

## Setting it up {#setup}

- **DIČ of the company.** Fill in *DIČ* (the 10-digit tax identification
  number) on the company; generation stops with an error without it.
- **Company address, phone and e-mail** go into the header. *Street* fills the
  street element and *Street2* the house-number element.
- **Every employee needs a birth number.** Enter it, 9 or 10 digits, in
  *Identification No* on the *Personal* tab of the employee form. Slashes and
  spaces are ignored.
- **Employee names and addresses.** The annex takes the employee's private
  street, ZIP and city. The **last word of the name is the surname** and
  everything before it the first name, so record names as "Ján Peter Novák",
  not "Novák Ján". With `hr_employee_firstname` installed, its separate first
  and last name fields are used instead.
- The form vintage **Annual tax reconciliation statement 2023+** (the
  `HLASENIEv23` schema, valid from 1 January 2023) is installed with the module
  and selected automatically.

## Filing a year {#usage}

*Payroll Declarations → SK annual tax reconciliation statement*, then *New*.

1. Choose the **Year**. The period is always 1 January to 31 December.
2. Leave **Correction Type** on *Regular* for the ordinary filing.
3. Click **Generate**. The module collects every non-cancelled payslip of the
   company whose period lies in the year — **drafts included** — builds one
   annex column per employee, renders the XML and validates it against the
   official schema `rh2023.xsd`. If an employee lacks a birth number, the
   error names them and nothing is generated.
4. Download the XML from *Xml Attachment* and upload it to the Finančná
   správa portal yourself.
5. Click **Mark Submitted** once filed; the filed copy is kept and the record
   locked. *Reset to Draft* unlocks it.

## What goes onto the form {#mapping}

**Part I (employer totals):**

| Row | Filled with |
|---|---|
| r. 00 | the sum of `GROSS` for the year |
| r. 01 | the withheld advance before the bonus: `INCOMETAX19` + `INCOMETAX25` on Enterprise, `INCOMETAX` on the OCA engine |
| r. 04 | equal to r. 01 (rows 02 and 03 are left empty) |
| r. 05 | the sum of `CHILD_BONUS`, capped at r. 04 |
| r. 06 | the employee premium — always 0.00, as no payroll rule produces it |

**Part III (recapitulation of the child tax bonus):**

| Row | Filled with |
|---|---|
| r. A | the whole child bonus paid in the year (sum of `CHILD_BONUS`) |
| r. B | the part paid out of the withheld advances — equal to r. 05 |
| r. C | r. A − r. B: the bonus the company paid from its own money because it exceeded the advances |

**Part V (per employee), two employees per page:** birth number, name,
private address, state `SK`, taxable income (r. 3a, from `GROSS`), withheld
advances (r. 4a), employee premium (r. 6) and the child bonus paid (r. 8).
With an odd number of employees the last page has an empty second column.

Part IV is never filled: every employee goes into Part V. Part II, rows D–F
of Part III,
the remaining rows of Part I, the number of children per employee, and the
counts and sums of the § 33a interest bonus and of the recreation allowance in
the header are left empty.

## Corrections {#corrections}

The report accepts *riadne*, *opravné* and *dodatočné* filings. Set
**Correction Type** to *Corrective* or *Supplementary*. The module refuses an
amending report unless a regular one is already marked submitted — but see
[Limitations](#limitations): it currently looks for that original in the
**same month** in which the new record was created.

## Limitations {#limitations}

- **Check the figures before filing.** The schema check proves the shape of
  the file, not the amounts. No report produced here has been confirmed by a
  live submission; reconcile the first one by hand, and check the column
  meanings against the current official instructions (*poučenie*) for the
  year you file.
- **Two-word surnames.** Without separate name fields, only the last word is
  taken as the surname; check Part V for an employee with a two-word surname.
- **Row 5 and Part III are capped on the year's totals.** Row 5 is the
  smaller of the year's bonus and row 4. If in some months the bonus exceeded
  that month's advances and you claimed the difference back through the
  monthly overviews instead of offsetting it later, compare rows 5 and C with
  your monthly filings before submitting.
- The annex state is always `SK`; foreign residents and employees taxed by
  withholding (*zrážková daň*) are not treated separately.
- **The annual reconciliation (*ročné zúčtovanie*) is not reported.** Rows
  for its results, the number of children per employee, insurance
  contributions and non-taxable parts of the base are left empty.
- **Draft payslips count**, and payslips are taken by their period, not by the
  payout date.
- **Amending reports and the month.** A corrective or supplementary report
  finds its original only if it was created in the same calendar month as the
  submitted original; otherwise generation is refused with "There is no
  submitted … to amend". The date the reasons for a *dodatočné hlásenie* were
  found is left empty.
- The legal-form element of the header is the *Právna forma* recorded on the company's contact by `l10n_sk_trade_registry`; without that module, or with the field empty, the element stays empty.
- Only the 2023 vintage ships. Check that the Finančná správa still accepts it
  for the year you are filing.
- Nothing is sent to the authority: *Mark Submitted* only records that you
  filed it.
