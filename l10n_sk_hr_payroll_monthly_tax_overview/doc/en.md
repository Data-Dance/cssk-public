---
title: SK Monthly Tax Overview (Prehľad)
summary: The monthly overview of income-tax advances withheld from employees and the child tax bonus paid, generated from the month's payslips as XML for the Slovak financial administration.
verified: 19.0.2.1.1
---

## What it is for {#purpose}

Every Slovak employer that withholds income tax from wages files, each month, a
**Prehľad o zrazených a odvedených preddavkoch na daň** (overview of withheld
and remitted tax advances) with its tax office. This module builds that
overview from the payslips of the month and exports it as XML in the
Finančná správa's own format, ready to upload to its portal.

It works with either payroll engine — Odoo Enterprise payroll or the OCA
payroll app — because it reads only what both put on a payslip (see the
[Slovak payroll family](module:l10n_sk_hr_payroll_base#declarations)). The
annual counterpart is
[module:l10n_sk_hr_payroll_annual_tax_report](module:l10n_sk_hr_payroll_annual_tax_report).
The screens, states and XML checks it shares with the other payroll returns
come from
[module:l10n_cssk_payroll_declaration_base](module:l10n_cssk_payroll_declaration_base).

## Legal background {#legal}

References are to the [Income Tax Act](law:sk/2003/595) (*zákon o dani z
príjmov*). Statutory terms are given in Slovak.

- **The obligation.** An employer that is a *platiteľ dane* must submit a
  *prehľad* of the tax advances it withheld and remitted from employment
  income it paid out, and of the *zamestnanecká prémia*, the *daňový bonus*
  and the *daňový bonus na zaplatené úroky*, for the past calendar month —
  [§ 39 ods. 9 písm. a)](law:sk/2003/595#paragraf-39.odsek-9.pismeno-a).
- **The deadline.** The *prehľad* is filed by the end of the calendar month
  for the previous calendar month —
  [§ 49 ods. 2](law:sk/2003/595#paragraf-49.odsek-2). The overview for
  October is therefore due by 30 November.
- **Remitting the advances.** Separately from the overview, the advances,
  reduced by the child tax bonus, must be remitted no later than five days
  after the day the wage is paid out —
  [§ 35 ods. 6](law:sk/2003/595#paragraf-35.odsek-6). This module does not
  create that payment.
- **The child tax bonus** (*daňový bonus*) itself is set by
  [§ 33](law:sk/2003/595#paragraf-33); the payroll computes it, this module
  only reports what the payslips paid.

## Setting it up {#setup}

- **DIČ of the company.** Fill in *DIČ* (the 10-digit tax identification
  number) on the company. Generation stops with an error until it is there.
- **Company address, phone and e-mail** go into the header of the overview. The house
  number is taken from the end of *Street* (*Hlavná 12*, *Hlavná 1141/11*);
  *Street2* is used only when it holds nothing but a number — a building, a
  floor or a c/o line there is never filed as the house number.
- **Bank account.** The first bank account of the company's partner is
  written into Part III as the account for a refund. It is required when you
  request one (see [Claiming the bonus difference back](#bonus-refund)).
- The form vintage **Monthly tax overview 2026** (valid from 1 January 2026)
  is installed with the module and selected automatically. It is listed under
  *Payroll Declarations → Configuration → Declaration Versions*.

## Filing a month {#usage}

*Payroll Declarations → SK monthly tax overview*, then *New*.

1. Choose the **Year** and **Month**. *Payment Date* is the payout date
   reported on row 01; it defaults to the last day of the month if left empty.
2. Leave **Correction Type** on *Regular* for the ordinary filing.
3. Click **Generate**. The module collects every payslip of the company whose
   period falls within the month and that is **not cancelled** — drafts
   included — sums the rule totals, renders the XML and validates it against
   the official schema `prehlad2026.xsd`. If any of this fails, nothing is
   attached and the error says why.
4. The XML appears in *Xml Attachment* and the state becomes *Generated*.
   Download it and upload it to the Finančná správa portal yourself.
5. Click **Mark Submitted** once filed. The filed copy is kept in *Filed XML*
   and *Filed history*, and the record is locked; *Reset to Draft* unlocks it
   for regeneration while keeping the filed copy.

The list of employees on the form shows who contributed to the figures and
their gross wage; the overview itself is employer-level only and carries no
per-employee data.

## What goes onto the form {#mapping}

| Row of the overview | Filled with |
|---|---|
| r. 00 — úhrn zúčtovaných a vyplatených zdaniteľných príjmov | the sum of the `GROSS` rule over the month's payslips |
| r. 01 — preddavky na daň (date and amount) | *Payment Date*, and the withheld advance before the bonus: `INCOMETAX19` + `INCOMETAX25` on Enterprise, `INCOMETAX` on the OCA engine |
| r. 04 | equal to r. 01 (rows 02 and 03 are left empty) |
| r. 05 — vyplatený daňový bonus | the sum of `CHILD_BONUS`, **capped at r. 04** |
| r. 08 — odvodová povinnosť | r. 04 − r. 05 |
| Part II, r. A / B / C | the bonus paid in total / the part covered by r. 05 / the remainder |

Rows 01a, 01b, 02, 03, 06, 07 and 08b, rows D–F of Part II and the Part III
requests to remit the employee premium or the interest bonus are left empty
or zero. The request to remit the child bonus is filled only when you ask for
it — see below.

## Claiming the bonus difference back {#bonus-refund}

Row 05 may carry the child tax bonus only up to the withheld advances
(row 04). Whatever the company paid beyond that came out of its own money and
appears in Part II, row C. The official instructions allow two ways to get it
back: deduct it from the advances of the following months, or ask the tax
administrator to pay it out with the request in **Part III** — filed after
the end of a calendar quarter, in the overview for its last month, for all
three months together.

In the overview for **March, June, September or December**, tick **Request
refund of the child tax bonus difference** before generating. Part III then
carries the request with the sum of row C over the quarter's three months,
each recomputed from that month's non-cancelled payslips. The company needs a
bank account for the refund; generation stops without one. The tick cannot be
set on any other month. Leave it off to deduct the difference later instead;
the file is then unchanged.

## Corrections {#corrections}

The overview accepts two kinds of filing: *riadny* and *opravný*. Set
**Correction Type** to *Corrective* to produce an *opravný prehľad*. The
module refuses to generate a corrective overview unless a regular one for the
same company, year and month is already marked submitted. A *dodatočný* or
cancelling overview cannot be produced.

## Limitations {#limitations}

- **Check the figures before filing.** The schema check proves the shape of
  the file, not that the amounts are right. No overview produced by this
  module has been confirmed by a live submission; reconcile the first one by
  hand.
- **Draft payslips count.** Every non-cancelled payslip of the month is
  included. Confirm or cancel the payslips before generating.
- Payslips are taken by their **period**, not by the payout date the law
  speaks of. A wage for September paid in October is reported for
  September.
- Row 01 carries **one** payout date. If the month's wages were paid on
  several dates, the rows per date must be split by hand.
- **Deducting the bonus difference later is not automated.** When you do not
  request a refund, nothing carries row C into the following months; reduce
  their payment of advances yourself. Row 08 never goes negative.
- The *zamestnanecká prémia*, the bonus on mortgage interest (§ 33a) and the
  corrections from the annual reconciliation (rows 02 and 03) have no source
  in the payroll and must be added by hand.
- The **legal form** element of the header is the *Právna forma* recorded on the company's contact by `l10n_sk_trade_registry`; without that module, or with the field empty, the element stays empty.
- The *opravný* overview leaves the date the correction was discovered
  (*dátum zistenia*) empty.
- The form vintage is picked by **today's date**, not by the period; an
  overview for a 2025 month is produced on the 2026 vintage.
- Nothing is sent to the authority: *Mark Submitted* only records that you
  filed it.
