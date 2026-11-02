=======================
MIS Builder KPI Details
=======================

|badge1|

.. |badge1| image:: https://img.shields.io/badge/licence-AGPL--3-blue.png
    :target: http://www.gnu.org/licenses/agpl-3.0-standalone.html
    :alt: License: AGPL-3

MIS Builder can expand a KPI into its accounts. This module adds **Details by**
to a KPI: pick a field of the journal items - partner, product, journal,
analytic account, or the date (by month) - and the KPI unfolds into one detail
row per value found in the column's data, each computed with the column's own
filters.

* The busiest values are shown, up to **Most detail rows**.
* Drill-down from a detail cell opens exactly that value's journal items.
* Works with every column, including the columns of
  ``mis_builder_column_breakdown``.
* Only KPIs computed directly from accounting expressions are unfolded; a KPI
  built from other KPIs is shown without details, because its detail rows
  would need every KPI it refers to recomputed per value.
* *Details by* and *Display details by account* exclude each other.

Credits
=======

Author: Data Dance s.r.o.
