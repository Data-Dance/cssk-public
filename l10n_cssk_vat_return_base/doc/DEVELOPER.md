# l10n_cssk_vat_return_base: developer notes

Not user documentation: this file is not rendered into a page.

## Engine support

Implements the **tags** and **aggregate** engines, which cover the output/input
tag lines and total aggregations. Odoo's own DPH report additionally uses
`sum` (children roll-ups) and custom `calcul` / external engines for some
net-payable lines — those need extended engine support or `manual` entry, and
accountant validation.
