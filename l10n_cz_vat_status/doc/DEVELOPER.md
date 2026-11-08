# l10n_cz_vat_status: developer notes

Not user documentation: this file is not rendered into a page.

## Implementation

Until this module the localisation treated every Czech company as a plátce:
`res.company._l10n_cz_typ_platce` in `l10n_cz_statutory` returned "P".

Two chart-wide passes of other modules are kept off the twins:
`l10n_cz_vat_return._cz_tag_selfassessed_deduction` (which would tag a
ř. 43/44 deduction onto every two-legged purchase tax — an IO has none) and the
historical-rate generator of `l10n_cssk_vat_return_base` (the historical rates
get twins of their own).
