# l10n_cz_mis_reports: developer notes

Not user documentation: this file is not rendered into a page.

## KPI names

A KPI name must not begin with an accounting-expression prefix (`bal`,
`balp`, `crd`, `deb`…). MIS Builder rewrites those tokens textually, so a
helper KPI named `balp_54_55` compiles as `(AccountingNone)_55` and every
expression referencing it fails with `#ERR`. The helper is called
`trida_54_55`, as its Slovak twin is `trieda_54_55`.

## Where the Czech template differs from the Slovak one

- Skupina 58 (změna stavu zásob vlastní činnosti, aktivace) is a cost line.
  The Slovak chart has these in 61 and 62, inside *ostatné výnosy*.
- The Czech chart has no 507, 606 or 607, and has 593 and 599 in the income
  tax group.
- Skupina 57 (rezervy a opravné položky ve finanční činnosti) is a financial
  cost; 597/598/697/698/699 follow the sides `l10n_cz_fs` gives them.
