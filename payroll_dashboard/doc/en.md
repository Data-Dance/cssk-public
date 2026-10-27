---
title: Payroll Dashboard
summary: Headline payroll figures — gross, net, employer contributions, labour cost and income tax — as tiles, a monthly trend chart and a pivot table in the OCA Payroll app.
verified: 19.0.1.2.0
---

## What it is for {#purpose}

The OCA **Payroll** app computes payslips but has no overview of what payroll
costs over time. This module adds two screens to it:

- a **Dashboard** of tiles with the all-time totals of the headline figures;
- an **Analysis** screen — a pivot table and a line chart of the payslip lines
  by month, by employee and by figure.

It is **not tied to any country**: it depends only on the OCA `payroll`
module and adds no fields. The figures it picks out are found by salary-rule
**code**, so what it shows depends on the codes your payroll rules use (see
[Which figures appear](#figures)).

## Setting it up {#setup}

Nothing to configure. Install it alongside the OCA Payroll app; both screens
are open to payroll users and payroll managers.

## The Dashboard {#dashboard}

*Payroll → Dashboard* shows seven tiles for each company selected in the
company switcher:

| Tile | Computed as |
|---|---|
| Total gross | sum of payslip lines with code `GROSS` |
| Total net | sum of lines with code `NET` |
| Employer contributions | sum of lines with code `SOCIALEMPLOYERTOTAL` (Slovak rules) or `SOCIALERTOT` + `HEALTHERTOT` + `SOCIAL_DISCOUNT` (Czech rules) |
| Total labour cost | `GROSS` + the employer contributions |
| Income tax | sum of lines with code `INCOMETAXTOTAL` (Slovak) or `INCOMETAXTOT` (Czech) |
| Payslips | number of payslips |
| Employees | number of distinct employees with a payslip |

Only payslips in the state **Done** are counted; drafts, payslips waiting for
verification and cancelled payslips are left out. Each company gets its own
tiles in its own currency, and a user sees only the companies they are
allowed in and have selected; with several companies the company name is
shown under each tile.

The tiles are totals over the **whole payroll history**: they cannot be
filtered by period or employee. For that, use the Analysis screen.

## The Analysis screen {#analysis}

*Payroll → Analysis* opens a pivot of payslip lines — figures in rows, months
in columns — with the filters **Headline (gross/net/employer/tax)** and
**Done payslips** applied, limited to the companies selected in the company
switcher. Switch to the graph for one line per figure over time. Each figure
is drawn as its own line, never stacked, because gross already contains net
and the deductions.

The search panel adds filters for each headline figure (*Gross*, *Net*,
*Employer cost*, *Income tax*) and groupings by *Period*, *Employee*,
*Figure* and *Category*. Remove the headline filter to analyse any other rule
code — a bonus, a surcharge, a deduction — and the *Done payslips* filter to
include drafts.

## Which figures appear {#figures}

The tiles know the rule codes of both country payrolls for the OCA engine:
the Slovak [module:l10n_sk_hr_payroll_oca](module:l10n_sk_hr_payroll_oca) and
the Czech [module:l10n_cz_hr_payroll_oca](module:l10n_cz_hr_payroll_oca). The
Czech rules keep the employer's social and health insurance in separate
totals and the employer's premium discount (`SOCIAL_DISCOUNT`) on its own
line, so all three are added up — the same figure as the Czech
`EMPLOYERCOST` rule less the gross wage. With payroll rules of your own, the
figures appear only if your rules use the same codes.

## Limitations {#limitations}

- Figures are found by rule code only; see [Which figures appear](#figures).
- In the Analysis screen the company scope follows the company switcher; it
  is not a record rule, because the OCA engine has none on payslip lines.
