---
title: MIS Builder Column Breakdown
summary: Split a MIS Builder column into one column per journal, partner, company, product or any other field, followed by the total.
verified: 19.0.1.1.0
---

## What it is for {#purpose}

In [module:mis_builder](module:mis_builder) a report with one column per
journal, partner or company had to be built by hand: one column for every
value, each with its own analytic filter, kept up to date as values were
added. This module lets a single column split itself by any field of the
journal items.

## Setting it up {#setup}

Open the MIS report (*Accounting › Reporting › MIS Reports*), then the column on
the *Columns* tab. Under **Breakdown**:

| Field | Meaning |
|---|---|
| Columns by | Any many2one or selection field of the column's journal items: *Journal*, *Partner*, *Company*, *Product*, *Currency*, *Account*, *Analytic account*… Empty: no breakdown. |
| Most columns | How many value columns to show at most (12 by default). The busiest values are shown; the others count only in the total. |

When the report is computed, the column becomes one column per value found in
its data, named after the value and sorted by name, followed by the column
itself as **(total)**.

## How it behaves {#behaviour}

- The column's own filters (dates, analytic filters, the report's filters)
  apply to every value column.
- Sum and comparison columns that refer to the broken-down column keep working:
  they use the total.
- **Drill-down** from a value column opens exactly the journal items of that
  value.
- **Notes** work on every column: a note on a value column belongs to that
  value, a note on the total to the whole column.
- Items with no value in the field (for example no partner) form their own
  column, *Undefined*.

## Limitations {#limitations}

Only columns with a move-line source can be broken down: *Actuals*, and
alternative sources such as budgets kept by account, by any field those lines
have. Budgets kept per KPI, and sum or comparison columns, cannot.
