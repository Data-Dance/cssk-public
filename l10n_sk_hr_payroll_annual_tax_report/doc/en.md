---
title: SK Annual Tax Report (Hlásenie)
summary: The employer's annual report on employment income, withheld tax advances and the child tax bonus, with one annex column per employee, generated from the year's payslips as XML for the Slovak financial administration.
verified: 19.0.2.1.1
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
- **Company address, phone and e-mail** go into the header. The house
  number is taken from the end of *Street* (*Hlavná 12*, *Hlavná 1141/11*);
  *Street2* is used only when it holds nothing but a number — a building, a
  floor or a c/o line there is never filed as the house number.
- **Every employee needs a birth number.** Enter it, 9 or 10 digits, in
  *Identification No* on the *Personal* tab of the employee form. Slashes and
  spaces are ignored.
- **Employee names and addresses.** The annex takes the employee's private
  street (its house number split off the same way), ZIP and city. The **last
  word of the name is the surname** and everything before it the first name,
  so record names as "Ján Peter Novák", not "Novák Ján". With `hr_employee_firstname` installed, its separate first
  and last name fields are used instead.
- The form vintage **Annual tax reconciliation statement 2023+** (the
  `HLASENIEv23` schema, valid from 1 January 2023) is installed with the module
  and selected automatically.

## Filing a year {#usage}

*Payroll Declarations → SK annual tax reconciliation statement*, then *New*.

1. Choose the **Year**. The period is always 1 January to 31 December.
2. Leave **Correction Type** on *Regular* for the ordinary filing.
3. Click **Generate**. The module collects every non-cancelled payslip of the
   company whose period lies in the year — **confirmed payslips only** — builds one
   annex column per employee, renders the XML and validates it against the
   official schema `rh2023.xsd`. If an employee lacks a birth number, the
   error names them and nothing is generated.
4. Download the XML from *Xml Attachment* and upload it to the Finančná
   správa portal yourself.
5. Click **Mark Submitted** once filed; the filed copy is kept and the record
   locked. *Reset to Draft* unlocks it.

## Annex mapping and verified scope {#mapping}


Version 19.0.2.1.0, 7 November 2026. Uses the bundled, unchanged rh2023 XSD.
This is not certification of a later form edition or acceptance by the authority.

Part IV reports this employer's income for employees without employer annual
reconciliation (RZD). Part V reports annual reconciliation data, including all
employers' income separately from this employer's contribution. Its r4a/r4b are
employee social/health insurance; withheld advance belongs to r6. The old export
sent every employee to Part V and placed advance tax in r4a.

The country report remains engine-neutral. `_annual_settlement_column(line)`
is the engine bridge: return `None` for Part IV, or reviewed Part V values using
the QWeb column keys and `completed_on` (DD.MM.YYYY). If an installed engine
exposes a computed/posted RZD but has no bridge, export stops. Completion of RZD
is distinct from subsequent payment of its balance. Foreign residence and child
bonus without full child identity/entitlement-month data are explicit open
adapters, never silently omitted.

Part IV month flags use the selected payroll intervals and historical versions.
Date-of-payment/tax-year selection must be supplied by the applicable payroll
adapter; this patch does not claim that a payslip date alone proves payment.
Parts IV/V have independent employee/page counts and odd-column padding.

Legal mapping: Finančná správa HLASENIEv23 instructions, Parts IV and V:
https://pfseform.financnasprava.sk/Formulare/Poucenia/HLASENIEv23-poucenie.pdf

Tests exercise native OCA payroll, XML/XSD, independent sections, proper row
meanings and the explicit missing-information guards. Enterprise runtime is not
claimed tested by an OCA run. The general bridge regression supplies a reviewed
adapter fixture; production annual calculation belongs to the engine bridge.

## Corrections {#corrections}

The report accepts *riadne*, *opravné* and *dodatočné* filings. Set
**Correction Type** to *Corrective* or *Supplementary*. The module refuses an
amending report unless a regular one is already marked submitted — but see
[Limitations](#limitations): it currently looks for that original in the
**same month** in which the new record was created.

## Form edition cutoff

Version 19.0.2.1.1 limits rh2023 / HLASENIEv23 to tax years through 2025,
including an upgrade migration for existing version records. Export for 2026+
is rejected. The Ministry's 2026 form changes Part V row meanings; a successful
old XSD check cannot prove compliance with the new form. Install a reviewed
current form adapter before filing. This module does not yet supply that adapter.

Source: https://www.mfsr.sk/files/archiv/75/HLASENIEv26-v1.2.pdf

