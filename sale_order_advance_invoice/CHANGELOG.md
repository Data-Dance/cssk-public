# Changelog — sale_order_advance_invoice

## 18.0.1.0.4

### Added
- "Advance Invoices" menu entry under Accounting → Customers, just before
  Payments (visible to salespeople and accounting users).

## 18.0.1.0.3

### Fixed
- The sale-order PDF of an advance invoice is now named "Advance Invoice -
  ADV…" ("Zálohová faktúra - …" / "Zálohová faktura - …") instead of
  "Order - ADV…": `sale.action_report_saleorder` delegates its
  `print_report_name` to `sale.order._get_saleorder_report_filename()`,
  translated per rendering language; hook + migration force the expression
  for every installed language. Fixed the fuzzy Slovak translations of
  "Advance Invoice" / "Advance Invoice #".

## 18.0.1.0.2

### Fixed
- All three mail templates now render in the customer's language
  (`lang = {{ object.partner_id.lang }}`) — previously they rendered in the
  sending user's language. A post-migration backfills the `noupdate` records
  on existing databases.

## 18.0.1.0.1

### Fixed
- Posting an advance tax document now reconciles its clearing-account leg
  (`advance_received_account_id`, e.g. 324001) against the advance payments'
  legs on the same account — previously the documentation claimed this
  happened but the step was silently left to the user.

## 19.0.2.2.1
- Regenerated `.pot` from the current module and merged `cs`/`cs_CZ`/`sk`/`sk_SK`
  `.po` (removed obsolete entries). Translated the renamed/added strings
  (advance clearing & received-advance accounts, long-term advance, tax-document
  label, settings help) into Czech and Slovak; recompiled `.mo`.

## 19.0.2.2.0

### Fixed
- `_ensure_advance_accounts` now returns the created/looked-up accounts and
  `_apply_advance_invoice_setup` uses them directly (with a flush before resolving
  the remaining chart accounts). Previously a just-created company-dependent
  account code could resolve to the wrong account in the same transaction,
  swapping the clearing and short-term accounts on multi-company installs.

## 19.0.2.1.0

### Added
- `res.company._ensure_advance_accounts()` + a `create_accounts` key in the
  localization spec, so localization modules can ship accounts the standard chart
  lacks (e.g. the reconcilable `324001` advance-clearing account).

## 19.0.2.0.0

### Added
- **Localization support.** Country-specific accounts/journal are now wired by
  thin localization modules (`l10n_cz_sale_order_advance_invoice`,
  `l10n_sk_sale_order_advance_invoice`) via `tools.apply_advance_invoice_spec`
  and `res.company._apply_advance_invoice_setup` — accounts resolved by code per
  company on the matching chart template. Existing hand-configured deployments
  are preserved (only empty fields are filled).
- **Long-term received advances.** New `advance_invoice_long_term` flag on the
  advance invoice routes settlement to a dedicated long-term account
  (`advance_tax_doc_account_lt_id`, e.g. 475) instead of the short-term one.
- Overridable `sale.order._advance_invoice_tax_doc_deadline()` hook for the
  statutory tax-document deadline (default: min(paid + 15 days, end of month)).
- Interactive documentation under `static/description`.

### Changed
- **Account model.** `advance_received_account_id` is now described as the
  reconcilable *clearing* account; `advance_tax_doc_account_id` as the short-term
  *net received-advance* account (no longer requires `reconcile=True`).
- The standalone-link wizard now routes the with-tax-document deduction to the
  net received-advance account, consistent with the parent-tracking path.
- Generic (country-neutral) field labels, help text and code comments.
- Author set to Data Dance s.r.o.

### Fixed
- **Multi-company crash:** `advance_invoice_journal_id` was `required=True` with a
  cross-company `env.ref` default, breaking creation of additional companies. The
  default/required were removed; the journal is set by the install hook, the
  localization, or manually.
- Journal type/domain mismatch: the field domain now allows the dedicated general
  journal it actually uses (`type in ('sale', 'general')`).
- Removed dead commented code in the tracking-line description builder.

## 19.0.1.0.0
- Initial version (built in VS Code Copilot Chat, see `docs/creation_transcript.md`).
