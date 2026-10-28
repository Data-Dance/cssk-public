---
title: SK Social Insurance Statement for Work Agreements (VPP)
summary: The výkaz poistného a príspevkov for employees with an irregular income — in practice the DoVP and DoPČ work agreements — built from the month's payslips and exported as XML checked against the official schema.
verified: 19.0.1.1.1
---

## What it is for {#purpose}

An employee whose legal relationship gives a right to an **irregular income**
(*nepravidelný príjem*) is insured only for old-age and disability pension
insurance, and the employer reports the premiums for such income on a separate
statement, the **VPP** (*Výkaz poistného a príspevkov*). In practice these are
mostly work agreements — *dohoda o vykonaní práce* (DoVP) and *dohoda
o pracovnej činnosti* (DoPČ) — paid irregularly.

This module builds the VPP from the payslips of agreement workers for a month
and exports it as XML for the Sociálna poisťovňa portal. It has the same shape
as the monthly MVP
([module:l10n_sk_hr_payroll_mvp](module:l10n_sk_hr_payroll_mvp)): fund totals
plus one annex row per employee. Like the MVP it reads payslips through
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base)
and works with either Slovak payroll engine — see
[the Slovak payroll guide](module:l10n_sk_hr_payroll_base#declarations).

## Legal background {#legal}

References are to the [Social Insurance Act](law:sk/2003/461).

- **Who it concerns.** For pension insurance, an employee is also a person in
  a legal relationship giving a right to an irregular income —
  [§ 4 ods. 2 písm. a)](law:sk/2003/461#paragraf-4.odsek-2.pismeno-a). Sickness
  and unemployment insurance cover only a regular monthly income
  ([§ 4 ods. 1](law:sk/2003/461#paragraf-4.odsek-1)).
- **The duty to file.**
  [§ 231 ods. 1 písm. g)](law:sk/2003/461#paragraf-231.odsek-1.pismeno-g)
  obliges the employer to submit the *výkaz poistného a príspevkov* for the
  calendar month within the due date of the premiums, broken down by employee
  and fund.
- **The due date.** Premiums on the assessment base of a § 4 ods. 2 písm. a)
  employee are due **by the eighth day of the month following the month in
  which the income was accounted for payment** —
  [§ 143 ods. 1](law:sk/2003/461#paragraf-143.odsek-1).

## Setting it up {#setup}

The same company and employee data as the MVP:

- *Company ID* (IČO), 8 to 12 digits, on the company form;
- *Sociálna poisťovňa variable symbol*, exactly 10 digits — fill it in on the
  VPP form itself. It is stored on the company and shared with the MVP, RLFO
  and ELDP modules, so it is filled in once; changing it needs the right to
  edit companies;
- the employee's **birth number** in *Identification No*;
- the employee's *Agreement Type* (from the Slovak payroll module) set to
  DoVP or DoPČ — this is what puts an employee on the VPP.

## Preparing the statement {#usage}

*Payroll Declarations → SK VPP (work agreements)*, then *New*.

1. Choose the **Year** and **Month**.
2. Click **Generate**. The module takes the company's payslips whose period
   lies within the month, keeps those of employees whose *Agreement Type* is
   DoVP or DoPČ, builds one row per employee, renders the XML and validates it
   against `VPP-v2026.xsd`. If no such payslip exists, it stops with a message.
3. Download the XML, upload it to the portal and click **Mark Submitted**.
   **Reset to Draft** reopens it.

## What the statement contains {#output}

- **Header.** *Číslo výkazu* `MM99RRRR` and *obdobie výplaty príjmov*
  `MMRRRR`, both from the chosen month; statement type R (regular).
- **Funds.** The same rule codes as on the MVP (SICK/SICKEMPLOYER,
  PENSION/PENSIONEMPLOYER, DISABILITY/DISABILITYEMPLOYER,
  UNEMPLOYMENT/UNEMPLOYMENTEMPLOYER, ACCIDENT, GUARANTEEEMPLOYER,
  RESERVEFUNDEMPLOYER). For an irregular income the payslip carries no sickness
  or unemployment amounts, so those rows are zero.
- **Total** (`spoluPoistne`): the sum of the fund rows above. Health
  insurance is not part of it; it is owed to the health insurers.
- **Annex.** Per employee: birth number, period, relationship type
  (*ZECD1N* for DoVP, *ZECD2N* for DoPČ — the irregular-income variants),
  assessment base (*GROSS*), days, hours and the amounts per fund.

## Limitations {#limitations}

- **Selection is by agreement type, not by income regularity.** Every DoVP and
  DoPČ goes on the VPP with an irregular-income code, even one marked as having
  a regular monthly income (which belongs on the MVP with code ZECD1/ZECD2).
  Since the MVP does not leave agreements out, such a worker appears on both
  statements. A student agreement (DoBPŠ) is never put on the VPP.
- The agreement type is read from the employee's current contract, not from
  the contract the payslip was computed on.
- Draft payslips count; only cancelled ones are left out. A payslip whose
  period crosses the month boundary is ignored. The month is the payslip
  period, which may differ from the month in which the income was accounted
  for payment.
- Days are the full calendar month for every row; the assessment-base
  exception flag is always 0.
- Only a regular statement; corrections go through the portal. Only the
  VPP 2026 vintage is shipped.
- Schema validation checks the shape of the file, not the figures.
