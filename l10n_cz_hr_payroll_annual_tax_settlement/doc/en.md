---
title: CZ Annual Statement of Employment Income Tax (DPZVD)
summary: The employer's annual vyúčtování daně z příjmů ze závislé činnosti for the Finanční správa — the year's tax advances by month, the monthly employee counts and Příloha č. 1 (employees per municipality), as EPO XML in the DPZVD6 structure.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

Every employer that paid employment income in a year files the
*vyúčtování daně z příjmů fyzických osob ze závislé činnosti vybírané
srážkou formou záloh* — the annual statement of the income tax advances it
withheld — with its tax office.

This module prepares that statement for a calendar year from the year's
payslips and exports it as EPO XML (`<Pisemnost>` with one `<DPZVD6>`),
checked against the shipped `dpzvd6_epo2.xsd`. Payslips are read through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base),
so it works with either Czech payroll engine — see
[the Czech payroll guide](module:l10n_cz_hr_payroll_base#declarations).

It is **not** the employee's annual tax reconciliation (*roční zúčtování
záloh*): that is done per employee in the payroll module itself.

**It fills in only part of the statement** — see
[Limitations](#limitations).

## Legal background {#legal}

References are to the [Income Taxes Act](law:cz/1992/586).

- **Who files.** A payer of tax that paid or accounted for employment income
  in the tax period files the statement with its local tax office
  (§ 38j odst. 4), also when, because of tax credits, it had no tax to pay
  over (§ 38j odst. 9).
- **When.** Within two months after the end of the calendar year, or by
  **20 March** when filed electronically (§ 38j odst. 5). The time limit
  cannot be extended (§ 38j odst. 7).
- **Annexes.** The statement has annexes: the number of employees at
  1 December by municipality of work, an overview of tax non-residents, and
  overviews of corrections (§ 38j odst. 8). The module produces the first,
  *Příloha č. 1 — Počet zaměstnanců* (§ 38j odst. 1); the others it does not.
- **Part I, column 1** of the form (`kc_dpzi01`) is, according to the
  instructions to the form (*pokyny k vyplnění*, MFin 5459/1), the total of
  the advances **after the monthly tax credits** (§ 35ba, § 35c and § 35d)
  that should have been withheld for each month; **column 5** the monthly
  tax bonuses paid. Part II row 1 is the total of column 1 and row 4 the
  total of column 5.
- **Number of employees** (item 05) is counted per month "k poslednímu dni
  měsíce" — on the last day of the month.
- **Příloha č. 1** counts the employees on 1 December by the municipality of
  their place of work, identified by its ZÚJ code (*základní územní
  jednotka*). For an agreement worker (DPP, DPČ) the place of work is the
  employer's seat.

## Setting it up {#setup}

On the company:

| Value | Used as |
|---|---|
| *Tax ID* (DIČ) | `dic` in `VetaP`: its digits, at most 10 |
| *Tax office code (FÚ)*, 1 to 4 digits | `c_ufo_cil`, the tax office the statement goes to |
| *Filing subject type* | `typ_ds`: *F — natural person*, *P — legal entity* (default) or *L — payer's cashier* |
| *Municipality code (ZÚJ)*, 6 digits, and *Municipality name (ZÚJ)* | the municipality of the company's own address (seat) in Příloha č. 1 |
| name, city, ZIP | the payer's identification |

*Tax office code (FÚ)*, *Filing subject type* and the two ZÚJ fields are on
the **Payroll Reporting** tab of the company form (see
[the declaration base](module:l10n_cssk_payroll_declaration_base#company)).

For Příloha č. 1, every address that is an employee's place of work needs a
ZÚJ code as well. The place of work is the **Work Address** on the
employee's contract version; agreement workers (DPP, DPČ) and employees
without a work address count at the company's own address. On a Czech
contact or address, *Municipality code (ZÚJ)* and *Municipality name (ZÚJ)*
are on the *Sales & Purchase* tab, in the *Misc* group. Take the code and
the name from the Finanční správa register *Obce ZUJ*.

## Preparing the statement {#usage}

*Payroll Declarations → CZ Annual tax settlement (income tax)*, then *New*.

1. Choose the **Year**. The period is 1 January to 31 December.
2. Click **Generate**. Every confirmed payslip of the company whose period
   ends within the year is collected (drafts and cancelled ones are not
   counted; see [the declaration base](module:l10n_cssk_payroll_declaration_base#payslips)),
   the XML is built,
   validated against the schema and attached.
3. Open the XML in the EPO application of the Finanční správa, complete the
   parts the module leaves out, file it, and click **Mark Submitted**.

Generation stops if the company has no DIČ or no tax office code, or if the
year has no payslips. It also stops, listing the addresses, when a place of
work counted in Příloha č. 1 has no 6-digit ZÚJ code.

## What the statement contains {#output}

| Item | Taken from |
|---|---|
| tax period, form `VD6`, type `B` (regular) | the year |
| Part I, one row per month (`VetaO`): columns 1 and 2 | the advance after the monthly credits: the payslips' *income tax* line (`INCOMETAX`) less the taxpayer credits (`TAXCREDIT`) and the child tax benefit set against the tax (`CHILDBEN`) — the same amount in both columns |
| Part I, column 5 (`kc_dpzi05`) | the child tax bonuses paid in that month (`CHILDBONUS`), when there are any |
| Part II, row 1 (`kc_dpzii01`) | the total of column 1 |
| Part II, row 4 (`kc_dpzii03a`) | the total of column 5, when there is any |
| number of employees per month (`poc_zam1`–`poc_zam12`) | employees with a payslip in that month whose employment still runs on the last day of the month |
| payer (`VetaP`) | DIČ, name, city, ZIP, filing subject type |
| Příloha č. 1 (`VetaB`), one row per municipality | the employees with a confirmed payslip in the year who are employed on 1 December, counted by the ZÚJ code (and name) of their place of work |

A payslip is assigned to the month in which its period ends.

## Limitations {#limitations}

- **Only Part I columns 1, 2 and 5, Part II rows 1 and 4.** The other rows
  of Part II (annual reconciliations, refunds, corrections, amounts paid
  over), the other columns of Part I, the annexes other than Příloha č. 1
  and the overviews of non-residents (`VetaC`, `VetaH`) are left for you to
  complete.
- **Withholding tax** at the special rate (on small *dohody*) is not
  included; it is reported on a separate statement the module does not
  produce.
- **Employee counts** start from the employees with a payslip in the
  month; someone still employed on the last day but with no payslip that
  month is not counted.
- Column 2 (advances originally withheld) always equals column 1, so
  corrections made under § 38i are not shown.
- Only a regular statement (type *B*); a corrective or supplementary one
  has to be prepared in EPO. The schema is a single file with a fixed
  `verzePis` of *1.0*; nothing in the module checks that it is still the
  current one.
- Schema validation checks the shape of the file, not the figures. No
  statement from this module has been confirmed by a live filing.
