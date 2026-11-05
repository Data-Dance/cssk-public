---
title: MIS Builder KPI Details
summary: Unfold a MIS Builder KPI by partner, product, journal, month or any other field of the journal items, not only by account.
verified: 19.0.1.0.1
---

## What it is for {#purpose}

[module:mis_builder](module:mis_builder) can show a KPI's accounts underneath it
(*Display details by account*). Often the question is a different one - which
customers make up the revenue, which months the costs fell in. This module
lets a KPI unfold by any field of the journal items.

## Setting it up {#setup}

Open the MIS report template, then the KPI. Next to *Display details by
account*:

| Field | Meaning |
|---|---|
| Details by | A field of the journal items: *Partner*, *Product*, *Journal*, *Analytic account*, *Date* (one row per month)… |
| Most detail rows | How many detail rows at most (20 by default); the busiest values are shown. |

## How it behaves {#behaviour}

- Each detail row is the KPI computed with the column's own filters plus that
  value, in every column of the report - also the columns of a column
  breakdown.
- Drill-down from a detail cell opens exactly that value's journal items.
- Only a KPI computed directly from accounting expressions (such as
  `-balp[60%]`) is unfolded. A KPI built from other KPIs keeps its single row:
  its details would need every KPI it refers to recomputed per value.
- *Details by* and *Display details by account* exclude each other.
