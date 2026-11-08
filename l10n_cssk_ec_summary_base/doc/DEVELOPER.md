# l10n_cssk_ec_summary_base: developer notes

Not user documentation: this file is not rendered into a page.

## Hooks

- `cssk.ec.summary.statement.version` — versioned template + schema + types.
* `cssk.ec.summary.statement` — mail.thread; draft → preview → exported →
  submitted; `action_compute_lines` + `action_export_xml` (VIES preflight →
  QWeb render → XSD validate → attach).
* `cssk.ec.summary.statement.line` — the aggregated line.
* `account.tax.cssk_ec_summary_code` — marks intra-EU supply taxes (the code
  drives the line's transaction type).
* Move-line hooks: `_cssk_ec_transaction_code` / `_cssk_ec_amount` /
  `_cssk_ec_partner_vat` (country-overridable).
