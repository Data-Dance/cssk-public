# l10n_cssk_kv_kh_base: developer notes

Not user documentation: this file is not rendered into a page.

## Mixins and hooks

- `cssk.control.statement.version` — versioned template + section registry +
  submission types + threshold. New legislation = new version record.
* `cssk.control.statement` — the statement (mail.thread; draft → preview →
  exported → submitted), with `action_compute_lines` and `action_export_xml`
  (QWeb render + `lxml` root-element check + XSD validation).
* Row mixins: `...section.mixin` (detail), `...summary.mixin` (aggregated),
  `...reconciliation.mixin` (fixed lines, e.g. CZ section C).
* `account.move.line.cssk_control_section_code` — stored, computed by a
  country-overridable `_cssk_resolve_section_code` (**reverse charge first**).
* `account.tax` — `cssk_control_is_reverse_charge`.
* `account.journal` — section override.
