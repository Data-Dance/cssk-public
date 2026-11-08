# l10n_cssk_income_tax_base: developer notes

Not user documentation: this file is not rendered into a page.

## Model

- `cssk.income.tax.version` + line definitions — line kinds: `account`
  (P&L / accounting result before tax), `aggregate` (the tax-computation
  spine, a formula over line codes) and `manual` (accountant adjustments —
  připočitatelné / odčitatelné položky); plus the submission types
  (`cssk.income.tax.type`). New legislation ships as a new version record.
* `cssk.income.tax.return` (mail.thread) — the return aggregate. Evaluator,
  manual overrides preserved and fed into dependent aggregate lines on
  recompute, state machine (draft → submitted), amendment (dodatečné /
  opravné), XSD-validated statutory XML export, and an optional income-tax
  posting of the splatná daň (591/341).
