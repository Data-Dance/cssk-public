=============================
MIS Builder Column Breakdown
=============================

|badge1|

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

In MIS Builder a column per journal, partner or company had to be made by
hand: one period per value, each with its own analytic domain. This module
adds **Columns by** to a period (*Breakdown*): pick any many2one or selection
field of the move line source - journal, partner, company, product, currency,
account... - and the period is computed once per value found in its data,
followed by the period's own column as the total.

* Columns are named after the values and sorted by name; **Most columns**
  caps how many are shown (the busiest values win; the rest stay in the total).
* The total keeps the period as its column, so sum and comparison columns that
  reference the period keep working.
* Drill-down from a breakdown cell opens exactly the journal items of that
  value.
* Notes work on every column: a note on a value column belongs to that
  value, a note on the total to the period.

Works with every MIS data source that has move lines (actuals and alternative
move-line sources) and combines with the column's own filters.

Credits
=======

Author: Data Dance s.r.o.
