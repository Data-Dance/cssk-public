---
title: Payroll Worked Days & Inputs Timeline
summary: A timeline, pivot and list of the worked days and other inputs that fed each payslip, per employee over time, in the OCA Payroll app.
verified: 19.0.1.0.0
---

## What it is for {#purpose}

A payslip is computed from its **worked days** (days and hours per type —
normal work, leave, sickness…) and its **other inputs** (amounts entered for
the period). In the OCA **Payroll** app these lines can only be seen inside
each payslip. Odoo Enterprise reviews them on a work-entries gantt; this
module offers a Community alternative: the lines of all payslips on one
timeline, and in a pivot table for auditing.

It is **not tied to any country**: it depends only on the OCA `payroll` and
`web_timeline` modules. It stores the employee and the period dates of the
payslip on each worked-day and input line (fields *Employee*, *Period Start*,
*Period End*) so that the lines can be grouped and placed in time on their own.

## Setting it up {#setup}

Nothing to configure. It needs the OCA module `web_timeline` (from the OCA
`web` repository) to be available. On installation the three fields are
filled in for existing payslip lines.

## Worked days {#worked-days}

*Payroll → Worked Days Timeline* opens a timeline grouped by employee. Each
worked-day line is a bar from the start to the end of its **payslip period**,
showing its code and its number of days and hours; lines with the code
`WORK100` (normal working days) are green. Click a bar to open the line;
hold *Ctrl* and scroll to zoom.

Switch to the **pivot** for an audit matrix — employee and code in rows,
months in columns, hours and days as measures — or to the **list**, which
totals days and hours. The search offers the filter *Worked (WORK100)* and
groupings by *Employee*, *Code* and *Period*.

## Other inputs {#inputs}

*Payroll → Other Inputs* shows the input lines of all payslips as a pivot
(employee and code by month, summing *Amount*) or as a list with a total, and
can be grouped the same way.

## Limitations {#limitations}

- **Bars span the payslip period, not the days themselves.** A worked-day line
  records how many days of a type a payslip counted, not on which dates; every
  line of a monthly payslip therefore spans the whole month, and leave in the
  middle of the month is not shown at its real dates.
- Only lines of computed payslips appear; there is nothing to show until
  payslips exist. Lines of draft and cancelled payslips are included — there
  is no state filter.
- Only `WORK100` has a colour of its own; all other codes share the default
  colour.
- The module has no Slovak or Czech translation of its own; its menus,
  filters and field names appear in English.
