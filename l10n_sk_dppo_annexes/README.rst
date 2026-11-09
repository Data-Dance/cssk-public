Slovak DPPO reviewed Tables A and B
===================================

Extends the native DPPOv25 return with structured, evidenced Table A items,
Table B depreciation amounts and their XML export. It does not maintain
another accounting ledger or automatically classify the company's expenses.

Enable reviewed annexes on the return, enter the complete company workpaper,
then calculate using the native action. A17 feeds r130. B6 is B2 minus B3
minus B4 plus B5; the difference between B1 and B6 feeds r150 or r250.
Proportional sale-year depreciation belongs to B5, not also to B2.
Conflicting manual main-row values are refused rather than silently discarded.
Other reviewed adjustments, such as r290, remain native DPPO inputs.

Evidence covers the posted ledger, complete entered annexes, main rows,
company header, schema and template. Changed sources require recalculation.
Exported/submitted inputs and exact XML snapshots are retained; filing status
records a separately verified external filing and never sends a return.

The feature is opt-in for compatibility. A blank legacy annex export is not
evidence that complete statutory annexes were prepared. This implementation
targets the held DPPOv25 layout; later statutory editions require review.
Other tables and special-company regimes are not inferred by this addon.
