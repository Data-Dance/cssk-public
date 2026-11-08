# l10n_sk_mis_reports: developer notes

Not user documentation: this file is not rendered into a page.

## KPI names

A KPI name must not begin with an accounting-expression prefix (`bal`,
`balp`, `crd`, `deb`…). MIS Builder rewrites those tokens textually, so a
helper KPI named `balp_54_55` became `(AccountingNone)_55` and every
expression referencing it failed with `#ERR`. It is called `trieda_54_55`.
