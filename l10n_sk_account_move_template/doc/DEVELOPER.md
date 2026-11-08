# l10n_sk_account_move_template: developer notes

Not user documentation: this file is not rendered into a page.

## Loader

The hook loads only what a company does not already have. That makes it
idempotent, and — the reason that matters — it means **an edit the accountant
made to a shipped predkontácia is never reverted**: these are editable data
records, and the chart loader rewrites any record it is handed.

- Slovak predkontácie as ordinary, editable `account.move.template` records on
  the l10n_sk chart.
* One-amount postings: the first line is typed by the accountant, every further
  line mirrors it through the engine's `L1` formula.
* Slovak names, shipped directly rather than as `name@sk` translations of an
  English source: `account.move.template.name` is not a translatable field, and
  the chart loader's `@lang` mechanism only covers models in `TEMPLATE_MODELS`.
