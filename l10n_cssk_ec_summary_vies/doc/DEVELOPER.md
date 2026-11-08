# l10n_cssk_ec_summary_vies: developer notes

Not user documentation: this file is not rendered into a page.

## Integration

- On export, every reported line's foreign VAT number is verified against the
  EU VIES service via `res.partner._vies_query_direct` (only when the company
  has *Use direct EU VIES* enabled).
* A line whose VAT VIES reports as **invalid** is a hard block on export — a
  filing carrying an invalid VAT number is penalised.
* The official **consultation number** (`requestIdentifier`), the **check
  date** and the **validity** are stored on each line, preserving proof of the
  consultation as of the filing date.
* A transient VIES outage does **not** block the statutory filing; the affected
  lines are exported without a fresh confirmation and the gap is logged in the
  statement chatter so the check can be repeated.
* The base presence/format hard-block from `l10n_cssk_ec_summary_base` runs
  first and is unchanged.
